import { asPercent } from "../utils/format";

interface KPISectionProps {
  totalConstituencies: number;
  projectedWinner: string;
  averageConfidence: number;
  dataLoading: boolean;
}

/**
 * Displays key performance indicators: Total constituencies, winner, and confidence
 */
export function KPISection({
  totalConstituencies,
  projectedWinner,
  averageConfidence,
  dataLoading,
}: KPISectionProps) {
  if (dataLoading) return null;

  return (
    <section className="kpi-grid">
      <article className="panel kpi-card">
        <h3>Total Constituencies</h3>
        <strong>{totalConstituencies}</strong>
      </article>
      <article className="panel kpi-card">
        <h3>Projected Winner</h3>
        <strong className="winner-fade-in">{projectedWinner}</strong>
      </article>
      <article className="panel kpi-card">
        <h3>Average Confidence</h3>
        <strong>{asPercent(averageConfidence)}</strong>
      </article>
    </section>
  );
}
