import type { AdminRunPayload } from "../../app/admin/types";

interface JobsPanelProps {
  runs: AdminRunPayload[];
  runsError: string | null;
  currentTime: string;
}

export function JobsPanel({ runs, runsError, currentTime }: JobsPanelProps) {
  return (
    <section id="jobs" className="panel panel--flat">
      <div className="panel__header">
        <div>
          <p className="panel__eyebrow">Surveillance</p>
          <h2 className="panel__title">Jobs nightly</h2>
        </div>
        <time>{currentTime}</time>
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
                <time>
                  {job.observed_at ? new Date(job.observed_at).toLocaleString("fr-FR") : "?"}
                </time>
                <span className={`pill ${job.status === "ok" ? "pill--ok" : "pill--alert"}`}>
                  {job.status === "ok" ? "OK" : "NOK"}
                </span>
              </div>
            </article>
          ))}
        {!runsError && runs.length === 0 && <p className="muted">Aucune exécution détectée.</p>}
      </div>
    </section>
  );
}
