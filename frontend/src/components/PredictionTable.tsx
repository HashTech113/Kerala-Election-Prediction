import { PartyBadge } from "./PartyBadge";
import { PredictionRow, Party } from "../types/prediction";
import { asPercent } from "../utils/format";

interface PredictionTableProps {
  rows: PredictionRow[];
  highConfidenceCount: number;
}

/**
 * Main table displaying all predictions
 */
export function PredictionTable({
  rows,
  highConfidenceCount,
}: PredictionTableProps) {
  return (
    <section className="panel table-panel explorer-section">
      <div className="table-head">
        <h2>Constituency Explorer</h2>
        <span className="table-meta">
          High Confidence Seats: {highConfidenceCount}
        </span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Constituency</th>
              <th>District</th>
              <th>Predicted</th>
              <th>Confidence</th>
              <th>LDF</th>
              <th>UDF</th>
              <th>NDA</th>
              <th>OTHERS</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.constituency}>
                <td>{row.constituency}</td>
                <td>{row.district}</td>
                <td>
                  <PartyBadge party={row.predicted} />
                </td>
                <td>{asPercent(row.confidence)}</td>
                <td>{asPercent(row.LDF)}</td>
                <td>{asPercent(row.UDF)}</td>
                <td>{asPercent(row.NDA)}</td>
                <td>{asPercent(row.OTHERS)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
