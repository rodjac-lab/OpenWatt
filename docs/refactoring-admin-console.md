# Guide de Refactoring - Admin Console

## Problème Actuel

Le fichier `ui/app/admin/page.tsx` contient **462 lignes** de code, ce qui le rend:

- Difficile à maintenir
- Difficile à tester
- Violation du principe de responsabilité unique (SRP)
- Duplication de logique fetch

## Objectif

Décomposer `admin/page.tsx` en **5 composants modulaires** réutilisables et testables.

---

## Architecture Cible

```
ui/
├── app/
│   └── admin/
│       └── page.tsx                    # Orchestrateur (50 lignes max)
├── components/
│   └── admin/
│       ├── DashboardMetrics.tsx        # Métriques santé API + data quality
│       ├── IngestionJobs.tsx           # Liste jobs nightly + statuts
│       ├── SupplierManager.tsx         # Gestion fournisseurs + parsers
│       ├── PDFInspector.tsx            # Outil inspection PDF inline
│       └── OverridesManager.tsx        # Création/liste overrides manuels
├── lib/
│   └── api/
│       ├── client.ts                   # Client API réutilisable
│       └── hooks.ts                    # React hooks (useAPI, useFetch)
```

---

## Étape 1: Créer le Client API Réutilisable

**Fichier**: `ui/lib/api/client.ts`

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: unknown,
  ) {
    super(message);
    this.name = "APIError";
  }
}

export const apiClient = {
  async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Unknown error" }));
      throw new APIError(response.status, error.detail || error.message, error);
    }

    return response.json();
  },

  async get<T>(endpoint: string): Promise<T> {
    return this.fetch<T>(endpoint);
  },

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.fetch<T>(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};
```

**Fichier**: `ui/lib/api/hooks.ts`

```typescript
import { useState, useEffect } from "react";
import { apiClient, APIError } from "./client";

export function useAPI<T>(endpoint: string, autoFetch = true) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState<APIError | null>(null);

  const fetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.get<T>(endpoint);
      setData(result);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoFetch) {
      fetch();
    }
  }, [endpoint, autoFetch]);

  return { data, loading, error, refetch: fetch };
}
```

---

## Étape 2: Extraire DashboardMetrics

**Fichier**: `ui/components/admin/DashboardMetrics.tsx`

```typescript
"use client";

import { useAPI } from "@/lib/api/hooks";
import { paths } from "@/lib/openapi-types";

type HealthResponse = paths["/health"]["get"]["responses"]["200"]["content"]["application/json"];

export function DashboardMetrics() {
  const { data: health, loading, error } = useAPI<HealthResponse>("/health");

  if (loading) return <div className="metric-card">Loading...</div>;
  if (error) return <div className="metric-card error">API Offline</div>;

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <h3>API Status</h3>
        <div className="metric-value">{health?.status || "unknown"}</div>
      </div>
      {/* Plus de métriques... */}
    </div>
  );
}
```

---

## Étape 3: Extraire IngestionJobs

**Fichier**: `ui/components/admin/IngestionJobs.tsx`

```typescript
"use client";

import { useAPI } from "@/lib/api/hooks";
import { paths } from "@/lib/openapi-types";

type RunsResponse = paths["/v1/admin/runs"]["get"]["responses"]["200"]["content"]["application/json"];

export function IngestionJobs() {
  const { data, loading, error, refetch } = useAPI<RunsResponse>("/v1/admin/runs");

  return (
    <section className="jobs-panel">
      <header>
        <h2>Ingestion Jobs</h2>
        <button onClick={refetch}>Refresh</button>
      </header>

      {loading && <p>Loading jobs...</p>}
      {error && <p className="error">{error.message}</p>}

      <table>
        <thead>
          <tr>
            <th>Supplier</th>
            <th>Status</th>
            <th>Last Run</th>
            <th>Records</th>
          </tr>
        </thead>
        <tbody>
          {data?.runs.map((run) => (
            <tr key={run.id}>
              <td>{run.supplier}</td>
              <td className={`status-${run.status}`}>{run.status}</td>
              <td>{new Date(run.timestamp).toLocaleString()}</td>
              <td>{run.records_inserted}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

---

## Étape 4: Extraire PDFInspector

**Fichier**: `ui/components/admin/PDFInspector.tsx`

```typescript
"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api/client";

export function PDFInspector() {
  const [yamlConfig, setYamlConfig] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [result, setResult] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  const handleInspect = async () => {
    if (!pdfFile || !yamlConfig) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("pdf", pdfFile);
      formData.append("config", yamlConfig);

      const response = await apiClient.post("/v1/admin/inspect", formData);
      setResult(response);
    } catch (error) {
      console.error("Inspection failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="pdf-inspector">
      <h2>PDF Inspector</h2>
      <div className="inspector-form">
        <textarea
          value={yamlConfig}
          onChange={(e) => setYamlConfig(e.target.value)}
          placeholder="Paste YAML config here..."
          rows={10}
        />
        <input type="file" accept=".pdf" onChange={(e) => setPdfFile(e.target.files?.[0] || null)} />
        <button onClick={handleInspect} disabled={loading || !pdfFile || !yamlConfig}>
          {loading ? "Inspecting..." : "Inspect PDF"}
        </button>
      </div>
      {result && <pre className="result">{JSON.stringify(result, null, 2)}</pre>}
    </section>
  );
}
```

---

## Étape 5: Extraire OverridesManager

**Fichier**: `ui/components/admin/OverridesManager.tsx`

```typescript
"use client";

import { useState } from "react";
import { useAPI } from "@/lib/api/hooks";
import { apiClient } from "@/lib/api/client";
import { paths } from "@/lib/openapi-types";

type OverridesResponse = paths["/v1/admin/overrides"]["get"]["responses"]["200"]["content"]["application/json"];

export function OverridesManager() {
  const { data, loading, error, refetch } = useAPI<OverridesResponse>("/v1/admin/overrides");
  const [showCreateForm, setShowCreateForm] = useState(false);

  const handleCreate = async (formData: unknown) => {
    await apiClient.post("/v1/admin/overrides", formData);
    refetch();
    setShowCreateForm(false);
  };

  return (
    <section className="overrides-manager">
      <header>
        <h2>Manual Overrides</h2>
        <button onClick={() => setShowCreateForm(true)}>Create Override</button>
      </header>

      {/* Liste des overrides + formulaire de création */}
    </section>
  );
}
```

---

## Étape 6: Simplifier admin/page.tsx

**Fichier**: `ui/app/admin/page.tsx` (nouveau - 50 lignes max)

```typescript
import { DashboardMetrics } from "@/components/admin/DashboardMetrics";
import { IngestionJobs } from "@/components/admin/IngestionJobs";
import { SupplierManager } from "@/components/admin/SupplierManager";
import { PDFInspector } from "@/components/admin/PDFInspector";
import { OverridesManager } from "@/components/admin/OverridesManager";

export default function AdminPage() {
  return (
    <div className="admin-console">
      <h1>OpenWatt Admin Console</h1>

      <DashboardMetrics />
      <IngestionJobs />
      <SupplierManager />
      <PDFInspector />
      <OverridesManager />
    </div>
  );
}
```

---

## Étape 7: Ajouter Tests

**Fichier**: `ui/components/admin/__tests__/DashboardMetrics.test.tsx`

```typescript
import { render, screen } from "@testing-library/react";
import { DashboardMetrics } from "../DashboardMetrics";

// Mock useAPI hook
jest.mock("@/lib/api/hooks", () => ({
  useAPI: () => ({
    data: { status: "ok", service: "OpenWatt API" },
    loading: false,
    error: null,
  }),
}));

describe("DashboardMetrics", () => {
  it("displays API status", () => {
    render(<DashboardMetrics />);
    expect(screen.getByText("ok")).toBeInTheDocument();
  });
});
```

---

## Bénéfices du Refactoring

### Avant

- ✅ 1 fichier de 462 lignes
- ❌ Difficile à tester
- ❌ Logique fetch dupliquée
- ❌ Violation SRP

### Après

- ✅ 7 fichiers modulaires (50-100 lignes chacun)
- ✅ Composants testables isolément
- ✅ Client API réutilisable
- ✅ Respect SRP
- ✅ Meilleure maintenabilité

---

## Checklist d'Implémentation

- [ ] Créer `ui/lib/api/client.ts`
- [ ] Créer `ui/lib/api/hooks.ts`
- [ ] Créer `ui/components/admin/DashboardMetrics.tsx`
- [ ] Créer `ui/components/admin/IngestionJobs.tsx`
- [ ] Créer `ui/components/admin/SupplierManager.tsx`
- [ ] Créer `ui/components/admin/PDFInspector.tsx`
- [ ] Créer `ui/components/admin/OverridesManager.tsx`
- [ ] Simplifier `ui/app/admin/page.tsx`
- [ ] Ajouter tests unitaires pour chaque composant
- [ ] Migrer styles CSS vers fichiers modulaires
- [ ] Valider avec `npm run build`

---

## Estimation

**Temps requis**: 4-6 heures
**Complexité**: Moyenne
**Priorité**: Haute (améliore qualité code et testabilité)
