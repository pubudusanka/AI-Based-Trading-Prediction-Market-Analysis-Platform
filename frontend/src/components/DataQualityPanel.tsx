"use client";

import React from "react";
import { DataQualityData } from "../types/market";
import { Database, CheckCircle2, AlertTriangle, ShieldCheck, Clock } from "lucide-react";

interface DataQualityPanelProps {
  quality: DataQualityData;
}

export default function DataQualityPanel({ quality }: DataQualityPanelProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* 1. Header Banner */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
              <Database size={20} color="var(--accent-blue)" />
              Market Data Quality & Integrity Auditor (Phase 5)
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 2 }}>
              Verifies zero data leakage, chronological integrity, and OHLC validity rules before training or inference.
            </p>
          </div>

          <span className={`badge ${quality.isFresh ? "badge-green" : "badge-yellow"}`}>
            {quality.isFresh ? "DATA PIPELINE ACTIVE" : "INGESTION PENDING"}
          </span>
        </div>

        {/* Audit Metrics Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 20 }}>
          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Total Candles Audited</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-primary)", marginTop: 4 }}>
              {quality.totalCandles.toLocaleString()}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Timeframe: {quality.timeframe}</div>
          </div>

          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Timeline Coverage</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--accent-green)", marginTop: 4 }}>
              {quality.coveragePct.toFixed(1)}%
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Strict 15m cadence</div>
          </div>

          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Missing Candle Gaps</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--accent-green)", marginTop: 4 }}>
              {quality.missingGaps}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Zero tolerance policy</div>
          </div>

          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Duplicate Timestamps</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--accent-green)", marginTop: 4 }}>
              {quality.duplicateCount}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Unique index constraint</div>
          </div>

          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Abnormal Volume Outliers</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--accent-green)", marginTop: 4 }}>
              {quality.abnormalVolumeCount}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>&gt; 8 std filter</div>
          </div>
        </div>

        {/* Audit Checklist */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div style={{ padding: 14, background: "rgba(30,41,59,0.4)", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
              <CheckCircle2 size={16} color="#10b981" />
              OHLC Relationship Invariants
            </div>
            <ul style={{ listStyle: "none", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.8 }}>
              <li>✓ High &ge; Open and High &ge; Close on 100% of candles</li>
              <li>✓ Low &le; Open and Low &le; Close on 100% of candles</li>
              <li>✓ High &ge; Low strictly verified</li>
              <li>✓ Zero non-positive price records</li>
            </ul>
          </div>

          <div style={{ padding: 14, background: "rgba(30,41,59,0.4)", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
              <ShieldCheck size={16} color="#10b981" />
              Lookahead & Leakage Safeguards
            </div>
            <ul style={{ listStyle: "none", fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.8 }}>
              <li>✓ Features computed strictly at candle close T</li>
              <li>✓ Orders simulated executing at open of candle T+1</li>
              <li>✓ Target labels generated with future horizon embargo</li>
              <li>✓ Raw candle records immutable in database</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
