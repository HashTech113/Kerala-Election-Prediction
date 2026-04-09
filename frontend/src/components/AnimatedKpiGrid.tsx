import { useEffect, useRef, useState } from "react";
import { asPercent } from "../utils/format";

interface AnimatedKpiGridProps {
  totalConstituencies: number;
  projectedWinner: string;
  averageConfidence: number;
}

let hasAnimatedKpiInSession = false;

export function AnimatedKpiGrid({
  totalConstituencies,
  projectedWinner,
  averageConfidence,
}: AnimatedKpiGridProps) {
  const kpiGridRef = useRef<HTMLElement | null>(null);
  const hasAnimatedRef = useRef(hasAnimatedKpiInSession);
  const [animatedConfidence, setAnimatedConfidence] = useState(
    hasAnimatedRef.current ? averageConfidence : 0,
  );
  const [animatedTotal, setAnimatedTotal] = useState(
    hasAnimatedRef.current ? totalConstituencies : 0,
  );
  const [animatedWinner, setAnimatedWinner] = useState(
    hasAnimatedRef.current ? projectedWinner : "",
  );

  useEffect(() => {
    if (!hasAnimatedRef.current) return;
    setAnimatedConfidence(averageConfidence);
    setAnimatedTotal(totalConstituencies);
    setAnimatedWinner(projectedWinner);
  }, [averageConfidence, totalConstituencies, projectedWinner]);

  useEffect(() => {
    const element = kpiGridRef.current;
    if (!element || hasAnimatedRef.current) return;

    let confidenceFrameId = 0;
    let totalFrameId = 0;
    let winnerIntervalId: number | undefined;

    const triggerAnimationOnce = () => {
      if (hasAnimatedRef.current) return;
      hasAnimatedRef.current = true;
      hasAnimatedKpiInSession = true;

      const confidenceDurationMs = 1200;
      const confidenceStart = performance.now();
      const confidenceTarget = averageConfidence;
      const confidenceTick = (now: number) => {
        const t = Math.min((now - confidenceStart) / confidenceDurationMs, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        setAnimatedConfidence(confidenceTarget * eased);
        if (t < 1) {
          confidenceFrameId = requestAnimationFrame(confidenceTick);
        }
      };
      confidenceFrameId = requestAnimationFrame(confidenceTick);

      const totalDurationMs = 900;
      const totalStart = performance.now();
      const totalTarget = totalConstituencies;
      const totalTick = (now: number) => {
        const t = Math.min((now - totalStart) / totalDurationMs, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        setAnimatedTotal(Math.round(totalTarget * eased));
        if (t < 1) {
          totalFrameId = requestAnimationFrame(totalTick);
        }
      };
      totalFrameId = requestAnimationFrame(totalTick);

      if (projectedWinner.length <= 1) {
        setAnimatedWinner(projectedWinner);
        return;
      }
      setAnimatedWinner("");
      let index = 0;
      winnerIntervalId = window.setInterval(() => {
        index += 1;
        setAnimatedWinner(projectedWinner.slice(0, index));
        if (index >= projectedWinner.length && winnerIntervalId) {
          window.clearInterval(winnerIntervalId);
        }
      }, 140);
    };

    if (typeof IntersectionObserver === "undefined") {
      triggerAnimationOnce();
      return () => {
        cancelAnimationFrame(confidenceFrameId);
        cancelAnimationFrame(totalFrameId);
        if (winnerIntervalId) {
          window.clearInterval(winnerIntervalId);
        }
      };
    }

    const observer = new IntersectionObserver((entries, observerInstance) => {
      const shouldAnimate = entries.some(
        (entry) => entry.isIntersecting && entry.intersectionRatio >= 0.35,
      );
      if (!shouldAnimate) return;
      triggerAnimationOnce();
      observerInstance.disconnect();
    }, { threshold: [0, 0.35] });

    observer.observe(element);
    const fallbackTimerId = window.setTimeout(triggerAnimationOnce, 300);

    return () => {
      window.clearTimeout(fallbackTimerId);
      observer.disconnect();
      cancelAnimationFrame(confidenceFrameId);
      cancelAnimationFrame(totalFrameId);
      if (winnerIntervalId) {
        window.clearInterval(winnerIntervalId);
      }
    };
  }, [averageConfidence, totalConstituencies, projectedWinner]);

  return (
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
  );
}
