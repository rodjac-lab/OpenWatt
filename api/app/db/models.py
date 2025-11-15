from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.app.db.base import Base
from api.app.models.enums import TariffOption


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    tariffs: Mapped[list["Tariff"]] = relationship(back_populates="supplier")


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    option: Mapped[TariffOption] = mapped_column(Enum(TariffOption, name="tariff_option", native_enum=False), nullable=False)
    puissance_kva: Mapped[int] = mapped_column(Integer, nullable=False)
    price_kwh_ttc: Mapped[Optional[float]] = mapped_column(Numeric(8, 6))
    price_kwh_hp_ttc: Mapped[Optional[float]] = mapped_column(Numeric(8, 6))
    price_kwh_hc_ttc: Mapped[Optional[float]] = mapped_column(Numeric(8, 6))
    abo_month_ttc: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    parser_version: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    supplier: Mapped[Supplier] = relationship(back_populates="tariffs")


class TrveReference(Base):
    __tablename__ = "trve_reference"

    id: Mapped[int] = mapped_column(primary_key=True)
    option: Mapped[TariffOption] = mapped_column(Enum(TariffOption, name="trve_tariff_option", native_enum=False), nullable=False)
    puissance_kva: Mapped[int] = mapped_column(Integer, nullable=False)
    price_kwh_ttc: Mapped[Optional[float]] = mapped_column(Numeric(8, 6))
    price_kwh_hp_ttc: Mapped[Optional[float]] = mapped_column(Numeric(8, 6))
    price_kwh_hc_ttc: Mapped[Optional[float]] = mapped_column(Numeric(8, 6))
    abo_month_ttc: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)


class AdminOverride(Base):
    __tablename__ = "admin_overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
