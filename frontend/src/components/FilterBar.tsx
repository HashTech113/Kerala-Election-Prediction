import { Party } from "../types/prediction";

interface FilterBarProps {
  district: string;
  districts: string[];
  party: Party | "ALL";
  query: string;
  onDistrictChange: (district: string) => void;
  onPartyChange: (party: Party | "ALL") => void;
  onQueryChange: (query: string) => void;
}

const PARTIES: (Party | "ALL")[] = ["ALL", "LDF", "UDF", "NDA", "OTHERS"];

/**
 * Filter controls for predictions
 */
export function FilterBar({
  district,
  districts,
  party,
  query,
  onDistrictChange,
  onPartyChange,
  onQueryChange,
}: FilterBarProps) {
  return (
    <section className="inner-block">
      <h2>Filters</h2>
      <div className="filters-grid">
        <div>
          <label htmlFor="district">District</label>
          <select id="district" value={district} onChange={(e) => onDistrictChange(e.target.value)}>
            <option value="ALL">All Districts</option>
            {districts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="party">Predicted Party</label>
          <select
            id="party"
            value={party}
            onChange={(e) => onPartyChange(e.target.value as Party | "ALL")}
          >
            {PARTIES.map((p) => (
              <option key={p} value={p}>
                {p === "ALL" ? "All Parties" : p}
              </option>
            ))}
          </select>
        </div>

        <div className="search-wrap">
          <label htmlFor="search">Search Constituency</label>
          <input
            id="search"
            type="text"
            value={query}
            placeholder="Type constituency name..."
            onChange={(e) => onQueryChange(e.target.value)}
          />
        </div>
      </div>
    </section>
  );
}
