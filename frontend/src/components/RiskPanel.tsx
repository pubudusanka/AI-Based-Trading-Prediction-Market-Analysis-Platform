"use client";

import React from "react";
import { RiskStatusData } from "../types/market";
import { ShieldCheck, ShieldAlert, AlertTriangle, Lock, RefreshCw } from "lucide-react";

interface RiskPanelProps {
  risk: RiskStatusData;
}

export default function RiskPanel({ risk }: RiskPanelProps) {
  const ddPct = risk.currentDrawdownPct;
  const maxDd = risk.maxDrawdownLimitPct;
  const isHealthy = !risk.isKillSwitchActive && risk.cooldownRemainingCandles === 0;

  return (
    <div className="glass-card" style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
            <ShieldCheck size={20} color={isHealthy ? "#10b981" : "#ef4444"} />
            Institutional Risk Management Safeguards (Phase 27)
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 2 }}>
            Dedicated capital preservation layer enforcing hard circuit breakers and dynamic sizing before execution.
          </p>
        </div>

        <span className={`badge ${isHealthy ? "badge-green" : "badge-red"}`}>
          {isHealthy ? "SAFEGUARDS ACTIVE" : "PROTECTION ENGAGED"}
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14, marginBottom: 20 }}>
        {/* Drawdown Gauge */}
        <div style={{ background: "rgba(15,23,42,0.6)", padding: "14px 16px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
            <span>Portfolio Drawdown</span>
            <span style={{ color: ddPct > 5.0 ? "var(--accent-red)" : "var(--accent-green)", fontWeight: "bold" }}>
              {ddPct.toFixed(2)}% / {maxDd.toFixed(0)}%
            </span>
          </div>
          <div style={{ width: "100%", height: 8, background: "rgba(255,255,255,0.08)", borderRadius: 4, marginTop: 8, overflow: "hidden" }}>
            <div
              style={{
                width: `${Math.min((ddPct / maxDd) * 100, 100)}%`,
                height: "100%",
                background: ddPct > 5 ? "var(--accent-red)" : "var(--accent-green)",
                borderRadius: 4,
              }}
            />
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 6 }}>
            Peak Capital: ${risk.peakCapital.toLocaleString()}
          </div>
        </div>

        {/* Daily Loss Circuit Breaker */}
        <div style={{ background: "rgba(15,23,42,0.6)", padding: "14px 16px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
          <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Daily Realized PnL</div>
          <div style={{ fontSize: "1.3rem", fontWeight: 700, color: risk.dailyPnl >= 0 ? "var(--accent-green)" : "var(--accent-red)", marginTop: 4 }}>
            {risk.dailyPnl >= 0 ? `+$${risk.dailyPnl.toFixed(2)}` : `-$${Math.abs(risk.dailyPnl).toFixed(2)}`}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
            Daily Circuit Breaker: Max 3.0% (-$300)
          </div>
        </div>

        {/* Cooldown Status */}
        <div style={{ background: "rgba(15,23,42,0.6)", padding: "14px 16px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
          <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Loss Cooldown Embargo</div>
          <div style={{ fontSize: "1.3rem", fontWeight: 700, color: risk.cooldownRemainingCandles === 0 ? "var(--accent-green)" : "var(--accent-yellow)", marginTop: 4 }}>
            {risk.cooldownRemainingCandles === 0 ? "INACTIVE (0 bars)" : `ACTIVE (${risk.cooldownRemainingCandles} bars left)`}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
            Consecutive Losses: {risk.consecutiveLosses} / 2
          </div>
        </div>

        {/* Open Position Cap */}
        <div style={{ background: "rgba(15,23,42,0.6)", padding: "14px 16px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
          <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Active Open Positions</div>
          <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-primary)", marginTop: 4 }}>
            {risk.openPositions} / 1 Position Max
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
            Max Sizing: 25% Portfolio Capital
          </div>
        </div>
      </div>
    </div>
  );
}
