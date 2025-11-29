"use client";

import { useEffect, useMemo, useState } from "react";

import type { components } from "../../lib/openapi-types";
import { AdminNav } from "../../components/admin/AdminNav";
import { JobsPanel } from "../../components/admin/JobsPanel";
import { MetricsPanel } from "../../components/admin/MetricsPanel";
import { SuppliersPanel } from "../../components/admin/SuppliersPanel";
import { ToolsPanel } from "../../components/admin/ToolsPanel";
import { OverrideHistoryPanel } from "../../components/admin/OverrideHistoryPanel";
import { MonitoringPanel } from "../../components/admin/MonitoringPanel";
import type {
  AdminRunPayload,
  AdminRunsResponse,
  AdminSection,
  FreshnessStats,
  HealthPayload,
  IngestHealthResponse,
  OverrideEntryPayload,
  OverrideHistoryResponse,
  SupplierRow,
} from "./types";

type Tariff = components["schemas"]["TariffObservation"];
type TrveDiff = components["schemas"]["TrveDiffEntry"];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function AdminConsole() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [ingestHealth, setIngestHealth] = useState<IngestHealthResponse | null>(null);
  const [ingestHealthError, setIngestHealthError] = useState<string | null>(null);
  const [ingestHealthLoading, setIngestHealthLoading] = useState(true);
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

  const fetchIngestHealth = () => {
    setIngestHealthLoading(true);
    fetch(`${API_BASE}/v1/health/ingest`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json();
      })
      .then((payload) => {
        setIngestHealth(payload);
        setIngestHealthError(null);
      })
      .catch((err) => setIngestHealthError(err.message))
      .finally(() => setIngestHealthLoading(false));
  };

  useEffect(() => {
    fetchIngestHealth();
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

  const freshnessStats: FreshnessStats = useMemo(() => {
    const stats = { fresh: 0, verifying: 0, stale: 0, broken: 0 };
    tariffs.forEach((row) => {
      const key = (row.data_status ?? "stale") as keyof typeof stats;
      stats[key] = (stats[key] ?? 0) + 1;
    });
    const total = tariffs.length || 1;
    return { stats, total };
  }, [tariffs]);

  const supplierRows: SupplierRow[] = useMemo(() => {
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
    return Array.from(map.values()).map((entry) => ({
      supplier: entry.supplier,
      parser_version: entry.parser_version,
      source_url: entry.source_url,
      statuses: Array.from(entry.statuses),
      observations: entry.observations,
    }));
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
    setInspectionMessage(
      `Fichier "${file.name}" (${Math.round(file.size / 1024)} Ko) prêt pour inspection.`
    );
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

  const sections: AdminSection[] = [
    { id: "monitoring", label: "Monitoring" },
    { id: "jobs", label: "Surveillance" },
    { id: "health", label: "Santé" },
    { id: "suppliers", label: "Fournisseurs" },
    { id: "tools", label: "Outils" },
    { id: "logs", label: "Logs" },
  ];

  const handlePageRefresh = () => {
    fetchIngestHealth();
    window.location.reload();
  };
  const handleOpenDocs = () => window.open("/api", "_blank");
  const supplierNames = supplierRows.map((row) => row.supplier);
  const currentTime = new Date().toLocaleString("fr-FR");

  return (
    <div className="admin-shell">
      <AdminNav sections={sections} healthStatus={health?.status} onRefresh={handlePageRefresh} />

      <main className="admin-page">
        <MonitoringPanel
          health={ingestHealth}
          error={ingestHealthError}
          loading={ingestHealthLoading}
          onRefresh={fetchIngestHealth}
        />

        <JobsPanel runs={runs} runsError={runsError} currentTime={currentTime} />

        <MetricsPanel
          freshness={freshnessStats}
          tariffError={tariffError}
          latencyMs={latencyMs}
          trveDiffCount={trveDiff.length}
          onRefreshDashboard={handlePageRefresh}
          onOpenDocs={handleOpenDocs}
        />

        <SuppliersPanel supplierRows={supplierRows} />

        <ToolsPanel
          supplierOptions={supplierNames}
          inspectionSupplier={inspectionSupplier}
          inspectionMessage={inspectionMessage}
          inspectionError={inspectionError}
          inspectionResult={inspectionResult}
          inspectionLoading={inspectionLoading}
          onInspectionSupplierChange={setInspectionSupplier}
          onInspectionFileChange={handleInspectionFile}
          onInspectionSubmit={handleInspectionSubmit}
          onOverrideSubmit={handleOverrideSubmit}
          overrideMessage={overrideMessage}
          overrideError={overrideError}
        />

        <OverrideHistoryPanel entries={overrideHistory} onRefresh={handlePageRefresh} />
      </main>
    </div>
  );
}
