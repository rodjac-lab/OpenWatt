export interface HealthPayload {
  status: string;
  service: string;
  timestamp_utc: string;
}

export interface AdminRunPayload {
  supplier: string;
  status: "ok" | "nok";
  message: string;
  observed_at?: string | null;
}

export interface AdminRunsResponse {
  generated_at: string;
  items: AdminRunPayload[];
}

export interface OverrideEntryPayload {
  id: number;
  supplier: string;
  url: string;
  observed_at?: string | null;
  created_at: string;
}

export interface OverrideHistoryResponse {
  items: OverrideEntryPayload[];
}

export interface SupplierRow {
  supplier: string;
  parser_version?: string;
  source_url?: string;
  statuses: string[];
  observations: number;
}

export interface FreshnessStats {
  stats: {
    fresh: number;
    verifying: number;
    stale: number;
    broken: number;
  };
  total: number;
}

export interface AdminSection {
  id: string;
  label: string;
}
