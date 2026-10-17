"use client";

import React from "react";
import { ModelInfoData } from "../types/market";
import { Cpu, CheckCircle2, ShieldCheck, FileCode, Sliders } from "lucide-react";

interface ModelRegistryPanelProps {
  model: ModelInfoData;
}

export default function ModelRegistryPanel({ model }: ModelRegistryPanelProps) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
      {/* 1. Model Artifact Metadata */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
            <Cpu size={18} color="var(--accent-blue)" />
            Active Production Model (Phase 19)
          </h3>
          <span className="badge badge-green">PROMOTED TO PRODUCTION</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 12px", background: "rgba(15,23,42,0.6)", borderRadius: 8 }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Model Version Tag:</span>
            <span style={{ fontWeight: 700, color: "var(--text-primary)", fontFamily: "monospace" }}>{model.version}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 12px", background: "rgba(15,23,42,0.6)", borderRadius: 8 }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Algorithm Family:</span>
            <span style={{ fontWeight: 600, color: "var(--accent-cyan)" }}>{model.modelType}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 12px", background: "rgba(15,23,42,0.6)", borderRadius: 8 }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Dataset & Labeling:</span>
            <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{model.datasetVersion}</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", padding: "10px 12px", background: "rgba(15,23,42,0.6)", borderRadius: 8 }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Probability Calibrator:</span>
            <span style={{ fontWeight: 600, color: "var(--accent-green)" }}>{model.calibrationMethod}</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 4, padding: "10px 12px", background: "rgba(15,23,42,0.6)", borderRadius: 8 }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Artifact Integrity (SHA-256):</span>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "monospace", wordBreak: "break-all" }}>
              {model.sha256Hash}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Validation & Probability Calibration Metrics */}
      <div className="glass-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
            <Sliders size={18} color="var(--accent-cyan)" />
            Calibration & Discrimination Metrics (Phases 16–17)
          </h3>
          <span className="badge badge-blue">Walk-Forward Purged CV</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Out-of-Sample ROC-AUC</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--accent-green)", marginTop: 4 }}>
              {model.rocAuc.toFixed(3)}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Baseline Dummy: 0.500</div>
          </div>

          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Brier Score</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-primary)", marginTop: 4 }}>
              {model.brierScore.toFixed(3)}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Lower is better (Calibrated)</div>
          </div>

          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Log Loss</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-primary)", marginTop: 4 }}>
              {model.logLoss.toFixed(3)}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Strict penalty on overconfidence</div>
          </div>

          <div style={{ background: "rgba(15,23,42,0.6)", padding: "12px 14px", borderRadius: 8, border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>ECE (Calibration Error)</div>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--accent-green)", marginTop: 4 }}>
              {(model.ece * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>Target: &lt; 5.0% error</div>
          </div>
        </div>

        <div style={{ padding: "10px 14px", background: "rgba(16,185,129,0.08)", borderRadius: 8, border: "1px solid rgba(16,185,129,0.2)", fontSize: "0.85rem", color: "var(--text-primary)", display: "flex", gap: 8, alignItems: "center" }}>
          <CheckCircle2 size={16} color="#10b981" />
          <span>Single active production invariant strictly maintained in Model Registry.</span>
        </div>
      </div>
    </div>
  );
}
