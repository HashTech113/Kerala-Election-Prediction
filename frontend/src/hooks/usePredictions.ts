import { useCallback, useEffect, useMemo, useState } from "react";
import { checkHealth, fetchPredictions } from "../services/api";
import { PredictionRow, Party } from "../types/prediction";

const PARTIES: Party[] = ["LDF", "UDF", "NDA", "OTHERS"];
const HIGH_CONFIDENCE_THRESHOLD = 0.75;

interface SeatCounts {
  [key in Party]: number;
}

interface DistrictBreakdown {
  name: string;
  LDF: number;
  UDF: number;
  NDA: number;
  OTHERS: number;
  total: number;
}

/**
 * Custom hook for managing prediction data fetching and calculations.
 * Handles data loading, filtering, and derived metrics.
 */
export function usePredictions() {
  const [rows, setRows] = useState<PredictionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load predictions on mount
  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);

      try {
        const healthy = await checkHealth();
        if (!healthy) throw new Error("Backend health check failed.");

        const predictions = await fetchPredictions();
        setRows(predictions);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(
          `${message} Check that the backend API is running and accessible.`
        );
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  // Get all unique districts
  const districts = useMemo(() => {
    return [...new Set(rows.map((r) => r.district))].sort((a, b) =>
      a.localeCompare(b)
    );
  }, [rows]);

  // Filter rows based on criteria
  const filterRows = useCallback(
    (
      district: string,
      party: Party | "ALL",
      query: string
    ): PredictionRow[] => {
      const q = query.trim().toLowerCase();
      const filtered = rows.filter((r) => {
        const districtOk = district === "ALL" || r.district === district;
        const partyOk = party === "ALL" || r.predicted === party;
        const queryOk = q.length === 0 || r.constituency.toLowerCase().includes(q);
        return districtOk && partyOk && queryOk;
      });

      filtered.sort((a, b) => b.confidence - a.confidence);
      return filtered;
    },
    [rows]
  );

  // Get seat counts for parties
  const getSeatCounts = useCallback((filteredRows: PredictionRow[]): SeatCounts => {
    const counts: SeatCounts = {
      LDF: 0,
      UDF: 0,
      NDA: 0,
      OTHERS: 0,
    };

    for (const row of filteredRows) {
      counts[row.predicted] += 1;
    }

    return counts;
  }, []);

  // Get projected winner
  const getProjectedWinner = useCallback((filteredRows: PredictionRow[]): Party | "-" => {
    if (filteredRows.length === 0) return "-";
    const counts = getSeatCounts(filteredRows);
    return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0] as Party;
  }, [getSeatCounts]);

  // Get district breakdown
  const getDistrictBreakdown = useCallback((filteredRows: PredictionRow[]): DistrictBreakdown[] => {
    const map = new Map<string, Record<Party, number>>();

    for (const row of filteredRows) {
      if (!map.has(row.district)) {
        map.set(row.district, { LDF: 0, UDF: 0, NDA: 0, OTHERS: 0 });
      }
      map.get(row.district)![row.predicted] += 1;
    }

    return [...map.entries()]
      .map(([name, counts]) => ({
        name,
        ...counts,
        total: counts.LDF + counts.UDF + counts.NDA + counts.OTHERS,
      }))
      .sort((a, b) => a.name.localeCompare(b));
  }, []);

  // Get closest/tightest seats
  const getClosestSeats = useCallback((filteredRows: PredictionRow[]): PredictionRow[] => {
    return [...filteredRows]
      .sort((a, b) => a.confidence - b.confidence)
      .slice(0, 8);
  }, []);

  // Calculate average confidence
  const calculateAverageConfidence = useCallback((filteredRows: PredictionRow[]): number => {
    if (filteredRows.length === 0) return 0;
    return filteredRows.reduce((sum, r) => sum + r.confidence, 0) / filteredRows.length;
  }, []);

  // Count high confidence predictions
  const countHighConfidence = useCallback((filteredRows: PredictionRow[]): number => {
    return filteredRows.filter((r) => r.confidence >= HIGH_CONFIDENCE_THRESHOLD).length;
  }, []);

  return {
    rows,
    loading,
    error,
    districts,
    filterRows,
    getSeatCounts,
    getProjectedWinner,
    getDistrictBreakdown,
    getClosestSeats,
    calculateAverageConfidence,
    countHighConfidence,
  };
}
