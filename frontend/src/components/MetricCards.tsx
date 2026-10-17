"use client";

import React from "react";
import { TrendingUp, TrendingDown, ShieldCheck, Zap, Activity } from "lucide-react";
import { PredictionData, TradingSignalData, RiskStatusData } from "../types/market";

interface MetricCardsProps {
  currentPrice: number;
  priceChangePct: number;
  symbol: string;
  prediction: PredictionData;
  signal: TradingSignalData;
  risk: RiskStatusData;
}

export default function MetricCards({
  currentPrice,
  priceChangePct,
  symbol,
  prediction,
  signal,
  risk,
}: MetricCardsProps) {
  const isUp = priceChangePct >= 0;

  return (
    <div className="metric-grid">
      {/* 1. Price Card */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div className="metric-label">{symbol} Price</div>
            <div className="metric-value">
              ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
          <span className={`badge ${isUp ? "badge-green" : "badge-red"}`}>
            {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {isUp ? `+${priceChangePct.toFixed(2)}%` : `${priceChangePct.toFixed(2)}%`}
          </span>
        </div>
        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 8 }}>
          Binance Spot • Closed-Candle Execution
        </div>
      </div>

      {/* 2. ML Prediction Card */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div className="metric-label">ML Calibrated Prediction</div>
            <div
              className="metric-value"
              style={{
                color:
                  prediction.prediction === "UP"
                    ? "var(--accent-green)"
                    : prediction.prediction === "DOWN"
                    ? "var(--accent-red)"
                    : "var(--accent-yellow)",
              }}
            >
              {prediction.prediction} ({(prediction.probabilityUp * 100).toFixed(1)}%)
            </div>
          </div>
          <span className="badge badge-blue">
            <Zap size={12} />
            {prediction.modelVersion.split("_")[2] || "RF"}
          </span>
        </div>
        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 8 }}>
          Horizon: 20 Candles (5h) • Target: +1.0% | Stop: -0.5%
        </div>
      </div>

      {/* 3. Confluence Signal Card */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div className="metric-label">Confluence Signal</div>
            <div
              className="metric-value"
              style={{
                color:
                  signal.signal === "BUY"
                    ? "var(--accent-green)"
                    : signal.signal === "SELL"
                    ? "var(--accent-red)"
                    : "var(--accent-yellow)",
              }}
            >
              {signal.signal}
            </div>
          </div>
          <span className="badge badge-green">
            Score: {signal.technicalScore.toFixed(0)}/100
          </span>
        </div>
        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 8 }}>
          R:R {signal.riskRewardRatio.toFixed(1)}:1 • Target ${signal.suggestedTakeProfit.toFixed(1)}
        </div>
      </div>

      {/* 4. Risk Guard Card */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div className="metric-label">Risk Management Guard</div>
            <div
              className="metric-value"
              style={{
                color: risk.isKillSwitchActive ? "var(--accent-red)" : "var(--accent-green)",
              }}
            >
              {risk.isKillSwitchActive ? "CIRCUIT BREAKER" : "ALL SYSTEMS GREEN"}
            </div>
          </div>
          <span className={`badge ${risk.isKillSwitchActive ? "badge-red" : "badge-green"}`}>
            <ShieldCheck size={12} />
            DD: {risk.currentDrawdownPct.toFixed(1)}%
          </span>
        </div>
        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 8 }}>
          Daily PnL: +${risk.dailyPnl.toFixed(0)} • Cooldown: {risk.cooldownRemainingCandles} bars
        </div>
      </div>
    </div>
  );
}
