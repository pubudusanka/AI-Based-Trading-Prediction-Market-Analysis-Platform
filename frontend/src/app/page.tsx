"use client";

import React, { useState, useEffect } from "react";
import Header from "../components/Header";
import MetricCards from "../components/MetricCards";
import CandleChart from "../components/CandleChart";
import SignalCard from "../components/SignalCard";
import PredictionPanel from "../components/PredictionPanel";
import RiskPanel from "../components/RiskPanel";
import BacktestPanel from "../components/BacktestPanel";
import ModelRegistryPanel from "../components/ModelRegistryPanel";
import DataQualityPanel from "../components/DataQualityPanel";

import {
  fetchCandles,
  fetchLatestPrediction,
  fetchLatestSignal,
  getRiskStatus,
  fetchBacktestMetrics,
  getModelInfo,
  fetchDataQuality,
} from "../services/api";

import {
  Candle,
  PredictionData,
  TradingSignalData,
  RiskStatusData,
  BacktestMetricsData,
  ModelInfoData,
  DataQualityData,
} from "../types/market";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [symbol, setSymbol] = useState("BTC/USDT");
  const [timeframe, setTimeframe] = useState("15m");

  const [candles, setCandles] = useState<Candle[]>([]);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [signal, setSignal] = useState<TradingSignalData | null>(null);
  const [risk, setRisk] = useState<RiskStatusData | null>(null);
  const [backtest, setBacktest] = useState<BacktestMetricsData | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoData | null>(null);
  const [quality, setQuality] = useState<DataQualityData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      const [cList, pred, sig, bt, q] = await Promise.all([
        fetchCandles(symbol, timeframe, 60),
        fetchLatestPrediction(symbol, timeframe),
        fetchLatestSignal(symbol, timeframe),
        fetchBacktestMetrics(symbol),
        fetchDataQuality(symbol, timeframe),
      ]);

      if (isMounted) {
        setCandles(cList);
        setPrediction(pred);
        setSignal(sig);
        setRisk(getRiskStatus());
        setBacktest(bt);
        setModelInfo(getModelInfo());
        setQuality(q);
        setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [symbol, timeframe]);

  const currentPrice = candles.length > 0 ? candles[candles.length - 1].close : 67320.0;
  const firstPrice = candles.length > 0 ? candles[0].open : 66500.0;
  const priceChangePct = ((currentPrice - firstPrice) / firstPrice) * 100.0;

  if (loading || !prediction || !signal || !risk || !backtest || !modelInfo || !quality) {
    return (
      <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              width: 36,
              height: 36,
              border: "3px solid rgba(59, 130, 246, 0.2)",
              borderTopColor: "var(--accent-blue)",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: "0 auto 16px",
            }}
          />
          <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>Loading Market Engine & Model State...</div>
        </div>
      </main>
    );
  }

  return (
    <main>
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        symbol={symbol}
        setSymbol={setSymbol}
        timeframe={timeframe}
        setTimeframe={setTimeframe}
      />

      <div className="container">
        {/* Metric Cards Top Summary */}
        <MetricCards
          currentPrice={currentPrice}
          priceChangePct={priceChangePct}
          symbol={symbol}
          prediction={prediction}
          signal={signal}
          risk={risk}
        />

        {/* Tab 1: Dashboard Overview (Full Terminal View) */}
        {activeTab === "dashboard" && (
          <>
            <SignalCard signal={signal} />
            <CandleChart candles={candles} symbol={symbol} timeframe={timeframe} />
            <div style={{ marginBottom: 24 }}>
              <PredictionPanel prediction={prediction} />
            </div>
            <RiskPanel risk={risk} />
          </>
        )}

        {/* Tab 2: Interactive Chart */}
        {activeTab === "chart" && (
          <>
            <CandleChart candles={candles} symbol={symbol} timeframe={timeframe} />
            <SignalCard signal={signal} />
          </>
        )}

        {/* Tab 3: Probabilities & Explainability */}
        {activeTab === "prediction" && (
          <PredictionPanel prediction={prediction} />
        )}

        {/* Tab 4: Backtesting & DSR Evaluation */}
        {activeTab === "backtest" && (
          <BacktestPanel metrics={backtest} />
        )}

        {/* Tab 5: Model Registry */}
        {activeTab === "models" && (
          <ModelRegistryPanel model={modelInfo} />
        )}

        {/* Tab 6: Data Quality & Ingestion Pipeline */}
        {activeTab === "quality" && (
          <DataQualityPanel quality={quality} />
        )}
      </div>
    </main>
  );
}
