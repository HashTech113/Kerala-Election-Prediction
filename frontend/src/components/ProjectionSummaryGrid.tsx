import { useEffect, useRef, useState } from "react";
import { ProjectionSummary } from "../types/prediction";
import { asPercent } from "../utils/format";

interface ProjectionSummaryGridProps {
  summary: ProjectionSummary;
}

let hasAnimatedSummaryInSession = false;

export function ProjectionSummaryGrid({ summary }: ProjectionSummaryGridProps) {
  const gridRef = useRef<HTMLElement | null>(null);
  const hasAnimatedRef = useRef(hasAnimatedSummaryInSession);
  const previousWinnerRef = useRef(
    hasAnimatedRef.current ? summary.projectedWinner : "",
  );

  const [animatedTotal, setAnimatedTotal] = useState(
    hasAnimatedRef.current ? summary.totalConstituencies : 0,
  );
  const [animatedScore, setAnimatedScore] = useState(
    hasAnimatedRef.current ? summary.averageWinningScore : 0,
  );
  const [animatedWinner, setAnimatedWinner] = useState(
    hasAnimatedRef.current ? summary.projectedWinner : "",
  );
  const [winnerRollToken, setWinnerRollToken] = useState(
    hasAnimatedRef.current ? 1 : 0,
  );

  useEffect(() => {
    if (!hasAnimatedRef.current) return;
    setAnimatedTotal(summary.totalConstituencies);
    setAnimatedScore(summary.averageWinningScore);
    if (previousWinnerRef.current !== summary.projectedWinner) {
      previousWinnerRef.current = summary.projectedWinner;
      setAnimatedWinner(summary.projectedWinner);
      setWinnerRollToken((prev) => prev + 1);
    }
  }, [
    summary.totalConstituencies,
    summary.averageWinningScore,
    summary.projectedWinner,
  ]);

  useEffect(() => {
    const element = gridRef.current;
    if (!element || hasAnimatedRef.current) return;

    let scoreFrameId = 0;
    let totalFrameId = 0;

    const triggerAnimationOnce = () => {
      if (hasAnimatedRef.current) return;
      hasAnimatedRef.current = true;
      hasAnimatedSummaryInSession = true;

      const scoreDurationMs = 1200;
      const scoreStart = performance.now();
      const scoreTarget = summary.averageWinningScore;
      const scoreTick = (now: number) => {
        const t = Math.min((now - scoreStart) / scoreDurationMs, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        setAnimatedScore(scoreTarget * eased);
        if (t < 1) scoreFrameId = requestAnimationFrame(scoreTick);
      };
      scoreFrameId = requestAnimationFrame(scoreTick);

      const totalDurationMs = 900;
      const totalStart = performance.now();
      const totalTarget = summary.totalConstituencies;
      const totalTick = (now: number) => {
        const t = Math.min((now - totalStart) / totalDurationMs, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        setAnimatedTotal(Math.round(totalTarget * eased));
        if (t < 1) totalFrameId = requestAnimationFrame(totalTick);
      };
      totalFrameId = requestAnimationFrame(totalTick);

      previousWinnerRef.current = summary.projectedWinner;
      setAnimatedWinner(summary.projectedWinner);
      setWinnerRollToken((prev) => prev + 1);
    };

    if (typeof IntersectionObserver === "undefined") {
      triggerAnimationOnce();
      return () => {
        cancelAnimationFrame(scoreFrameId);
        cancelAnimationFrame(totalFrameId);
      };
    }

    const observer = new IntersectionObserver(
      (entries, observerInstance) => {
        const shouldAnimate = entries.some(
          (entry) => entry.isIntersecting && entry.intersectionRatio >= 0.35,
        );
        if (!shouldAnimate) return;
        triggerAnimationOnce();
        observerInstance.disconnect();
      },
      { threshold: [0, 0.35] },
    );

    observer.observe(element);
    const fallbackTimerId = window.setTimeout(triggerAnimationOnce, 300);

    return () => {
      window.clearTimeout(fallbackTimerId);
      observer.disconnect();
      cancelAnimationFrame(scoreFrameId);
      cancelAnimationFrame(totalFrameId);
    };
  }, [
    summary.averageWinningScore,
    summary.totalConstituencies,
    summary.projectedWinner,
  ]);

  return (
    <section className="kpi-grid kpi-grid-4" ref={gridRef}>
      <article className="panel kpi-card">
        <h3>Total Constituencies</h3>
        <strong>{animatedTotal}</strong>
      </article>
      <article className="panel kpi-card">
        <h3>Data Reference</h3>
        <strong className="kpi-data-reference">{summary.dataReference}</strong>
      </article>
      <article className="panel kpi-card">
        <h3>Projected Winner</h3>
        <strong className="winner-roll-box" aria-live="polite">
          <span className="winner-roll-text" key={winnerRollToken}>
            {animatedWinner || "-"}
          </span>
        </strong>
      </article>
      <article className="panel kpi-card">
        <h3>Average Winning Score</h3>
        <strong>{asPercent(animatedScore)}</strong>
      </article>
    </section>
  );
}
