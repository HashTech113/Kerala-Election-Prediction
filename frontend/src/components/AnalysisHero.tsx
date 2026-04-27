import { useMemo, useState } from "react";
import { PROJECTION_SUMMARIES, ProjectionTab } from "../types/prediction";
import { asPercent } from "../utils/format";

type TabId = "historical" | "long_term" | "recent_swing" | "live_score";

const TABS: Array<{ id: TabId; label: string }> = [
  {
    id: "historical",
    label: "HISTORICAL PROJECTION",
  },
  { id: "long_term", label: "LONG-TERM TREND" },
  { id: "recent_swing", label: "RECENT SWING" },
  {
    id: "live_score",
    label: "LIVE INTELLIGENCE SCORE",
  },
];

const TAB_TO_PROJECTION: Record<TabId, ProjectionTab> = {
  historical: "historical_projection",
  long_term: "long_term_trend",
  recent_swing: "recent_swing",
  live_score: "live_intelligence_score",
};

export function AnalysisHero() {
  const [activeTab, setActiveTab] = useState<TabId>("historical");
  const activeProjection = TAB_TO_PROJECTION[activeTab];
  const summary = PROJECTION_SUMMARIES[activeProjection];

  const kpi = useMemo(
    () => [
      {
        label: "TOTAL CONSTITUENCIES",
        value: String(summary.totalConstituencies),
      },
      { label: "DATA REFERENCE", value: summary.dataReference },
      { label: "PROJECTED WINNER", value: summary.projectedWinner },
      { label: "AVERAGE WINNING SCORE", value: asPercent(summary.averageWinningScore) },
    ],
    [summary]
  );

  return (
    <section className="ep-section">
      <header className="ep-hero">
        <div className="ep-brand">
          <img
            src="/assets/owlytics.png"
            alt="Owlytics logo"
            className="ep-logo"
            width={56}
            height={56}
            decoding="async"
          />
          <h1>Election Predictions</h1>
        </div>
        <p>
          Our <span>Intelligent AI</span> tracked every vote across{" "}
          <span>Kerala&apos;s</span> constituencies, uncovered key trends, and predicted who will
          form the next government.
        </p>
      </header>

      <nav className="ep-tabs" aria-label="Prediction analysis tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`ep-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
            type="button"
            aria-pressed={activeTab === tab.id}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <section className="ep-kpi">
        {kpi.map((item) => (
          <article key={item.label} className="ep-kpi-item">
            <h3>{item.label}</h3>
            <strong>{item.value}</strong>
          </article>
        ))}
      </section>
    </section>
  );
}
