"use client";

import React from "react";
import { PredictionData } from "../types/market";
import { Zap, Info, Sliders, CheckCircle2 } from "lucide-react";

interface PredictionPanelProps {
  prediction: PredictionData;
}

export default function PredictionPanel({ prediction }: PredictionPanelProps) {
  const pUp = Math.round(prediction.probabilityUp * 100);
  const pDown = Math.round(prediction.probabilityDown * 100);
  const pNeutral = Math.max(0, 100 - pUp - pDown);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
      {/* 1. Probability Distribution Card */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
            <Zap size={18} style={{ color: "var(--accent-blue)" }} />
            Calibrated Probability Distribution
          </h3>
          <span className="badge badge-green">Isotonic Calibrated</span>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: 16, lineHeight: 1.5 }}>
          Probabilities represent the chance of hitting the <strong>+1.0% take profit</strong> or <strong>-0.5% stop loss</strong> within the next <strong>20 candles (5 hours)</strong>.
        </p>

        {/* Multi-segment Probability Bar */}
        <div className="prob-bar-container" style={{ height: 28, marginBottom: 16 }}>
          <div
            className="prob-up"
            style={{ width: `${pUp}%`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem", fontWeight: "bold" }}
          >
            {pUp > 12 ? `UP ${pUp}%` : ""}
          </div>
          <div
            className="prob-neutral"
            style={{ width: `${pNeutral}%`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem", fontWeight: "bold" }}
          >
            {pNeutral > 12 ? `TIMEOUT ${pNeutral}%` : ""}
          </div>
          <div
            className="prob-down"
            style={{ width: `${pDown}%`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem", fontWeight: "bold" }}
          >
            {pDown > 12 ? `DOWN ${pDown}%` : ""}
          </div>
        </div>

        {/* Detailed Probabilities breakdown */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "rgba(16, 185, 129, 0.08)", borderRadius: 8, border: "1px solid rgba(16, 185, 129, 0.2)" }}>
            <span style={{ color: "var(--accent-green)", fontWeight: 600 }}>● P(UP) — Reaches +1.0% first</span>
            <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-green)" }}>{pUp}.0%</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "rgba(245, 158, 11, 0.08)", borderRadius: 8, border: "1px solid rgba(245, 158, 11, 0.2)" }}>
            <span style={{ color: "var(--accent-yellow)", fontWeight: 600 }}>● P(NEUTRAL) — Times out at 20 candles</span>
            <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-yellow)" }}>{pNeutral}.0%</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "rgba(239, 68, 68, 0.08)", borderRadius: 8, border: "1px solid rgba(239, 68, 68, 0.2)" }}>
            <span style={{ color: "var(--accent-red)", fontWeight: 600 }}>● P(DOWN) — Reaches -0.5% first</span>
            <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-red)" }}>{pDown}.0%</span>
          </div>
        </div>

        <div style={{ marginTop: 16, padding: "10px 14px", background: "rgba(15, 23, 42, 0.5)", borderRadius: 8, fontSize: "0.8rem", color: "var(--text-muted)" }}>
          <Info size={14} style={{ display: "inline", verticalAlign: "middle", marginRight: 6 }} />
          {prediction.disclaimer}
        </div>
      </div>

      {/* 2. Top Factors / Explainability (SHAP) Card */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
            <Sliders size={18} style={{ color: "var(--accent-cyan)" }} />
            Feature Explainability & SHAP Drivers
          </h3>
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Top 5 Drivers</span>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: 16 }}>
          Local feature contribution breakdown identifying why the model assigned a {pUp}% bullish probability:
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {prediction.topFactors.map((factor, idx) => {
            const isPositive = factor.impact >= 0;
            const pct = Math.abs(factor.impact * 100).toFixed(1);
            return (
              <div key={idx} style={{ background: "rgba(30, 41, 59, 0.4)", padding: 12, borderRadius: 8, border: "1px solid var(--border-color)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, fontSize: "0.9rem", color: "var(--text-primary)" }}>
                    {factor.feature}
                  </span>
                  <span style={{ fontWeight: 700, fontSize: "0.85rem", color: isPositive ? "var(--accent-green)" : "var(--accent-red)" }}>
                    {isPositive ? `+${pct}%` : `-${pct}%`} impact
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  {factor.description}
                </div>
                {/* Visual mini-bar */}
                <div style={{ width: "100%", height: 4, background: "rgba(255,255,255,0.06)", borderRadius: 2, marginTop: 8, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${Math.min(Math.abs(factor.impact) * 400, 100)}%`,
                      height: "100%",
                      background: isPositive ? "var(--accent-green)" : "var(--accent-red)",
                      borderRadius: 2,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
