import type { FreshnessStats } from "../../app/admin/types";

interface MetricsPanelProps {
  freshness: FreshnessStats;
  tariffError: string | null;
  latencyMs: number | null;
  trveDiffCount: number;
  onRefreshDashboard: () => void;
  onOpenDocs: () => void;
}

export function MetricsPanel({
  freshness,
  tariffError,
  latencyMs,
  trveDiffCount,
  onRefreshDashboard,
  onOpenDocs,
}: MetricsPanelProps) {
  const freshRatio = freshness.total ? freshness.stats.fresh / freshness.total : 0;
  const freshPercent = Math.round(freshRatio * 100);

  return (
    <section id="health" className="metric-grid">
      <article className="panel metric">
        <p className="panel__eyebrow">Qualité data</p>
        <h3 className="panel__title">Santé base</h3>
        <p>
          {freshPercent}% d&apos;observations fresh ({freshness.stats.fresh}/{freshness.total || 1})
        </p>
        <div className="progress">
          <span style={{ width: `${freshPercent}%` }} />
        </div>
        <ul>
          <li>verifying : {freshness.stats.verifying}</li>
          <li>stale : {freshness.stats.stale}</li>
          <li>broken : {freshness.stats.broken}</li>
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
            <p>TRVE deltas (items): {trveDiffCount}</p>
          </>
        )}
      </article>
      <article className="panel metric">
        <p className="panel__eyebrow">Raccourcis</p>
        <h3 className="panel__title">Actions rapides</h3>
        <button className="btn" onClick={onRefreshDashboard}>
          Rafraîchir dashboard
        </button>
        <button className="btn btn--ghost" onClick={onOpenDocs}>
          Voir doc API
        </button>
      </article>
    </section>
  );
}
