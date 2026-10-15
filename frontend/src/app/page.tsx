export default function DashboardPage() {
  return (
    <main>
      <header className="header">
        <div className="nav-brand">
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#10b981", boxShadow: "0 0 10px #10b981" }}></div>
          <span>AI Trading Prediction Engine</span>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <span className="badge badge-blue">BTC/USDT</span>
          <span className="badge badge-green">15M Timeframe</span>
          <span className="badge badge-blue">Model: XGBoost v1</span>
        </div>
      </header>

      <div className="container">
        {/* Metric Cards */}
        <div className="metric-grid">
          <div className="glass-card">
            <div className="metric-label">Target Asset</div>
            <div className="metric-value">BTC / USDT</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 4 }}>Binance Spot Market</div>
          </div>
          <div className="glass-card">
            <div className="metric-label">Prediction Horizon</div>
            <div className="metric-value">20 Candles (5h)</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 4 }}>Target: +1.0% | Stop: -0.5%</div>
          </div>
          <div className="glass-card">
            <div className="metric-label">Active Signal</div>
            <div className="metric-value" style={{ color: "var(--accent-yellow)" }}>NEUTRAL</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 4 }}>Confidence: 64.2%</div>
          </div>
          <div className="glass-card">
            <div className="metric-label">Pipeline Status</div>
            <div className="metric-value" style={{ color: "var(--accent-green)" }}>Ready</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 4 }}>PostgreSQL & Redis connected</div>
          </div>
        </div>

        {/* Prediction Probabilities Breakdown */}
        <div className="glass-card" style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>Probabilistic Forecast (Next 20 Candles)</h2>
            <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Updated at Candle Close</span>
          </div>

          <div className="prob-bar-container">
            <div className="prob-up" style={{ width: "35%" }} title="UP: 35%"></div>
            <div className="prob-neutral" style={{ width: "45%" }} title="NEUTRAL: 45%"></div>
            <div className="prob-down" style={{ width: "20%" }} title="DOWN: 20%"></div>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginTop: 8 }}>
            <span style={{ color: "var(--accent-green)" }}>● P(UP / +1.0% first): <strong>35.0%</strong></span>
            <span style={{ color: "var(--accent-yellow)" }}>● P(NEUTRAL / Timeout): <strong>45.0%</strong></span>
            <span style={{ color: "var(--accent-red)" }}>● P(DOWN / -0.5% first): <strong>20.0%</strong></span>
          </div>
        </div>

        {/* System Architecture & Status Details */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div className="glass-card">
            <h3 style={{ fontSize: "1rem", marginBottom: 12 }}>System Architecture</h3>
            <ul style={{ listStyle: "none", fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: "1.8" }}>
              <li>✓ <strong>Data Ingestion:</strong> Spring Boot 3.3 (Java 21)</li>
              <li>✓ <strong>Feature & ML Engine:</strong> Python (Pandas, XGBoost, Scikit-learn)</li>
              <li>✓ <strong>Storage:</strong> PostgreSQL Raw Immutable Candles</li>
              <li>✓ <strong>Dashboard:</strong> Next.js 14 App Router</li>
            </ul>
          </div>
          <div className="glass-card">
            <h3 style={{ fontSize: "1rem", marginBottom: 12 }}>Implementation Roadmap</h3>
            <ul style={{ listStyle: "none", fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: "1.8" }}>
              <li>✓ <strong>Phase 0:</strong> Project Definition (Completed)</li>
              <li>✓ <strong>Phase 1:</strong> Repo & Environment Scaffolding (In Progress)</li>
              <li>⏳ <strong>Phase 2:</strong> Market Data Provider Selection</li>
              <li>⏳ <strong>Phase 3:</strong> Raw Market Data Ingestion</li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  );
}
