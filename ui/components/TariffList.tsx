"use client";

import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";

import type { components } from "../lib/openapi-types";
import { FreshnessBadge } from "./FreshnessBadge";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const PUISSANCES = [3, 6, 9, 12, 15, 18, 24, 30, 36];

type Tariff = components["schemas"]["TariffObservation"];

type OptionFilter = Tariff["option"] | "";

type TrveDiffEntry = {
  supplier: string;
  option: string;
  puissance_kva: number;
  delta_eur_per_mwh: number;
  status: string;
};

type TableRow = Tariff & {
  annualCost: number;
  vsTrve?: number | null;
  isTrve?: boolean;
};

const CONSUMPTION_PROFILES = [
  { id: "small", icon: "🏢", label: "Petit appart", value: 2000 },
  { id: "medium", icon: "🏡", label: "Maison moyenne", value: 5000 },
  { id: "large", icon: "🏘️", label: "Grande maison", value: 8000 },
  { id: "electric", icon: "⚡", label: "Tout électrique", value: 12000 },
] as const;

export function TariffList() {
  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [trveDiff, setTrveDiff] = useState<TrveDiffEntry[]>([]);
  const [option, setOption] = useState<OptionFilter>("");
  const [puissance, setPuissance] = useState<number | "">("");
  const [consumption, setConsumption] = useState(5000);
  const [hcShare, setHcShare] = useState(40);
  const [selectedProfile, setSelectedProfile] = useState<string | null>("medium");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [onlyCheaperThanTrve, setOnlyCheaperThanTrve] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE}/v1/tariffs?include_stale=true`).then((res) => res.json()),
      fetch(`${API_BASE}/v1/guards/trve-diff`).then((res) => res.json()),
    ])
      .then(([tariffsPayload, trvePayload]) => {
        setTariffs(tariffsPayload.items ?? []);
        setTrveDiff(trvePayload.items ?? []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return tariffs.filter((row) => {
      if (option && row.option !== option) return false;
      if (puissance && row.puissance_kva !== puissance) return false;
      return true;
    });
  }, [tariffs, option, puissance]);

  const computeAnnualCost = (row: Tariff): number => {
    const abo = (row.abo_month_ttc ?? 0) * 12;
    if (row.option === "HPHC") {
      const hpPrice = row.price_kwh_hp_ttc ?? row.price_kwh_ttc ?? 0;
      const hcPrice = row.price_kwh_hc_ttc ?? row.price_kwh_ttc ?? hpPrice;
      const hpConso = consumption * (1 - hcShare / 100);
      const hcConso = consumption * (hcShare / 100);
      return abo + hpConso * hpPrice + hcConso * hcPrice;
    }
    if (row.option === "BASE" || row.option === "TEMPO") {
      const basePrice = row.price_kwh_ttc ?? row.price_kwh_hp_ttc ?? 0;
      return abo + consumption * basePrice;
    }
    return abo;
  };

  const findTrveComparison = (row: Tariff): number | null => {
    const match = trveDiff.find(
      (diff) =>
        diff.supplier.toLowerCase() === row.supplier.toLowerCase() &&
        diff.option === row.option &&
        diff.puissance_kva === row.puissance_kva
    );
    if (!match) return null;
    return (match.delta_eur_per_mwh / 1000) * consumption;
  };

  const isTrveSupplier = (supplier: string): boolean => {
    return supplier.toLowerCase() === "trve" || supplier.toLowerCase().includes("réglementé");
  };

  const tableRows: TableRow[] = filtered
    .map((row) => ({
      ...row,
      annualCost: computeAnnualCost(row),
      vsTrve: findTrveComparison(row),
      isTrve: isTrveSupplier(row.supplier),
    }))
    .filter((row) => {
      if (onlyCheaperThanTrve && row.vsTrve !== null && row.vsTrve !== undefined) {
        return row.vsTrve < 0;
      }
      return true;
    })
    .sort((a, b) => a.annualCost - b.annualCost);

  const handleProfileSelect = (profileId: string, value: number) => {
    setSelectedProfile(profileId);
    setConsumption(value);
  };

  const handleConsumptionChange = (value: number) => {
    setConsumption(value);
    setSelectedProfile(null);
  };

  const renderTrveComparison = (row: TableRow) => {
    if (!row.vsTrve) return null;

    const isCheaper = row.vsTrve < 0;
    const absValue = Math.abs(row.vsTrve).toFixed(0);
    const className = isCheaper
      ? "podium-card__trve-comparison podium-card__trve-comparison--cheaper"
      : "podium-card__trve-comparison podium-card__trve-comparison--expensive";

    return (
      <div className={className}>
        {isCheaper ? `${absValue} € moins cher que le TRVE` : `${absValue} € plus cher que le TRVE`}
      </div>
    );
  };

  return (
    <section>
      <header className="tariff-header">
        <div>
          <h2>Comparateur</h2>
          <p>Données issues des parsers PDF (insert-only). Tri par coût annuel TTC.</p>
        </div>
      </header>

      <div className="profiles">
        <h3 className="profiles__title">Choisissez votre profil de consommation</h3>
        <div className="profiles__grid">
          {CONSUMPTION_PROFILES.map((profile) => (
            <button
              key={profile.id}
              type="button"
              className={clsx("profile-card", {
                "profile-card--selected": selectedProfile === profile.id,
              })}
              onClick={() => handleProfileSelect(profile.id, profile.value)}
            >
              <div className="profile-card__icon">{profile.icon}</div>
              <div className="profile-card__label">{profile.label}</div>
              <div className="profile-card__value">{profile.value.toLocaleString()} kWh/an</div>
            </button>
          ))}
        </div>
      </div>

      <div className="tariff-controls">
        <label>
          Option
          <select value={option} onChange={(e) => setOption(e.target.value as OptionFilter)}>
            <option value="">Toutes</option>
            <option value="BASE">BASE</option>
            <option value="HPHC">HPHC</option>
            <option value="TEMPO">TEMPO</option>
          </select>
        </label>
        <label>
          Puissance
          <select
            value={puissance}
            onChange={(e) => setPuissance(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">Toutes</option>
            {PUISSANCES.map((p) => (
              <option key={p} value={p}>
                {p} kVA
              </option>
            ))}
          </select>
        </label>
        <label>
          Consommation annuelle (kWh)
          <input
            type="number"
            min={500}
            step={100}
            value={consumption}
            onChange={(e) => handleConsumptionChange(Math.max(0, Number(e.target.value)))}
          />
        </label>
        <label className="hc-slider">
          % Heures creuses
          <input
            type="range"
            min={0}
            max={100}
            value={hcShare}
            onChange={(e) => setHcShare(Number(e.target.value))}
            disabled={Boolean(option && option !== "HPHC")}
          />
          <span>{hcShare}%</span>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="checkbox"
            checked={onlyCheaperThanTrve}
            onChange={(e) => setOnlyCheaperThanTrve(e.target.checked)}
          />
          <span>Uniquement offres &lt; TRVE</span>
        </label>
      </div>

      {loading && <p>Chargement...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && tableRows.length >= 3 && (
        <div className="podium">
          <h3 className="podium__title">🏆 Top 3 des meilleures offres</h3>
          <div className="podium__grid">
            {/* 2nd place */}
            <div className="podium-card podium-card--silver">
              <div className="podium-card__medal">🥈</div>
              <div className="podium-card__rank">2ème</div>
              <div className="podium-card__supplier">{tableRows[1].supplier}</div>
              <div className="podium-card__details">
                {tableRows[1].option} • {tableRows[1].puissance_kva} kVA
              </div>
              <div className="podium-card__price">
                {tableRows[1].annualCost.toFixed(0)} €<span>/an</span>
              </div>
              <div className="podium-card__savings">
                +{(tableRows[1].annualCost - tableRows[0].annualCost).toFixed(0)} € vs 1er
              </div>
              {renderTrveComparison(tableRows[1])}
            </div>

            {/* 1st place */}
            <div className="podium-card podium-card--gold">
              <div className="podium-card__medal">🥇</div>
              <div className="podium-card__rank">1er</div>
              <div className="podium-card__supplier">{tableRows[0].supplier}</div>
              <div className="podium-card__details">
                {tableRows[0].option} • {tableRows[0].puissance_kva} kVA
              </div>
              <div className="podium-card__price">
                {tableRows[0].annualCost.toFixed(0)} €<span>/an</span>
              </div>
              <div className="podium-card__badge">💰 Meilleure offre!</div>
              {renderTrveComparison(tableRows[0])}
            </div>

            {/* 3rd place */}
            <div className="podium-card podium-card--bronze">
              <div className="podium-card__medal">🥉</div>
              <div className="podium-card__rank">3ème</div>
              <div className="podium-card__supplier">{tableRows[2].supplier}</div>
              <div className="podium-card__details">
                {tableRows[2].option} • {tableRows[2].puissance_kva} kVA
              </div>
              <div className="podium-card__price">
                {tableRows[2].annualCost.toFixed(0)} €<span>/an</span>
              </div>
              <div className="podium-card__savings">
                +{(tableRows[2].annualCost - tableRows[0].annualCost).toFixed(0)} € vs 1er
              </div>
              {renderTrveComparison(tableRows[2])}
            </div>
          </div>
        </div>
      )}
      {!loading && !error && (
        <table className="tariff-table comparator" key={`table-${consumption}-${hcShare}`}>
          <thead>
            <tr>
              <th>Fournisseur</th>
              <th>Option</th>
              <th>Puissance</th>
              <th>Abonnement<br />€/mois</th>
              <th>Prix kWh<br />Base/HP</th>
              <th>Prix kWh<br />HC</th>
              <th>Coût annuel<br />estimé</th>
              <th>vs. TRVE</th>
              <th>Fraîcheur</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row, index) => (
              <tr
                key={`${row.supplier}-${row.option}-${row.puissance_kva}-${index}`}
                className={clsx({ "trve-row": row.isTrve })}
              >
                <td><strong>{row.supplier}</strong></td>
                <td>{row.option}</td>
                <td>{row.puissance_kva} kVA</td>
                <td>{row.abo_month_ttc?.toFixed?.(2) ?? "-"} €</td>
                <td>
                  {row.price_kwh_ttc
                    ? `${row.price_kwh_ttc} €`
                    : row.price_kwh_hp_ttc
                    ? `${row.price_kwh_hp_ttc} €`
                    : "-"}
                </td>
                <td>
                  {row.price_kwh_hc_ttc ? `${row.price_kwh_hc_ttc} €` : "-"}
                </td>
                <td className="cost">
                  <strong>{row.annualCost ? `${row.annualCost.toFixed(0)} €` : "n/a"}</strong>
                </td>
                <td>
                  {row.isTrve ? (
                    <span className="vs-trve vs-trve--neutral">Référence</span>
                  ) : row.vsTrve !== null && row.vsTrve !== undefined ? (
                    <span
                      className={clsx("vs-trve", {
                        "vs-trve--cheaper": row.vsTrve < 0,
                        "vs-trve--expensive": row.vsTrve >= 0,
                      })}
                    >
                      {row.vsTrve < 0 ? "-" : "+"}{Math.abs(row.vsTrve).toFixed(0)} €
                    </span>
                  ) : (
                    <span className="vs-trve vs-trve--neutral">-</span>
                  )}
                </td>
                <td>
                  <FreshnessBadge status={row.data_status ?? "stale"} isTrve={row.isTrve} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
