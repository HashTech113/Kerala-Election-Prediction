export type Party = "LDF" | "UDF" | "NDA" | "OTHERS";

export type PredictionRow = {
  constituency: string;
  district: string;
  predicted: Party;
  confidence: number;
  LDF: number;
  UDF: number;
  NDA: number;
  OTHERS: number;
};

export type SeatCounts = Record<Party, number>;

export type PredictionsMeta = {
  api_version?: string;
  source_file: string;
  source_path?: string;
  source_last_modified_utc?: string | null;
  source_sha256?: string | null;
  fallback_in_use: boolean;
  allow_assembly_fallback?: boolean;
  total_constituencies: number;
  seat_counts: SeatCounts;
  projected_winner: Party | "-";
};

export type HealthResponse = {
  status: "ok" | "error";
  api_version?: string;
  meta?: PredictionsMeta;
  error?: string;
};
