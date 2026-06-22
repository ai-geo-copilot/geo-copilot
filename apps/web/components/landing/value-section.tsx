export function ValueSection() {
  return (
    <section className="section" id="value">
      <div className="container">
        <div className="section-header">
          <p className="section-label">Why GEO</p>
          <h2 className="section-title">为什么 GEO 优化在 AI 时代不可或缺</h2>
          <p className="section-subtitle" style={{ margin: "0.75rem auto 0" }}>
            生成式引擎不靠排名，靠证据——让你的内容成为 AI 答案的原材料
          </p>
        </div>
        <div className="grid-3">
          <div className="value-card">
            <div className="value-card__icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </div>
            <h3 className="value-card__title">从被索引到被引用</h3>
            <p className="body-sm">
              传统 SEO 关注排名位置。GEO 关注内容是否在 AI 答案中被吸收和引用——这是根本性的范式转变。
            </p>
          </div>
          <div className="value-card">
            <div className="value-card__icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <h3 className="value-card__title">证据即货币</h3>
            <p className="body-sm">
              AI 搜索引擎不信任没有来源的主张。可验证的数据、引用和结构化信息是内容被安全引用的前提。
            </p>
          </div>
          <div className="value-card">
            <div className="value-card__icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </div>
            <h3 className="value-card__title">双阶段诊断框架</h3>
            <p className="body-sm">
              Citation Selection（能否被发现）+ Citation Absorption（能否被引用），全面覆盖 GEO 就绪度的两大入口。
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
