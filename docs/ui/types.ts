export type FreshnessStatus = "fresh" | "verifying" | "stale" | "broken";

export interface Tariff {
  supplier: string;
  option: "BASE" | "HPHC" | "TEMPO";
  puissance_kva: 3 | 6 | 9 | 12 | 15 | 18 | 24 | 30 | 36;
  price_kwh_ttc: number | null;
  price_kwh_hp_ttc: number | null;
  price_kwh_hc_ttc: number | null;
  abo_month_ttc: number;
  observed_at: string; // ISO datetime
  parser_version: string;
  source_url: string;
  source_checksum: string;
  data_status: FreshnessStatus;
  last_verified?: string | null;
}

export interface TariffHistoryResponse {
  filters: Record<string, unknown>;
  items: Tariff[];
}

export interface TrveDiffEntry {
  supplier: string;
  option: Tariff["option"];
  puissance_kva: Tariff["puissance_kva"];
  delta_eur_per_mwh: number;
  compared_at: string;
  status: "ok" | "alert";
}
