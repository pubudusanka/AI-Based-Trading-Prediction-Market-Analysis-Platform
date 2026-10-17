"use client";

import React, { useEffect, useState } from "react";
import { Activity, BarChart3, Cpu, Database, History, ShieldCheck, Zap } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  symbol: string;
  setSymbol: (s: string) => void;
  timeframe: string;
  setTimeframe: (t: string) => void;
}

export default function Header({
  activeTab,
  setActiveTab,
  symbol,
  setSymbol,
  timeframe,
  setTimeframe,
}: HeaderProps) {
  const [currentTime, setCurrentTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: Activity },
    { id: "chart", label: "Interactive Chart", icon: BarChart3 },
    { id: "prediction", label: "Probabilities & Factors", icon: Zap },
    { id: "backtest", label: "Backtest & DSR", icon: History },
    { id: "models", label: "Model Registry", icon: Cpu },
    { id: "quality", label: "Data Quality & Pipeline", icon: Database },
  ];

  return (
    <header className="header" style={{ marginBottom: 20 }}>
      {/* Brand & Market Selectors */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
        <div className="nav-brand">
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: "#10b981",
              boxShadow: "0 0 12px #10b981",
            }}
          />
          <span style={{ fontWeight: 800, letterSpacing: "-0.02em" }}>
            AI Trade <span style={{ color: "var(--accent-blue)" }}>Predictor</span>
          </span>
        </div>

        {/* Symbol Selector */}
        <div style={{ display: "flex", gap: 6, background: "rgba(15,23,42,0.6)", padding: "4px 6px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
          {["BTC/USDT", "ETH/USDT", "SOL/USDT"].map((s) => (
            <button
              key={s}
              onClick={() => setSymbol(s)}
              className={`selector-pill ${symbol === s ? "active" : ""}`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Timeframe Selector */}
        <div style={{ display: "flex", gap: 6, background: "rgba(15,23,42,0.6)", padding: "4px 6px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
          {["15m", "1h", "4h", "1d"].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`selector-pill ${timeframe === tf ? "active" : ""}`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs & Clock */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
        <nav style={{ display: "flex", gap: 4 }}>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-tab ${isActive ? "active" : ""}`}
              >
                <Icon size={15} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
          {currentTime || "UTC Loading..."}
        </div>
      </div>
    </header>
  );
}
