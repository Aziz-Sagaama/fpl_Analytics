export type Position = "GK" | "DEF" | "MID" | "FWD";

export interface Player {
  full_name: string;
  element_type: Position;
  minutes: number;
  goals_scored: number;
  assists: number;
  total_points: number;
  creativity: number;
  influence: number;
  threat: number;
  ict_index: number;
  clean_sheets: number;
  cost_m: number;
}

export interface PositionStats {
  position: Position;
  players: number;
  average_total_points: number;
  average_price: number;
  points: number[];
  prices: number[];
  minutes: number[];
}

export interface HistogramBin {
  label: string;
  from: number;
  to: number;
  count: number;
}

export interface AdvancedData {
  players: Player[];
  top_players: { player: string; position: Position; total_points: number }[];
  position_stats: PositionStats[];
  price_histogram: HistogramBin[];
  points_histogram: HistogramBin[];
  price_summary: { mean: number; median: number };
  points_summary: { mean: number; median: number };
  correlation_features: string[];
  correlation_matrix: { row: string; values: number[] }[];
}

export interface Overview {
  total_players: number;
  feature_count: number;
  position_count: number;
  average_total_points: number;
  average_price: number;
  missing_values: number;
  duplicate_records: number;
}

export interface Analysis {
  player: string;
  position: Position;
  price: number;
  actual_total_points: number;
  predicted_points: number;
  points_per_million?: number;
  recruitment_score: number | null;
  verdict: "RECRUIT" | "MONITOR" | "AVOID" | "INSUFFICIENT DATA";
  explanation: string;
  metrics?: Record<string, number>;
  comparison_players?: number;
}

export interface Recommendation {
  first_name: string;
  second_name: string;
  price: number;
  total_points: number;
  predicted_points: number;
  points_per_million: number;
}

export interface RecommendationResponse {
  position: Position;
  budget: number;
  player_budget: number;
  total_candidates: number;
  recommendations: Recommendation[];
  message?: string;
}
