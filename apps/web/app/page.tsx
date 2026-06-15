const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  return (
    <main className="shell">
      <section className="panel">
        <p className="eyebrow">GEO Copilot</p>
        <h1>URL 分析控制台</h1>
        <form className="analysis-form">
          <label htmlFor="url">目标 URL</label>
          <div className="input-row">
            <input id="url" name="url" type="url" placeholder="https://example.com/product" />
            <button type="submit">创建分析</button>
          </div>
        </form>
        <dl className="status-grid">
          <div>
            <dt>API</dt>
            <dd>{apiBaseUrl}</dd>
          </div>
          <div>
            <dt>当前阶段</dt>
            <dd>Sprint 0 scaffold</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
