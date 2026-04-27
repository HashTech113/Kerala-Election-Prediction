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

// ---- Projection summary tabs (UI-only; not sent to backend) --------------

export type ProjectionTab =
  | "historical_projection"
  | "long_term_trend"
  | "recent_swing"
  | "live_intelligence_score";

export type ProjectionSummary = {
  tab: ProjectionTab;
  label: string;
  totalConstituencies: number;
  dataReference: string;
  projectedWinner: Party;
  averageWinningScore: number; // fraction in [0, 1]
};

export const PROJECTION_TAB_LABELS: Record<ProjectionTab, string> = {
  historical_projection: "Historical Projection",
  long_term_trend: "Long-Term Trend",
  recent_swing: "Recent Swing",
  live_intelligence_score: "Live Intelligence Score",
};

// Values come from backend/data_files/kerala_past_election_projection_summary.csv,
// produced by `python backend/generate_scores.py`. Re-bake when that file changes.
export const PROJECTION_SUMMARIES: Record<ProjectionTab, ProjectionSummary> = {
  historical_projection: {
    tab: "historical_projection",
    label: "Historical Projection",
    totalConstituencies: 140,
    dataReference: "2011 – 2026",
    projectedWinner: "UDF",
    averageWinningScore: 0.4853,
  },
  long_term_trend: {
    tab: "long_term_trend",
    label: "Long-Term Trend",
    totalConstituencies: 140,
    dataReference: "2014 – 2026",
    projectedWinner: "LDF",
    averageWinningScore: 0.7849,
  },
  recent_swing: {
    tab: "recent_swing",
    label: "Recent Swing",
    totalConstituencies: 140,
    dataReference: "2024 – 2026",
    projectedWinner: "UDF",
    averageWinningScore: 0.4532,
  },
  live_intelligence_score: {
    tab: "live_intelligence_score",
    label: "Live Intelligence Score",
    totalConstituencies: 140,
    dataReference: "LIVE DATA",
    projectedWinner: "UDF",
    averageWinningScore: 0.4853,
  },
};
