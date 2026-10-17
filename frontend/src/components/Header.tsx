"use client";

import React, { useEffect, useState } from "react";
import { Activity, BarChart3, Cpu, Database, History, Zap, Radio, PauseCircle, PlayCircle } from "lucide-react";
import { NotificationCenter } from "./NotificationCenter";
import { NotificationItem } from "../types/market";
import { ConnectionStatus } from "../services/useMarketStream";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  symbol: string;
  setSymbol: (s: string) => void;
  timeframe: string;
  setTimeframe: (t: string) => void;
  livePrice?: number;
  connectionStatus?: ConnectionStatus;
  streamActive?: boolean;
  toggleStream?: () => void;
  notifications: NotificationItem[];
  onClearNotifications: () => void;
  onMarkNotificationRead: (id?: string) => void;
}

export default function Header({
  activeTab,
  setActiveTab,
  symbol,
  setSymbol,
  timeframe,
  setTimeframe,
  livePrice,
  connectionStatus = "CONNECTED",
  streamActive = true,
  toggleStream,
  notifications,
  onClearNotifications,
  onMarkNotificationRead,
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
              background: connectionStatus === "CONNECTED" ? "#10b981" : "#f59e0b",
              boxShadow: connectionStatus === "CONNECTED" ? "0 0 12px #10b981" : "0 0 12px #f59e0b",
            }}
          />
          <span style={{ fontWeight: 800, letterSpacing: "-0.02em" }}>
            AI Trade <span style={{ color: "var(--accent-blue)" }}>Predictor</span>
          </span>
        </div>

        {/* Live Status Badge & Stream Toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={toggleStream}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium transition"
            style={{
              background: streamActive ? "rgba(16, 185, 129, 0.12)" : "rgba(148, 163, 184, 0.12)",
              color: streamActive ? "#34d399" : "#94a3b8",
              border: streamActive ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(148, 163, 184, 0.2)",
            }}
            title={streamActive ? "Real-time updates active. Click to pause." : "Streaming paused. Click to resume."}
          >
            {streamActive ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>LIVE SSE</span>
                <PauseCircle size={12} className="ml-1 opacity-70" />
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-slate-500"></span>
                <span>PAUSED</span>
                <PlayCircle size={12} className="ml-1 opacity-70" />
              </>
            )}
          </button>

          {livePrice && (
            <span style={{ fontFamily: "monospace", fontSize: "0.85rem", fontWeight: 700, color: "#f8fafc" }}>
              ${livePrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          )}
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

      {/* Tabs, Notification Center & Clock */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
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

        {/* Notification Bell Center */}
        <NotificationCenter
          notifications={notifications}
          onClearAll={onClearNotifications}
          onMarkRead={onMarkNotificationRead}
        />

        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontFamily: "monospace" }}>
          {currentTime || "UTC Loading..."}
        </div>
      </div>
    </header>
  );
}
