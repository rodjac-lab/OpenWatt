"use client";

import { useEffect, useState } from "react";

interface HealthPayload {
  status: string;
  service: string;
  timestamp_utc: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function Home() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((payload) => setHealth(payload))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main className="landing">
      <h1>OpenWatt UI</h1>
      <p>Spec-driven comparator for residential electricity tariffs in France.</p>
      <section>
        <h2>API health</h2>
        {health && (
          <code>
            {health.status} @ {health.timestamp_utc}
          </code>
        )}
        {error && <p className="error">{error}</p>}
        {!health && !error && <p>Checking...</p>}
      </section>
      <section>
        <h2>Next steps</h2>
        <ul>
          <li>Implement tariff list view consuming `/v1/tariffs`.</li>
          <li>Render freshness badges using `docs/ui/badges.md`.</li>
          <li>Wire filters (supplier, option, puissance) to query params.</li>
        </ul>
      </section>
    </main>
  );
}
