export function CtaSection() {
  return (
    <>
      <section className="cta" id="cta">
        <h2 className="cta__title">准备好优化你的页面了吗？</h2>
        <p className="cta__sub">输入任意网址，获得结构化 GEO 优化报告</p>
        <a href="#hero" className="btn btn--primary" style={{ fontSize: "1rem", padding: "0.85rem 2rem" }}>
          开始诊断 &rarr;
        </a>
      </section>
      <footer className="footer-bottom">
        <p>GEO Copilot v0.1 — 基于页面证据的 AI 搜索优化诊断引擎</p>
        <p style={{ marginTop: "0.35rem", fontSize: "0.7rem" }}>GEO 方法基于前沿论文 · 诊断结果仅供优化参考</p>
      </footer>
    </>
  );
}
