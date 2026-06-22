import { insights } from "../../mocks/landing-data";

export function InsightsSection() {
  return (
    <section className="section section--alt" id="insights">
      <div className="container">
        <div className="section-header">
          <p className="section-label">Knowledge Base</p>
          <h2 className="section-title">GEO 方法知识库</h2>
          <p className="section-subtitle" style={{ margin: "0.75rem auto 0" }}>
            基于前沿论文和开源项目，持续更新优化策略
          </p>
        </div>
        <div className="grid-3">
          {insights.map((ins, i) => (
            <div className="insight-card" key={i}>
              <span className={`insight-card__badge insight-card__badge--${ins.trust}`}>
                信任等级: {ins.trust === "high" ? "高" : "中"}
              </span>
              <h3 className="insight-card__title">{ins.title}</h3>
              <p className="insight-card__excerpt">{ins.excerpt}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
