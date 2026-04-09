import { Party } from "../types/prediction";
import { asSeatPercent } from "../utils/format";

interface SeatDistributionProps {
  parties: Party[];
  seatCounts: Record<Party, number>;
  total: number;
}

/**
 * Bar chart showing seat distribution across parties
 */
export function SeatDistribution({
  parties,
  seatCounts,
  total,
}: SeatDistributionProps) {
  const safeTotal = total || 1;

  return (
    <section className="inner-block">
      <h2>Seat Distribution</h2>
      <div className="bar-list">
        {parties.map((p) => (
          <div className="bar-item" key={p}>
            <div className="bar-top">
              <span>{p}</span>
              <span>
                {seatCounts[p]} ({asSeatPercent(seatCounts[p], safeTotal)})
              </span>
            </div>
            <div className="bar-track">
              <div
                className={`bar-fill fill-${p}`}
                style={{ width: `${(seatCounts[p] / safeTotal) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
