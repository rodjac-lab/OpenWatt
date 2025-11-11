"use client";

import { useEffect, useState } from "react";

import { TariffList } from "../components/TariffList";

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
      <header className="hero">
        <div>
          <p className="hero__eyebrow">Spec-Kit • Open Data</p>
          <h1>OpenWatt UI</h1>
          <p>Comparateur des tarifs électricité FR — statuts fresh / verifying / stale / broken alignés sur la spec.</p>
        </div>
        <div className="health">
          <h3>API health</h3>
          {health && (
            <code>
              {health.status} @ {health.timestamp_utc}
            </code>
          )}
          {error && <p className="error">{error}</p>}
          {!health && !error && <p>Checking...</p>}
        </div>
      </header>
      <TariffList />
    </main>
  );
}
