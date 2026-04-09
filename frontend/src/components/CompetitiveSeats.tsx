import { PartyBadge } from "./PartyBadge";
import { PredictionRow, Party } from "../types/prediction";
import { asPercent } from "../utils/format";

interface CompetitiveSeatsProps {
  seats: PredictionRow[];
}

/**
 * Displays the most competitive (closest margin) seats
 */
export function CompetitiveSeats({ seats }: CompetitiveSeatsProps) {
  return (
    <article className="panel">
      <h2>Most Competitive Seats</h2>
      <ul className="tight-list">
        {seats.map((seat) => (
          <li key={seat.constituency}>
            <div>
              <strong>{seat.constituency}</strong>
              <small>{seat.district}</small>
            </div>
            <div className="right-inline">
              <PartyBadge party={seat.predicted} />
              <span>{asPercent(seat.confidence)}</span>
            </div>
          </li>
        ))}
      </ul>
    </article>
  );
}
