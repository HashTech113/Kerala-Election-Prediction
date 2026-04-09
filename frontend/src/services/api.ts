import { PredictionRow } from "../types/prediction";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  import.meta.env.VITE_API_URL?.trim() ||
  "http://127.0.0.1:8001";

export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  const response = await fetch(`${API_BASE}/api/health`, { signal });
  if (!response.ok) return false;
  const body = await response.json();
  return body?.status === "ok";
}

export async function fetchPredictions(signal?: AbortSignal): Promise<PredictionRow[]> {
  const response = await fetch(`${API_BASE}/api/predictions`, { signal });
  if (!response.ok) {
    throw new Error(`Failed to load predictions (${response.status})`);
  }
  const data: PredictionRow[] = await response.json();
  return data;
}

export { API_BASE };
