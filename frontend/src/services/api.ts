import { PredictionRow } from "../types/prediction";

/**
 * API Base URL Configuration
 * Priority:
 * 1. VITE_API_BASE_URL (preferred)
 * 2. VITE_API_URL (fallback)
 * 3. Default to http://127.0.0.1:8001 if neither is set
 *
 * For production (Railway): Set VITE_API_BASE_URL to your Railway backend URL
 * For local dev: Use .env with VITE_API_BASE_URL=http://127.0.0.1:8001
 */
const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  import.meta.env.VITE_API_URL?.trim() ||
  "http://127.0.0.1:8001";

function withCacheBuster(path: string): string {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}_ts=${Date.now()}`;
}

// Debug logging (helpful for troubleshooting)
if (import.meta.env.DEV) {
  console.log(
    "[API Config] API_BASE_URL:",
    API_BASE,
    "| VITE_API_BASE_URL:",
    import.meta.env.VITE_API_BASE_URL,
    "| VITE_API_URL:",
    import.meta.env.VITE_API_URL
  );
}

/**
 * Validates that the API_BASE URL is set
 * Logs a warning if using default localhost
 */
function validateApiConfig(): void {
  if (!API_BASE) {
    console.error(
      "[API Config] ERROR: API_BASE is not configured. Set VITE_API_BASE_URL in your .env file."
    );
  } else if (API_BASE === "http://127.0.0.1:8001" && import.meta.env.PROD) {
    console.warn(
      "[API Config] WARNING: Using localhost API_BASE in production. Set VITE_API_BASE_URL to your Railway backend URL."
    );
  }
}

// Validate on module load
validateApiConfig();

export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(withCacheBuster(`${API_BASE}/api/health`), {
      signal,
      cache: "no-store",
    });
    if (!response.ok) {
      console.warn(
        `[API] Health check failed: ${response.status} ${response.statusText}`
      );
      return false;
    }
    const body = await response.json();
    return body?.status === "ok";
  } catch (error) {
    console.error("[API] Health check error:", error);
    return false;
  }
}

export async function fetchPredictions(signal?: AbortSignal): Promise<PredictionRow[]> {
  try {
    const response = await fetch(withCacheBuster(`${API_BASE}/api/predictions`), {
      signal,
      cache: "no-store",
    });
    if (!response.ok) {
      const errorMsg = `Failed to load predictions (${response.status} ${response.statusText}) from ${API_BASE}`;
      console.error("[API]", errorMsg);
      throw new Error(errorMsg);
    }
    const source = response.headers.get("X-Predictions-Source");
    const fallback = response.headers.get("X-Predictions-Fallback") === "1";
    if (source) {
      console.info(
        `[API] Predictions source: ${source}${fallback ? " (fallback mode)" : ""}`
      );
    }
    const data: PredictionRow[] = await response.json();
    return data;
  } catch (error) {
    if (error instanceof TypeError) {
      console.error(
        "[API] Network error - unable to reach backend at",
        API_BASE,
        error
      );
    }
    throw error;
  }
}

export { API_BASE };
