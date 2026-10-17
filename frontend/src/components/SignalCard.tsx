"use client";

import React from "react";
import { TradingSignalData } from "../types/market";
import { ShieldAlert, ShieldCheck, Target, ArrowDownCircle, ArrowUpCircle, CheckCircle2 } from "lucide-react";

interface SignalCardProps {
  signal: TradingSignalData;
}

export default function SignalCard({ signal }: SignalCardProps) {
  const isBuy = signal.signal === "BUY";
  const isSell = signal.signal === "SELL";

  return (
    <div className="glass-card" style={{ marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
            {isBuy ? <ArrowUpCircle size={20} color="#10b981" /> : isSell ? <ArrowDownCircle size={20} color="#ef4444" /> : null}
            Trading Signal Engine & Confluence Execution
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 2 }}>
            Decoupled multi-layer validation combining ML forecast, technical indicator scores, and risk filters.
          </p>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span
            className="badge"
            style={{
              fontSize: "0.95rem",
              padding: "6px 16px",
              background: isBuy ? "rgba(16,185,129,0.2)" : isSell ? "rgba(239,68,68,0.2)" : "rgba(245,158,11,0.2)",
              color: isBuy ? "var(--accent-green)" : isSell ? "var(--accent-red)" : "var(--accent-yellow)",
              border: `1px solid ${isBuy ? "var(--accent-green)" : isSell ? "var(--accent-red)" : "var(--accent-yellow)"}`,
            }}
          >
            ACTION: {signal.signal}
          </span>
        </div>
      </div>

      {/* Trade Parameters & Barriers Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, marginBottom: 16 }}>
        <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 16px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Suggested Entry</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-primary)", marginTop: 4 }}>
            ${signal.suggestedEntry.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>T+1 Candle Open with slippage</div>
        </div>

        <div style={{ background: "rgba(16,185,129,0.06)", padding: "12px 16px", borderRadius: 8, border: "1px solid rgba(16,185,129,0.2)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--accent-green)" }}>Take Profit (+1.0%)</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-green)", marginTop: 4 }}>
            ${signal.suggestedTakeProfit.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Fixed horizon barrier exit</div>
        </div>

        <div style={{ background: "rgba(239,68,68,0.06)", padding: "12px 16px", borderRadius: 8, border: "1px solid rgba(239,68,68,0.2)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--accent-red)" }}>Stop Loss (-0.5%)</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-red)", marginTop: 4 }}>
            ${signal.suggestedStopLoss.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Capital protection barrier</div>
        </div>

        <div style={{ background: "rgba(59,130,246,0.06)", padding: "12px 16px", borderRadius: 8, border: "1px solid rgba(59,130,246,0.2)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--accent-blue)" }}>Risk/Reward Ratio</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--accent-blue)", marginTop: 4 }}>
            {signal.riskRewardRatio.toFixed(1)} : 1
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Minimum required: 1.5:1</div>
        </div>

        <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 16px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Technical Score</div>
          <div style={{ fontSize: "1.2rem", fontWeight: 700, color: signal.technicalScore >= 60 ? "var(--accent-green)" : "var(--accent-yellow)", marginTop: 4 }}>
            {signal.technicalScore.toFixed(1)} / 100
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>RSI, EMAs, MACD & Patterns</div>
        </div>
      </div>

      {/* Confluence Rationale String */}
      <div style={{ padding: "12px 16px", background: "rgba(30,41,59,0.3)", borderRadius: 8, border: "1px solid var(--border-color)", display: "flex", gap: 10, alignItems: "flex-start" }}>
        <CheckCircle2 size={18} color="#10b981" style={{ flexShrink: 0, marginTop: 2 }} />
        <div style={{ fontSize: "0.9rem", color: "var(--text-primary)", lineHeight: 1.5 }}>
          <strong>Execution Confluence Rationale:</strong> {signal.reasoning}
        </div>
      </div>
    </div>
  );
}
