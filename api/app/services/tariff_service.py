"""Services fetching tariff data while keeping Spec-Kit semantics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy.exc import SQLAlchemyError

from api.app.core.config import settings
from api.app.db import models
from api.app.db.repositories.tariffs import TariffRepository
from api.app.db.session import get_session
from api.app.models.enums import FreshnessStatus, TariffOption
from api.app.models.tariffs import (
    TariffCollection,
    TariffHistoryFilters,
    TariffHistoryResponse,
    TariffObservation,
    TrveDiffEntry,
    TrveDiffResponse,
)

import logging

logger = logging.getLogger(__name__)


def _seed_observations() -> list[TariffObservation]:
    """Simulate DB rows then compute data_status according to the constitution."""
    now = datetime.now(timezone.utc)
    base_ts = now.replace(microsecond=0)
    seeds = [
        {
            "supplier": "EDF",
            "option": TariffOption.BASE,
            "puissance_kva": 6,
            "price_kwh_ttc": 0.251,
            "price_kwh_hp_ttc": None,
            "price_kwh_hc_ttc": None,
            "abo_month_ttc": 12.5,
            "observed_at": base_ts - timedelta(days=1),
            "parser_version": "edf_v1",
            "source_url": "https://edf.fr/tarifs",
            "source_checksum": "f" * 64,
            "last_verified": base_ts - timedelta(hours=6),
        },
        {
            "supplier": "Engie",
            "option": TariffOption.HPHC,
            "puissance_kva": 9,
            "price_kwh_ttc": None,
            "price_kwh_hp_ttc": 0.269,
            "price_kwh_hc_ttc": 0.19,
            "abo_month_ttc": 15.2,
            "observed_at": base_ts - timedelta(hours=8),
            "parser_version": "engie_v1",
            "source_url": "https://particuliers.engie.fr/tarifs",
            "source_checksum": "e" * 64,
            "validation_pending": True,
        },
        {
            "supplier": "Mint",
            "option": TariffOption.BASE,
            "puissance_kva": 12,
            "price_kwh_ttc": 0.241,
            "price_kwh_hp_ttc": None,
            "price_kwh_hc_ttc": None,
            "abo_month_ttc": 14.0,
            "observed_at": base_ts - timedelta(days=20),
            "parser_version": "mint_v1",
            "source_url": "https://mint-energie.com/tarifs",
            "source_checksum": "d" * 64,
            "last_verified": base_ts - timedelta(days=10),
        },
        {
            "supplier": "TotalEnergies",
            "option": TariffOption.BASE,
            "puissance_kva": 3,
            "price_kwh_ttc": None,
            "price_kwh_hp_ttc": None,
            "price_kwh_hc_ttc": None,
            "abo_month_ttc": 11.2,
            "observed_at": base_ts - timedelta(days=2),
            "parser_version": "total_v1",
            "source_url": "https://www.totalenergies.fr/offres-electricite",
            "source_checksum": "c" * 64,
            "parse_error": True,
        },
    ]
    return [_build_observation(seed, now) for seed in seeds]


def _build_observation(seed: dict, now: datetime) -> TariffObservation:
    return TariffObservation(
        supplier=seed["supplier"],
        option=seed["option"],
        puissance_kva=seed["puissance_kva"],
        price_kwh_ttc=seed.get("price_kwh_ttc"),
        price_kwh_hp_ttc=seed.get("price_kwh_hp_ttc"),
        price_kwh_hc_ttc=seed.get("price_kwh_hc_ttc"),
        abo_month_ttc=seed["abo_month_ttc"],
        observed_at=seed["observed_at"],
        parser_version=seed["parser_version"],
        source_url=seed["source_url"],
        source_checksum=seed["source_checksum"],
        last_verified=seed.get("last_verified"),
        data_status=_determine_data_status(seed, now),
    )


def _determine_data_status(seed: dict, now: datetime) -> FreshnessStatus:
    if seed.get("parse_error"):
        return FreshnessStatus.BROKEN
    if seed.get("validation_pending"):
        return FreshnessStatus.VERIFYING
    age = now - seed["observed_at"]
    if age > timedelta(days=14):
        return FreshnessStatus.STALE
    return FreshnessStatus.FRESH


def _filter_observations(
    observations: Iterable[TariffObservation],
    *,
    option: TariffOption | None,
    puissance: int | None,
    include_stale: bool,
) -> list[TariffObservation]:
    def is_visible(obs: TariffObservation) -> bool:
        if option and obs.option != option:
            return False
        if puissance and obs.puissance_kva != puissance:
            return False
        if not include_stale and obs.data_status in {FreshnessStatus.STALE, FreshnessStatus.BROKEN}:
            return False
        return True

    return [obs for obs in observations if is_visible(obs)]


async def fetch_latest_tariffs(
    *, option: TariffOption | None = None, puissance: int | None = None, include_stale: bool = False
) -> TariffCollection:
    observations: list[TariffObservation] | None = None
    if settings.enable_db:
        try:
            async with get_session() as session:
                repo = TariffRepository(session)
                observations = await repo.fetch_latest(
                    option=option, puissance=puissance, include_stale=include_stale
                )
        except SQLAlchemyError as exc:
            logger.warning("DB fetch_latest_tariffs failed, falling back to seed data: %s", exc)
            observations = None
    if not observations:
        observations = _filter_observations(
            _seed_observations(),
            option=option,
            puissance=puissance,
            include_stale=include_stale,
        )
    return TariffCollection(items=observations)


async def fetch_history(filters: TariffHistoryFilters) -> TariffHistoryResponse:
    observations: list[TariffObservation] | None = None
    if settings.enable_db:
        try:
            async with get_session() as session:
                repo = TariffRepository(session)
                observations = await repo.fetch_history(filters.model_dump(exclude_none=True))
        except SQLAlchemyError as exc:
            logger.warning("DB fetch_history failed, falling back to seed data: %s", exc)
            observations = None
    if observations is None:
        observations = [obs for obs in _seed_observations() if _matches_filters(obs, filters)]
    return TariffHistoryResponse(filters=filters, items=observations)


def _matches_filters(obs: TariffObservation, filters: TariffHistoryFilters) -> bool:
    if filters.supplier and obs.supplier.lower() != filters.supplier.lower():
        return False
    if filters.option and obs.option != filters.option:
        return False
    if filters.puissance_kva and obs.puissance_kva != filters.puissance_kva:
        return False
    if filters.since and obs.observed_at.date() < filters.since:
        return False
    if filters.until and obs.observed_at.date() > filters.until:
        return False
    return True


def compute_trve_diff_seed() -> TrveDiffResponse:
    now = datetime.now(timezone.utc)
    items = [
        TrveDiffEntry(
            supplier="EDF",
            option=TariffOption.BASE,
            puissance_kva=6,
            delta_eur_per_mwh=1.2,
            compared_at=now,
            status="ok",
        ),
        TrveDiffEntry(
            supplier="Engie",
            option=TariffOption.HPHC,
            puissance_kva=9,
            delta_eur_per_mwh=15.4,
            compared_at=now,
            status="alert" if 15.4 > 10 else "ok",
        ),
    ]
    return TrveDiffResponse(generated_at=now, items=items)


async def compute_trve_diff() -> TrveDiffResponse:
    now = datetime.now(timezone.utc)
    if not settings.enable_db:
        return compute_trve_diff_seed()
    try:
        async with get_session() as session:
            repo = TariffRepository(session)
            observations = await repo.fetch_latest(include_stale=True)
            trve_rows = await repo.fetch_trve_reference()
    except SQLAlchemyError as exc:
        logger.warning("DB compute_trve_diff failed, returning seed data: %s", exc)
        return compute_trve_diff_seed()

    trve_map: dict[tuple[TariffOption, int], models.TrveReference] = {}
    for row in trve_rows:
        trve_map[(row.option, row.puissance_kva)] = row

    entries: list[TrveDiffEntry] = []
    for obs in observations:
        ref = trve_map.get((obs.option, obs.puissance_kva))
        if not ref:
            continue
        delta = _compute_delta_eur_per_mwh(obs, ref)
        status = "alert" if abs(delta) > 10 else "ok"
        entries.append(
            TrveDiffEntry(
                supplier=obs.supplier,
                option=obs.option,
                puissance_kva=obs.puissance_kva,
                delta_eur_per_mwh=delta,
                compared_at=now,
                status=status,
            )
        )
    if not entries:
        return compute_trve_diff_seed()
    return TrveDiffResponse(generated_at=now, items=entries)


def _compute_delta_eur_per_mwh(obs: TariffObservation, ref: models.TrveReference) -> float:
    base_price = ref.price_kwh_ttc
    obs_price = obs.price_kwh_ttc
    if obs.option == TariffOption.HPHC:
        base_price = ref.price_kwh_hp_ttc or ref.price_kwh_ttc
        obs_price = obs.price_kwh_hp_ttc
    if base_price is None or obs_price is None:
        return 0.0
    return (float(obs_price) - float(base_price)) * 1000.0
