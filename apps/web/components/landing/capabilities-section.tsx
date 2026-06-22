import { capabilities } from "../../mocks/landing-data";

export function CapabilitiesSection() {
  return (
    <section className="section section--alt" id="capabilities">
      <div className="container">
        <div className="section-header">
          <p className="section-label">Capabilities</p>
          <h2 className="section-title">六大诊断维度</h2>
          <p className="section-subtitle" style={{ margin: "0.75rem auto 0" }}>
            从爬虫可访达到答案就绪，全面评估页面 GEO 成熟度
          </p>
        </div>
        <div className="grid-3">
          {capabilities.map((c, i) => (
            <div className="capability-card" key={c.num}>
              <span className="capability-card__number">{c.num}</span>
              <h3 className="capability-card__title">{c.title}</h3>
              <p className="capability-card__desc body-sm">{c.desc}</p>
              <ul className="capability-card__list">
                {c.items.map((it, j) => (
                  <li key={j}>{it}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
