import { IngestHealthResponse, SupplierHealthStatus } from "../../app/admin/types";

interface MonitoringPanelProps {
  health: IngestHealthResponse | null;
  error: string | null;
  loading: boolean;
  onRefresh: () => void;
}

export function MonitoringPanel({ health, error, loading, onRefresh }: MonitoringPanelProps) {
  if (loading) {
    return (
      <section id="monitoring" className="panel panel--flat">
        <div className="panel__header">
          <div>
            <p className="panel__eyebrow">Santé Ingestion</p>
            <h2 className="panel__title">Chargement...</h2>
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section id="monitoring" className="panel panel--flat">
        <div className="panel__header">
          <div>
            <p className="panel__eyebrow">Santé Ingestion</p>
            <h2 className="panel__title error">Erreur de chargement</h2>
          </div>
        </div>
        <p className="error">{error}</p>
        <button onClick={onRefresh} className="btn btn--secondary">
          Réessayer
        </button>
      </section>
    );
  }

  if (!health) return null;

  return (
    <section id="monitoring" className="panel panel--flat">
      <div className="panel__header">
        <div>
          <p className="panel__eyebrow">Santé Ingestion</p>
          <h2 className="panel__title">État des scrapers</h2>
        </div>
        <div className="panel__actions">
          <time>{new Date(health.generated_at).toLocaleString("fr-FR")}</time>
          <button onClick={onRefresh} className="btn btn--icon" title="Rafraîchir">
            ↻
          </button>
        </div>
      </div>

      <div className="monitoring-grid">
        {health.suppliers.map((supplier) => (
          <SupplierCard key={supplier.supplier} status={supplier} />
        ))}
      </div>
    </section>
  );
}

function SupplierCard({ status }: { status: SupplierHealthStatus }) {
  const isOk = status.data_status === "fresh" || status.data_status === "verifying";
  const isRunning = status.last_run_status === "running";

  let statusClass = "card--ok";
  if (status.data_status === "broken") statusClass = "card--error";
  if (status.data_status === "stale") statusClass = "card--warning";
  if (isRunning) statusClass = "card--running";

  return (
    <article className={`monitoring-card ${statusClass}`}>
      <div className="card__header">
        <h3 className="card__title">{status.supplier}</h3>
        <span className={`pill pill--${status.data_status}`}>
          {status.data_status.toUpperCase()}
        </span>
      </div>

      <div className="card__meta">
        <div className="meta-row">
          <span className="label">Dernier run:</span>
          <span className="value">
            {status.last_run_at ? new Date(status.last_run_at).toLocaleString("fr-FR") : "Jamais"}
          </span>
        </div>

        <div className="meta-row">
          <span className="label">Statut run:</span>
          <span className={`value status-${status.last_run_status}`}>
            {status.last_run_status || "N/A"}
          </span>
        </div>

        {status.error_message && (
          <div className="meta-row error-row">
            <span className="label">Erreur:</span>
            <p className="value error-text" title={status.error_message}>
              {status.error_message}
            </p>
          </div>
        )}

        <div className="meta-row">
          <span className="label">Échecs consécutifs:</span>
          <span className={`value ${status.consecutive_failures > 0 ? "warn" : ""}`}>
            {status.consecutive_failures}
          </span>
        </div>
      </div>
    </article>
  );
}
