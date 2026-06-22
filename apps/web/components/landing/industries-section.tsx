import { industries } from "../../mocks/landing-data";

export function IndustriesSection() {
  return (
    <section className="section" id="industries">
      <div className="container">
        <div className="section-header">
          <p className="section-label">Page Types</p>
          <h2 className="section-title">适用页面类型</h2>
          <p className="section-subtitle" style={{ margin: "0.75rem auto 0" }}>
            适用于多种业务场景，从产品定价页到技术文档
          </p>
        </div>
        <div className="industry-scroll">
          {industries.map((ind, i) => (
            <div className="industry-card" key={i}>
              <div className="industry-card__icon">{ind.icon}</div>
              <h3 className="industry-card__title">{ind.title}</h3>
              <p className="caption" style={{ marginTop: "0.35rem" }}>{ind.desc}</p>
            </div>
          ))}
        </div>
        <p className="caption text-center" style={{ marginTop: "1.5rem" }}>
          自动检测页面类型，匹配最优 GEO 策略
        </p>
      </div>
    </section>
  );
}
