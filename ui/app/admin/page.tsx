"use client";

import { useEffect, useMemo, useState } from "react";

import type { components } from "../../lib/openapi-types";

type Tariff = components["schemas"]["TariffObservation"];
type TrveDiff = components["schemas"]["TrveDiffEntry"];

interface HealthPayload {
  status: string;
  service: string;
  timestamp_utc: string;
}

interface AdminRunPayload {
  supplier: string;
  status: "ok" | "nok";
  message: string;
  observed_at?: string | null;
}

interface AdminRunsResponse {
  generated_at: string;
  items: AdminRunPayload[];
}

interface OverrideEntryPayload {
  id: number;
  supplier: string;
  url: string;
  observed_at?: string | null;
  created_at: string;
}

interface OverrideHistoryResponse {
  items: OverrideEntryPayload[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function AdminConsole() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [trveDiff, setTrveDiff] = useState<TrveDiff[]>([]);
  const [tariffError, setTariffError] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [inspectionMessage, setInspectionMessage] = useState<string>("Aucun fichier analysé");
  const [inspectionFile, setInspectionFile] = useState<File | null>(null);
  const [inspectionSupplier, setInspectionSupplier] = useState<string>("");
  const [inspectionResult, setInspectionResult] = useState<any[]>([]);
  const [inspectionError, setInspectionError] = useState<string | null>(null);
  const [inspectionLoading, setInspectionLoading] = useState(false);
  const [overrideMessage, setOverrideMessage] = useState<string>("");
  const [runs, setRuns] = useState<AdminRunPayload[]>([]);
  const [runsError, setRunsError] = useState<string | null>(null);
  const [overrideHistory, setOverrideHistory] = useState<OverrideEntryPayload[]>([]);
  const [overrideError, setOverrideError] = useState<string | null>(null);

  useEffect(() => {
    document.body.classList.add("admin-theme");
    return () => document.body.classList.remove("admin-theme");
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((payload) => setHealth(payload))
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    const started = performance.now();
    fetch(`${API_BASE}/v1/tariffs?include_stale=true`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json();
      })
      .then((payload) => setTariffs(payload.items ?? []))
      .catch((err) => setTariffError(err.message))
      .finally(() => setLatencyMs(Math.round(performance.now() - started)));
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/v1/guards/trve-diff`)
      .then((res) => res.json())
      .then((payload) => setTrveDiff(payload.items ?? []))
      .catch(() => setTrveDiff([]));
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/v1/admin/runs`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json() as Promise<AdminRunsResponse>;
      })
      .then((payload) => setRuns(payload.items ?? []))
      .catch((err) => setRunsError(err.message));
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/v1/admin/overrides`)
      .then((res) => res.json() as Promise<OverrideHistoryResponse>)
      .then((payload) => setOverrideHistory(payload.items ?? []))
      .catch((err) => setOverrideError(err.message));
  }, []);

  const freshnessStats = useMemo(() => {
    const stats = { fresh: 0, verifying: 0, stale: 0, broken: 0 };
    tariffs.forEach((row) => {
      const key = (row.data_status ?? "stale") as keyof typeof stats;
      stats[key] = (stats[key] ?? 0) + 1;
    });
    const total = tariffs.length || 1;
    return { stats, total };
  }, [tariffs]);

  const supplierRows = useMemo(() => {
    const map = new Map<
      string,
      {
        supplier: string;
        parser_version?: string;
        source_url?: string;
        statuses: Set<string>;
        observations: number;
      }
    >();
    tariffs.forEach((row) => {
      if (!map.has(row.supplier)) {
        map.set(row.supplier, {
          supplier: row.supplier,
          parser_version: row.parser_version,
          source_url: row.source_url,
          statuses: new Set(),
          observations: 0,
        });
      }
      const entry = map.get(row.supplier)!;
      if (row.parser_version) entry.parser_version = row.parser_version;
      if (row.source_url) entry.source_url = row.source_url;
      if (row.data_status) entry.statuses.add(row.data_status);
      entry.observations += 1;
    });
    return Array.from(map.values());
  }, [tariffs]);

  useEffect(() => {
    if (!inspectionSupplier && supplierRows.length > 0) {
      setInspectionSupplier(supplierRows[0].supplier);
    }
  }, [inspectionSupplier, supplierRows]);

  function handleInspectionFile(files: FileList | null) {
    if (!files || files.length === 0) {
      setInspectionFile(null);
      setInspectionMessage("Aucun fichier sélectionné");
      return;
    }
    const file = files[0];
    setInspectionFile(file);
    setInspectionMessage(`Fichier "${file.name}" (${Math.round(file.size / 1024)} Ko) prêt pour inspection.`);
  }

  function handleInspectionSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!inspectionSupplier) {
      setInspectionError("Choisissez un fournisseur.");
      return;
    }
    if (!inspectionFile) {
      setInspectionError("Ajoutez un PDF à analyser.");
      return;
    }
    setInspectionLoading(true);
    setInspectionError(null);
    setInspectionResult([]);
    const formData = new FormData();
    formData.append("supplier", inspectionSupplier);
    formData.append("limit", "50");
    formData.append("file", inspectionFile);
    fetch(`${API_BASE}/v1/admin/inspect`, {
      method: "POST",
      body: formData,
    })
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json();
      })
      .then((payload) => {
        setInspectionResult(payload.items ?? []);
        setInspectionMessage(`${payload.count} lignes extraites (affichage limité)`);
      })
      .catch((err) => setInspectionError(err.message))
      .finally(() => setInspectionLoading(false));
  }

  function handleOverrideSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload: Record<string, string> = {
      supplier: String(formData.get("supplier") || ""),
      url: String(formData.get("url") || ""),
    };
    const observed = formData.get("observed_at");
    if (observed) {
      payload.observed_at = `${observed}T00:00:00Z`;
    }
    setOverrideMessage("Override en cours...");
    fetch(`${API_BASE}/v1/admin/overrides`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json() as Promise<OverrideEntryPayload>;
      })
      .then((entry) => {
        setOverrideMessage(`Override enregistré pour ${entry.supplier}`);
        setOverrideHistory((prev) => [entry, ...prev]);
      })
      .catch((err) => setOverrideMessage(`Erreur: ${err.message}`));
    event.currentTarget.reset();
  }

  const sections = [
    { id: "jobs", label: "Surveillance" },
    { id: "health", label: "Santé" },
    { id: "suppliers", label: "Fournisseurs" },
    { id: "tools", label: "Outils" },
    { id: "logs", label: "Logs" },
  ];

  return (
    <div className="admin-shell">
      <nav className="admin-nav">
        <div className="admin-nav__brand">
          <span className="brand-icon">⚡</span>
          <strong>OpenWatt</strong>
        </div>
        <div className="admin-nav__tabs">
          {sections.map((section) => (
            <a key={section.id} href={`#${section.id}`}>
              {section.label}
            </a>
          ))}
        </div>
        <div className="admin-nav__actions">
          <span className="pill">{health?.status === "ok" ? "API OK" : "API ?"}</span>
          <button className="btn btn--ghost" onClick={() => window.location.reload()}>
            Rafraîchir
          </button>
        </div>
      </nav>

      <main className="admin-page">
        <section id="jobs" className="panel panel--flat">
          <div className="panel__header">
            <div>
              <p className="panel__eyebrow">Surveillance</p>
              <h2 className="panel__title">Jobs nightly</h2>
            </div>
            <time>{new Date().toLocaleString("fr-FR")}</time>
          </div>
        <div className="job-list">
          {runsError && <p className="error">{runsError}</p>}
          {!runsError &&
            runs.map((job) => (
              <article key={`${job.supplier}-${job.observed_at ?? "n/a"}`} className="job-item">
                <div>
                  <span className="job-item__label">{job.supplier}</span>
                  <p className="job-item__message">{job.message}</p>
                </div>
                <div className="job-item__meta">
                  <time>{job.observed_at ? new Date(job.observed_at).toLocaleString("fr-FR") : "?"}</time>
                  <span className={`pill ${job.status === "ok" ? "pill--ok" : "pill--alert"}`}>
                    {job.status === "ok" ? "OK" : "NOK"}
                  </span>
                </div>
              </article>
            ))}
          {!runsError && runs.length === 0 && <p className="muted">Aucune exécution détectée.</p>}
        </div>
        </section>

        <section id="health" className="metric-grid">
          <article className="panel metric">
            <p className="panel__eyebrow">Qualité data</p>
            <h3 className="panel__title">Santé base</h3>
            <p>
              {((freshnessStats.stats.fresh / (freshnessStats.total || 1)) * 100).toFixed(0)}% d&apos;observations fresh (
              {freshnessStats.stats.fresh}/{freshnessStats.total})
            </p>
            <div className="progress">
              <span style={{ width: `${(freshnessStats.stats.fresh / (freshnessStats.total || 1)) * 100}%` }} />
          </div>
          <ul>
            <li>verifying : {freshnessStats.stats.verifying}</li>
            <li>stale : {freshnessStats.stats.stale}</li>
            <li>broken : {freshnessStats.stats.broken}</li>
          </ul>
          </article>
          <article className="panel metric">
            <p className="panel__eyebrow">Observabilité</p>
            <h3 className="panel__title">API monitoring</h3>
            {tariffError ? (
              <p className="error">Erreur : {tariffError}</p>
          ) : (
            <>
              <p>Latence moyenne</p>
              <strong>{latencyMs ?? "?"} ms</strong>
              <p>TRVE deltas (items): {trveDiff.length}</p>
            </>
          )}
          </article>
          <article className="panel metric">
            <p className="panel__eyebrow">Raccourcis</p>
            <h3 className="panel__title">Actions rapides</h3>
            <button className="btn" onClick={() => window.location.reload()}>
              Rafraîchir dashboard
            </button>
            <button className="btn btn--ghost" onClick={() => window.open("/api", "_blank")}>
              Voir doc API
            </button>
          </article>
        </section>

        <section id="suppliers" className="panel">
        <header className="panel__header">
          <div>
            <h2>Fournisseurs & parsers</h2>
            <p>Liste extraite des observations en base.</p>
          </div>
          <button className="btn btn--ghost">Ajouter un fournisseur</button>
        </header>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Fournisseur</th>
                <th>Parser</th>
                <th>Source</th>
                <th>Observations</th>
                <th>Statuts</th>
              </tr>
            </thead>
            <tbody>
              {supplierRows.map((row) => (
                <tr key={row.supplier}>
                  <td>{row.supplier}</td>
                  <td>{row.parser_version ?? "?"}</td>
                  <td className="truncate">
                    <a href={row.source_url} target="_blank" rel="noreferrer">
                      {row.source_url ?? "?"}
                    </a>
                  </td>
                  <td>{row.observations}</td>
                  <td>
                    {Array.from(row.statuses).map((status) => (
                      <span key={status} className="badge badge--grey">
                        {status}
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
              {supplierRows.length === 0 && (
                <tr>
                  <td colSpan={5}>Aucune observation chargée.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        </section>

        <section id="tools" className="panel tools-grid">
        <div>
          <h3>Inspection PDF</h3>
          <p>Utiliser ce module pour vérifier rapidement une table PDF avant de mettre à jour un snapshot.</p>
          <form className="override-form" onSubmit={handleInspectionSubmit}>
            <label>
              Fournisseur
              <input
                name="inspect_supplier"
                list="supplier-options"
                value={inspectionSupplier}
                onChange={(e) => setInspectionSupplier(e.target.value)}
                placeholder="engie"
              />
            </label>
            <datalist id="supplier-options">
              {supplierRows.map((row) => (
                <option key={row.supplier} value={row.supplier} />
              ))}
            </datalist>
            <label>
              Fichier PDF
              <input type="file" accept=".pdf" onChange={(event) => handleInspectionFile(event.target.files)} />
            </label>
            <button className="btn" type="submit" disabled={inspectionLoading}>
              {inspectionLoading ? "Analyse..." : "Inspecter"}
            </button>
          </form>
          <p className="muted">{inspectionMessage}</p>
          {inspectionError && <p className="error">{inspectionError}</p>}
          {inspectionResult.length > 0 && (
            <div className="inspect-preview">
              <p>{inspectionResult.length} lignes (aperçu des premières):</p>
              <pre>{JSON.stringify(inspectionResult.slice(0, 3), null, 2)}</pre>
            </div>
          )}
        </div>
        <div>
          <h3>Override source</h3>
          <form className="override-form" onSubmit={handleOverrideSubmit}>
            <label>
              Fournisseur
              <input required name="supplier" placeholder="ex: Engie" />
            </label>
            <label>
              URL source temporaire
              <input required name="url" type="url" placeholder="https://..." />
            </label>
            <label>
              Observed at (optionnel)
              <input name="observed_at" type="date" />
            </label>
            <button className="btn" type="submit">
              Lancer override
            </button>
          </form>
          {overrideMessage && <p className="muted">{overrideMessage}</p>}
          {overrideError && <p className="error">{overrideError}</p>}
        </div>
        </section>

        <section id="logs" className="panel">
        <header className="panel__header">
          <h2>Overrides manuels</h2>
          <button className="btn btn--ghost" onClick={() => window.location.reload()}>
            Rafraîchir
          </button>
        </header>
        <div className="job-history">
          {overrideHistory.map((entry) => (
            <details key={entry.id}>
              <summary>
                {entry.supplier} → {entry.url} ({new Date(entry.created_at).toLocaleString("fr-FR")})
              </summary>
              <p>Observed at: {entry.observed_at ? new Date(entry.observed_at).toLocaleDateString("fr-FR") : "non défini"}</p>
            </details>
          ))}
          {overrideHistory.length === 0 && <p className="muted">Aucun override enregistré.</p>}
        </div>
        </section>
      </main>
    </div>
  );
}
