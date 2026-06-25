"use client";

import { useEffect, useRef, useState } from "react";
import { stats } from "../../mocks/landing-data";

export function StatsSection() {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section className="section section--alt" id="stats">
      <div className="container">
        <div className="section-header">
          <p className="section-label">By the Numbers</p>
          <h2 className="section-title">诊断能力概览</h2>
        </div>
        <div className="grid-4" ref={ref}>
          {stats.map((s, i) => (
            <div className="stat" key={i}>
              <span className="stat__number">
                <CountUp target={s.number} start={visible} />
              </span>
              <span className="stat__label">{s.label}</span>
            </div>
          ))}
        </div>
        <p className="body-sm text-center" style={{ marginTop: "2rem", color: "var(--text-tertiary)", maxWidth: "500px", marginLeft: "auto", marginRight: "auto" }}>
          每个诊断覆盖 6 个核心维度，调用 25+ 条 GEO 优化策略，单次分析即可产出问题清单、优先动作和可直接使用的资产草案
        </p>
      </div>
    </section>
  );
}

function CountUp({ target, start }: { target: number; start: boolean }) {
  const [count, setCount] = useState(0);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    if (!start) return;
    const duration = 1500;
    const startTime = performance.now();
    function step(now: number) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(eased * target));
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step);
      } else {
        setCount(target);
      }
    }
    frameRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameRef.current);
  }, [start, target]);

  return <>{count}</>;
}
