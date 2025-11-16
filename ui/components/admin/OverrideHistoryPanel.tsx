import type { OverrideEntryPayload } from "../../app/admin/types";

interface OverrideHistoryPanelProps {
  entries: OverrideEntryPayload[];
  onRefresh: () => void;
}

export function OverrideHistoryPanel({ entries, onRefresh }: OverrideHistoryPanelProps) {
  return (
    <section id="logs" className="panel">
      <header className="panel__header">
        <h2>Overrides manuels</h2>
        <button className="btn btn--ghost" onClick={onRefresh}>
          Rafraîchir
        </button>
      </header>
      <div className="job-history">
        {entries.map((entry) => (
          <details key={entry.id}>
            <summary>
              {entry.supplier} → {entry.url} ({new Date(entry.created_at).toLocaleString("fr-FR")})
            </summary>
            <p>
              Observed at:{" "}
              {entry.observed_at
                ? new Date(entry.observed_at).toLocaleDateString("fr-FR")
                : "non défini"}
            </p>
          </details>
        ))}
        {entries.length === 0 && <p className="muted">Aucun override enregistré.</p>}
      </div>
    </section>
  );
}
