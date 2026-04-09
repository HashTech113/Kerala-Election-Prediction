import { Party } from "../types/prediction";

interface DistrictBreakdownPanelProps {
  districts: Array<{
    name: string;
    LDF: number;
    UDF: number;
    NDA: number;
    OTHERS: number;
    total: number;
  }>;
}

const PARTIES: Party[] = ["LDF", "UDF", "NDA", "OTHERS"];

/**
 * Shows seat distribution by district
 */
export function DistrictBreakdownPanel({
  districts,
}: DistrictBreakdownPanelProps) {
  return (
    <article className="panel">
      <h2>District Breakdown</h2>
      <div className="district-list">
        {districts.map((d) => (
          <div key={d.name} className="district-item">
            <div className="district-head">
              <strong>{d.name}</strong>
              <span>{d.total} seats</span>
            </div>
            <div className="district-bars">
              {PARTIES.map((p) => (
                <div
                  key={p}
                  className={`district-segment segment-${p}`}
                  style={{ width: `${(d[p] / (d.total || 1)) * 100}%` }}
                  title={`${p}: ${d[p]}`}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}
