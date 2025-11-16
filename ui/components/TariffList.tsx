"use client";

import { useEffect, useMemo, useState } from "react";

import type { components } from "../lib/openapi-types";
import { FreshnessBadge } from "./FreshnessBadge";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const PUISSANCES = [3, 6, 9, 12, 15, 18, 24, 30, 36];

type Tariff = components["schemas"]["TariffObservation"];

type OptionFilter = Tariff["option"] | "";

type TableRow = Tariff & { annualCost: number };

export function TariffList() {
  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [option, setOption] = useState<OptionFilter>("");
  const [puissance, setPuissance] = useState<number | "">("");
  const [consumption, setConsumption] = useState(5000);
  const [hcShare, setHcShare] = useState(40);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/v1/tariffs?include_stale=true`)
      .then((res) => res.json())
      .then((payload) => setTariffs(payload.items ?? []))
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

  function computeAnnualCost(row: Tariff): number {
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
  }

  const tableRows: TableRow[] = useMemo(() => {
    return filtered
      .map((row) => ({ ...row, annualCost: computeAnnualCost(row) }))
      .sort((a, b) => a.annualCost - b.annualCost);
  }, [filtered, consumption, hcShare]);

  return (
    <section>
      <header className="tariff-header">
        <div>
          <h2>Comparateur</h2>
          <p>Données issues des parsers PDF (insert-only). Tri par coût annuel TTC.</p>
        </div>
      </header>

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
            onChange={(e) => setConsumption(Math.max(0, Number(e.target.value)))}
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
      </div>

      {loading && <p>Chargement...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && (
        <table className="tariff-table comparator">
          <thead>
            <tr>
              <th>Fournisseur</th>
              <th>Option</th>
              <th>Puissance</th>
              <th>Abonnement €/mois</th>
              <th>€/kWh (base / HP / HC)</th>
              <th>Coût annuel estimé</th>
              <th>Fraîcheur</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row) => (
              <tr key={`${row.supplier}-${row.option}-${row.puissance_kva}`}>
                <td>{row.supplier}</td>
                <td>{row.option}</td>
                <td>{row.puissance_kva} kVA</td>
                <td>{row.abo_month_ttc?.toFixed?.(2) ?? "-"}</td>
                <td>
                  {row.price_kwh_ttc ?? "-"} / {row.price_kwh_hp_ttc ?? "-"} /{" "}
                  {row.price_kwh_hc_ttc ?? "-"}
                </td>
                <td className="cost">
                  {row.annualCost ? `${row.annualCost.toFixed(0)} €` : "n/a"}
                </td>
                <td>
                  <FreshnessBadge status={row.data_status ?? "stale"} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
