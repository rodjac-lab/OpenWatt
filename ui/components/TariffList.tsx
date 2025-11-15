"use client";

import { useEffect, useMemo, useState } from "react";

import type { components } from "../lib/openapi-types";
import { FreshnessBadge } from "./FreshnessBadge";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

type Tariff = components["schemas"]["Tariff"];

interface Filters {
  option: Tariff["option"] | "";
}

export function TariffList() {
  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [filters, setFilters] = useState<Filters>({ option: "" as Filters["option"] });
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
    if (!filters.option) return tariffs;
    return tariffs.filter((row) => row.option === filters.option);
  }, [tariffs, filters.option]);

  function handleOptionChange(value: string) {
    setFilters((prev) => ({ ...prev, option: value as Filters["option"] }));
  }

  return (
    <section>
      <header className="tariff-header">
        <div>
          <h2>Tarifs observés</h2>
          <p>Données insert-only issues des parseurs YAML.</p>
        </div>
        <label>
          Option
          <select value={filters.option} onChange={(e) => handleOptionChange(e.target.value)}>
            <option value="">Toutes</option>
            <option value="BASE">BASE</option>
            <option value="HPHC">HPHC</option>
            <option value="TEMPO">TEMPO</option>
          </select>
        </label>
      </header>
      {loading && <p>Chargement…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && (
        <table className="tariff-table">
          <thead>
            <tr>
              <th>Fournisseur</th>
              <th>Option</th>
              <th>Puissance</th>
              <th>Abonnement €/mois</th>
              <th>kWh (BASE/HP/HC)</th>
              <th>Fraîcheur</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={`${row.supplier}-${row.option}-${row.puissance_kva}`}>
                <td>{row.supplier}</td>
                <td>{row.option}</td>
                <td>{row.puissance_kva} kVA</td>
                <td>{row.abo_month_ttc?.toFixed?.(2)}</td>
                <td>
                  {row.price_kwh_ttc ?? "—"} / {row.price_kwh_hp_ttc ?? "—"} / {row.price_kwh_hc_ttc ?? "—"}
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
