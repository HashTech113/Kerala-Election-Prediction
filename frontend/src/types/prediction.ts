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

// ---- Scenario projections -------------------------------------------------

export type ScenarioName =
  | "base_model"
  | "votevibe"
  | "cvoter"
  | "final_weighted";

export type PredictionLevel =
  | "long_term_trend"
  | "recent_swing"
  | "live_intelligence_score";

export type ScenarioConstituency = {
  constituency: string;
  district: string;
  winner: Party;
  confidence: number;
  LDF: number;
  UDF: number;
  NDA: number;
  OTHERS: number;
  base_model_winner: Party;
  changed_from_base: boolean;
  scenario_source?: string | null;
  scenario_notes?: string | null;
};

export type KeralaScenarioResponse = {
  scenario: ScenarioName;
  scenario_name: string;
  prediction_level: PredictionLevel;
  result_status: string;
  counting_date: string;
  seat_counts: SeatCounts;
  vote_share_estimate: SeatCounts;
  confidence_level: number;
  constituencies: ScenarioConstituency[];
  changed_seats: ScenarioConstituency[];
  notes: string;
};

export const SCENARIO_LABELS: Record<ScenarioName, string> = {
  base_model: "Base Model",
  votevibe: "VoteVibe Scenario",
  cvoter: "C-Voter Scenario",
  final_weighted: "Final Weighted Scenario",
};

export const PREDICTION_LEVEL_LABELS: Record<PredictionLevel, string> = {
  long_term_trend: "Long-Term Trend",
  recent_swing: "Recent Swing",
  live_intelligence_score: "Live Intelligence Score",
};
