import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { PartyBadge } from "./components/PartyBadge";
import { API_BASE, checkHealth, fetchPredictions } from "./services/api";
import { PredictionRow, Party } from "./types/prediction";
import { asPercent, asSeatPercent } from "./utils/format";

const PARTIES: Party[] = ["LDF", "UDF", "NDA", "OTHERS"];
const HIGH_CONFIDENCE_THRESHOLD = 0.75;

function getSeatCounts(rows: PredictionRow[]) {
  const counts: Record<Party, number> = {
    LDF: 0,
    UDF: 0,
    NDA: 0,
    OTHERS: 0,
  };

  for (const row of rows) counts[row.predicted] += 1;
  return counts;
}

function getProjectedWinner(rows: PredictionRow[]): Party | "-" {
  if (rows.length === 0) return "-";
  const counts = getSeatCounts(rows);
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0] as Party;
}

export function App() {
  const [rows, setRows] = useState<PredictionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [district, setDistrict] = useState("ALL");
  const [party, setParty] = useState<Party | "ALL">("ALL");
  const [query, setQuery] = useState("");
  const [animatedConfidence, setAnimatedConfidence] = useState(0);
  const [animatedTotal, setAnimatedTotal] = useState(0);
  const [animatedWinner, setAnimatedWinner] = useState("");
  const [kpiAnimCycle, setKpiAnimCycle] = useState(1);
  const kpiGridRef = useRef<HTMLElement | null>(null);
  const middleStageRef = useRef<HTMLElement | null>(null);
  const leftCardRef = useRef<HTMLElement | null>(null);
  const centerCardRef = useRef<HTMLElement | null>(null);
  const rightCardRef = useRef<HTMLElement | null>(null);
  const middleAnimDebounceRef = useRef<number | null>(null);
  const middleAnimLastRunRef = useRef(-10000);

  const replayMiddleStageAnimation = useCallback(() => {
    const element = middleStageRef.current;
    if (!element) return;

    const now = performance.now();
    if (now - middleAnimLastRunRef.current < 700) return;
    middleAnimLastRunRef.current = now;

    element.classList.remove("animate-cards");
    void element.offsetWidth;
    element.classList.add("animate-cards");
  }, []);

  const replayCardAnimation = useCallback((element: HTMLElement | null) => {
    if (!element) return;

    const lineEls = element.querySelectorAll<HTMLElement>(".bar-fill, .district-segment");
    for (const line of lineEls) {
      line.classList.remove("line-grow");
      void line.offsetWidth;
      line.classList.add("line-grow");
    }
  }, []);

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
        setError(`${message} Ensure backend is running on ${API_BASE}.`);
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const districts = useMemo(() => {
    return [...new Set(rows.map((r) => r.district))].sort((a, b) => a.localeCompare(b));
  }, [rows]);

  const filteredRows = useMemo(() => {
    const q = query.trim().toLowerCase();

    const next = rows.filter((r) => {
      const districtOk = district === "ALL" || r.district === district;
      const partyOk = party === "ALL" || r.predicted === party;
      const queryOk = q.length === 0 || r.constituency.toLowerCase().includes(q);
      return districtOk && partyOk && queryOk;
    });

    next.sort((a, b) => b.confidence - a.confidence);

    return next;
  }, [rows, district, party, query]);

  const seatCounts = useMemo(() => getSeatCounts(filteredRows), [filteredRows]);
  const sortedParties = useMemo(() => {
    return [...PARTIES].sort((a, b) => seatCounts[b] - seatCounts[a]);
  }, [seatCounts]);
  const total = filteredRows.length;
  const safeTotal = total || 1;
  const projectedWinner = getProjectedWinner(filteredRows);
  const averageConfidence =
    filteredRows.reduce((sum, r) => sum + r.confidence, 0) / safeTotal;
  const highConfidence = filteredRows.filter(
    (r) => r.confidence >= HIGH_CONFIDENCE_THRESHOLD,
  ).length;

  const closestSeats = useMemo(() => {
    return [...filteredRows]
      .sort((a, b) => a.confidence - b.confidence)
      .slice(0, 8);
  }, [filteredRows]);

  const districtBreakdown = useMemo(() => {
    const map = new Map<string, Record<Party, number>>();

    for (const row of filteredRows) {
      if (!map.has(row.district)) {
        map.set(row.district, { LDF: 0, UDF: 0, NDA: 0, OTHERS: 0 });
      }
      map.get(row.district)![row.predicted] += 1;
    }

    return [...map.entries()]
      .map(([name, counts]) => ({ name, ...counts, total: counts.LDF + counts.UDF + counts.NDA + counts.OTHERS }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [filteredRows]);

  useEffect(() => {
    const target = averageConfidence;
    const durationMs = 1200;
    const start = performance.now();
    const from = 0;

    let frameId = 0;
    const tick = (now: number) => {
      const t = Math.min((now - start) / durationMs, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      const value = from + (target - from) * eased;
      setAnimatedConfidence(value);
      if (t < 1) frameId = requestAnimationFrame(tick);
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [averageConfidence, kpiAnimCycle]);

  useEffect(() => {
    const target = total;
    const durationMs = 900;
    const start = performance.now();
    const from = 0;

    let frameId = 0;
    const tick = (now: number) => {
      const t = Math.min((now - start) / durationMs, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      const value = from + (target - from) * eased;
      setAnimatedTotal(Math.round(value));
      if (t < 1) frameId = requestAnimationFrame(tick);
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [total, kpiAnimCycle]);

  useEffect(() => {
    const winnerText = String(projectedWinner);
    if (winnerText.length <= 1) {
      setAnimatedWinner(winnerText);
      return;
    }

    setAnimatedWinner("");
    let index = 0;
    let intervalId: number | undefined;

    const startTimeoutId = window.setTimeout(() => {
      intervalId = window.setInterval(() => {
        index += 1;
        setAnimatedWinner(winnerText.slice(0, index));
        if (index >= winnerText.length && intervalId) {
          window.clearInterval(intervalId);
        }
      }, 140);
    }, 120);

    return () => {
      window.clearTimeout(startTimeoutId);
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [projectedWinner, kpiAnimCycle]);

  useEffect(() => {
    const element = kpiGridRef.current;
    if (!element) return;

    let wasInView = false;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.35 && !wasInView) {
            wasInView = true;
            setKpiAnimCycle((c) => c + 1);
          } else if (!entry.isIntersecting || entry.intersectionRatio <= 0.08) {
            wasInView = false;
          }
        }
      },
      { threshold: [0, 0.08, 0.35, 0.45] },
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [loading, error]);

  useEffect(() => {
    const element = middleStageRef.current;
    if (!element) return;

    let wasInView = false;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (
            entry.isIntersecting &&
            entry.intersectionRatio >= 0.12 &&
            !wasInView
          ) {
            wasInView = true;
            replayMiddleStageAnimation();
          } else if (!entry.isIntersecting || entry.intersectionRatio <= 0.06) {
            wasInView = false;
            element.classList.remove("animate-cards");
          }
        }
      },
      { threshold: [0, 0.06, 0.12, 0.28] },
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [loading, error, replayMiddleStageAnimation]);

  useEffect(() => {
    if (loading || error) return;
    const element = middleStageRef.current;
    if (!element) return;

    const id = window.setTimeout(() => {
      replayMiddleStageAnimation();
    }, 140);

    return () => window.clearTimeout(id);
  }, [loading, error, replayMiddleStageAnimation]);

  useEffect(() => {
    const leftStack = leftCardRef.current;
    const centerCard = centerCardRef.current;
    const rightStack = rightCardRef.current;

    const cards = [
      {
        targetNode: leftStack,
        listenNode: leftStack?.querySelector<HTMLElement>(".panel") ?? leftStack,
        hasLines: true,
      },
      {
        targetNode: centerCard,
        listenNode: centerCard,
        hasLines: true,
      },
      {
        targetNode: rightStack,
        listenNode: rightStack?.querySelector<HTMLElement>(".panel") ?? rightStack,
        hasLines: false,
      },
    ];

    const cleanups: Array<() => void> = [];

    for (const card of cards) {
      const targetNode = card.targetNode;
      const listenNode = card.listenNode;
      if (!targetNode || !listenNode) continue;

      const onScrollLike = () => {
        if (middleAnimDebounceRef.current) {
          window.clearTimeout(middleAnimDebounceRef.current);
        }
        middleAnimDebounceRef.current = window.setTimeout(() => {
          if (card.hasLines) {
            replayCardAnimation(targetNode);
          }
        }, 120);
      };

      // Trigger only when this specific card is actually scrolled.
      listenNode.addEventListener("scroll", onScrollLike, { passive: true });

      cleanups.push(() => {
        listenNode.removeEventListener("scroll", onScrollLike);
      });
    }

    return () => {
      if (middleAnimDebounceRef.current) {
        window.clearTimeout(middleAnimDebounceRef.current);
      }
      for (const cleanup of cleanups) cleanup();
    };
  }, [loading, error, replayCardAnimation]);

  return (
    <div className="app-shell">
      <div className="bg-blur bg-blur-a" />
      <div className="bg-blur bg-blur-b" />

      <main className="container">
        <header className="hero">
          <div className="hero-inner">
            <div className="brand-line" aria-label="QVotelytics">
              <img src="/owlytics" alt="Q logo" className="q-logo" />
              <h1 className="brand-title">Election Prediction</h1>
            </div>
            <p className="hero-tagline">
              Track every vote across Kerala&apos;s constituencies and see who rises to
              power to form the government
            </p>
          </div>
        </header>

        {error && <div className="error-banner">{error}</div>}
        {loading && <div className="panel loading">Loading predictions...</div>}

        {!loading && !error && (
          <>
            <section className="kpi-grid" ref={kpiGridRef}>
              <article className="panel kpi-card">
                <h3>Total Constituencies</h3>
                <strong>{animatedTotal}</strong>
              </article>
              <article className="panel kpi-card">
                <h3>Projected Winner</h3>
                <strong className="winner-fade-in">{animatedWinner}</strong>
              </article>
              <article className="panel kpi-card">
                <h3>Average Confidence</h3>
                <strong>{asPercent(animatedConfidence)}</strong>
              </article>
            </section>

            <section className="middle-stage" ref={middleStageRef}>
              <aside className="left-stack" ref={leftCardRef}>
                <article className="panel">
                  <h2>District Breakdown</h2>
                  <div className="district-list">
                    {districtBreakdown.map((d) => (
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
              </aside>

              <article className="panel center-card" ref={centerCardRef}>
                <div className="center-inner-grid">
                  <section className="inner-block">
                    <h2>Filters</h2>
                    <div className="filters-grid">
                      <div>
                        <label htmlFor="district">District</label>
                        <select
                          id="district"
                          value={district}
                          onChange={(e) => setDistrict(e.target.value)}
                        >
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
                          onChange={(e) => setParty(e.target.value as Party | "ALL")}
                        >
                          <option value="ALL">All Parties</option>
                          {PARTIES.map((p) => (
                            <option key={p} value={p}>
                              {p}
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
                          onChange={(e) => setQuery(e.target.value)}
                        />
                      </div>
                    </div>
                  </section>

                  <section className="inner-block">
                    <h2>Seat Distribution</h2>
                    <div className="bar-list">
                      {sortedParties.map((p) => (
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
                </div>
              </article>

              <aside className="right-stack" ref={rightCardRef}>
                <article className="panel">
                  <h2>Most Competitive Seats</h2>
                  <ul className="tight-list">
                    {closestSeats.map((seat) => (
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
              </aside>
            </section>

            <section className="panel table-panel explorer-section">
              <div className="table-head">
                <h2>Constituency Explorer</h2>
                <span className="table-meta">
                  High Confidence Seats: {highConfidence}
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
                    {filteredRows.map((row) => (
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
          </>
        )}
      </main>
    </div>
  );
}
