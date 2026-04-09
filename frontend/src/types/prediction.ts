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
