"use client";

import React, { useState, useMemo } from "react";
import { Candle } from "../types/market";
import { Sliders, Eye, EyeOff, Layers } from "lucide-react";

interface CandleChartProps {
  candles: Candle[];
  symbol: string;
  timeframe: string;
}

export default function CandleChart({ candles, symbol, timeframe }: CandleChartProps) {
  const [showEma20, setShowEma20] = useState(true);
  const [showEma50, setShowEma50] = useState(true);
  const [showEma200, setShowEma200] = useState(true);
  const [showBollinger, setShowBollinger] = useState(true);
  const [showFibonacci, setShowFibonacci] = useState(true);
  const [showPatterns, setShowPatterns] = useState(true);
  const [showSignals, setShowSignals] = useState(true);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const width = 1100;
  const height = 480;
  const padding = { top: 30, right: 70, bottom: 50, left: 20 };
  const chartHeight = height - padding.top - padding.bottom;
  const chartWidth = width - padding.left - padding.right;

  const { minPrice, maxPrice, fibLevels } = useMemo(() => {
    if (!candles || candles.length === 0) {
      return { minPrice: 0, maxPrice: 1, fibLevels: [] };
    }
    const highs = candles.map((c) => c.high);
    const lows = candles.map((c) => c.low);
    const min = Math.min(...lows);
    const max = Math.max(...highs);
    const pad = (max - min) * 0.08;
    const effMin = min - pad;
    const effMax = max + pad;
    const diff = max - min;

    const fibs = [
      { label: "1.000", price: max, color: "#94a3b8" },
      { label: "0.786", price: min + diff * 0.786, color: "#cbd5e1" },
      { label: "0.618 (Golden)", price: min + diff * 0.618, color: "#f59e0b" },
      { label: "0.500", price: min + diff * 0.5, color: "#38bdf8" },
      { label: "0.382", price: min + diff * 0.382, color: "#cbd5e1" },
      { label: "0.236", price: min + diff * 0.236, color: "#94a3b8" },
      { label: "0.000", price: min, color: "#94a3b8" },
    ];

    return { minPrice: effMin, maxPrice: effMax, fibLevels: fibs };
  }, [candles]);

  const priceToY = (price: number) => {
    if (maxPrice === minPrice) return chartHeight / 2 + padding.top;
    return padding.top + chartHeight - ((price - minPrice) / (maxPrice - minPrice)) * chartHeight;
  };

  const candleWidth = chartWidth / Math.max(candles.length, 1);
  const barWidth = Math.max(candleWidth * 0.7, 4);

  const hoveredCandle = hoveredIndex !== null ? candles[hoveredIndex] : candles[candles.length - 1];

  // Helper for generating polyline points
  const getPolylinePoints = (getValue: (c: Candle) => number | undefined) => {
    return candles
      .map((c, i) => {
        const val = getValue(c);
        if (val === undefined) return null;
        const x = padding.left + i * candleWidth + candleWidth / 2;
        const y = priceToY(val);
        return `${x},${y}`;
      })
      .filter(Boolean)
      .join(" ");
  };

  return (
    <div className="glass-card" style={{ marginBottom: 24, position: "relative" }}>
      {/* Top Header & Overlay Controls */}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h2 style={{ fontSize: "1.2rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ color: "var(--accent-blue)" }}>{symbol}</span>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontWeight: 500 }}>• {timeframe}</span>
          </h2>
          {hoveredCandle && (
            <div style={{ display: "flex", gap: 12, fontSize: "0.8rem", fontFamily: "var(--font-mono, monospace)" }}>
              <span>O: <strong style={{ color: "var(--text-primary)" }}>{hoveredCandle.open.toFixed(2)}</strong></span>
              <span>H: <strong style={{ color: "var(--accent-green)" }}>{hoveredCandle.high.toFixed(2)}</strong></span>
              <span>L: <strong style={{ color: "var(--accent-red)" }}>{hoveredCandle.low.toFixed(2)}</strong></span>
              <span>C: <strong style={{ color: hoveredCandle.close >= hoveredCandle.open ? "var(--accent-green)" : "var(--accent-red)" }}>{hoveredCandle.close.toFixed(2)}</strong></span>
              <span>Vol: <strong style={{ color: "var(--text-secondary)" }}>{hoveredCandle.volume.toFixed(1)}</strong></span>
            </div>
          )}
        </div>

        {/* Overlay Toggle Buttons */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
          <button
            onClick={() => setShowEma20(!showEma20)}
            className={`pill-btn ${showEma20 ? "active-cyan" : ""}`}
            title="Exponential Moving Average 20"
          >
            EMA 20
          </button>
          <button
            onClick={() => setShowEma50(!showEma50)}
            className={`pill-btn ${showEma50 ? "active-blue" : ""}`}
            title="Exponential Moving Average 50"
          >
            EMA 50
          </button>
          <button
            onClick={() => setShowEma200(!showEma200)}
            className={`pill-btn ${showEma200 ? "active-purple" : ""}`}
            title="Exponential Moving Average 200"
          >
            EMA 200
          </button>
          <button
            onClick={() => setShowBollinger(!showBollinger)}
            className={`pill-btn ${showBollinger ? "active-indigo" : ""}`}
            title="Bollinger Bands (20, 2)"
          >
            BB (20,2)
          </button>
          <button
            onClick={() => setShowFibonacci(!showFibonacci)}
            className={`pill-btn ${showFibonacci ? "active-yellow" : ""}`}
            title="Fibonacci Retracement Grid"
          >
            Fibonacci
          </button>
          <button
            onClick={() => setShowPatterns(!showPatterns)}
            className={`pill-btn ${showPatterns ? "active-green" : ""}`}
            title="Candlestick Patterns"
          >
            Patterns
          </button>
          <button
            onClick={() => setShowSignals(!showSignals)}
            className={`pill-btn ${showSignals ? "active-emerald" : ""}`}
            title="Trading Signals & Execution Markers"
          >
            Signals
          </button>
        </div>
      </div>

      {/* SVG Chart Container */}
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: "100%", height: "auto", minWidth: 700, display: "block" }}
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <defs>
            <linearGradient id="bbAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.02" />
            </linearGradient>
            <linearGradient id="volGradUp" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.05" />
            </linearGradient>
            <linearGradient id="volGradDown" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.05" />
            </linearGradient>
          </defs>

          {/* Background Grid Lines */}
          {[0.2, 0.4, 0.6, 0.8].map((ratio) => {
            const y = padding.top + chartHeight * ratio;
            const price = maxPrice - (maxPrice - minPrice) * ratio;
            return (
              <g key={ratio}>
                <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
                <text x={width - padding.right + 8} y={y + 4} fill="#64748b" fontSize="11" fontFamily="monospace">
                  {price.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Fibonacci Grid Lines */}
          {showFibonacci &&
            fibLevels.map((fib, idx) => {
              const y = priceToY(fib.price);
              return (
                <g key={idx}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    stroke={fib.color}
                    strokeWidth={idx === 2 ? 1.4 : 0.8}
                    strokeDasharray={idx === 2 ? "none" : "3 3"}
                    opacity={idx === 2 ? 0.85 : 0.4}
                  />
                  <text
                    x={padding.left + 8}
                    y={y - 4}
                    fill={fib.color}
                    fontSize="10"
                    fontFamily="monospace"
                    opacity={idx === 2 ? 0.95 : 0.6}
                    fontWeight={idx === 2 ? "bold" : "normal"}
                  >
                    Fib {fib.label}: {fib.price.toFixed(1)}
                  </text>
                </g>
              );
            })}

          {/* Volume bars (bottom 20% of chart) */}
          {candles.map((c, i) => {
            const x = padding.left + i * candleWidth + (candleWidth - barWidth) / 2;
            const maxVol = Math.max(...candles.map((cd) => cd.volume), 1);
            const vHeight = (c.volume / maxVol) * 70;
            const y = padding.top + chartHeight - vHeight;
            const isGreen = c.close >= c.open;
            return (
              <rect
                key={`vol-${i}`}
                x={x}
                y={y}
                width={barWidth}
                height={vHeight}
                fill={isGreen ? "url(#volGradUp)" : "url(#volGradDown)"}
              />
            );
          })}

          {/* Bollinger Bands Overlay */}
          {showBollinger && (
            <>
              <polyline points={getPolylinePoints((c) => c.bbUpper)} fill="none" stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />
              <polyline points={getPolylinePoints((c) => c.bbLower)} fill="none" stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 2" opacity="0.6" />
            </>
          )}

          {/* Moving Averages */}
          {showEma200 && (
            <polyline points={getPolylinePoints((c) => c.ema200)} fill="none" stroke="#c084fc" strokeWidth="1.8" opacity="0.85" />
          )}
          {showEma50 && (
            <polyline points={getPolylinePoints((c) => c.ema50)} fill="none" stroke="#3b82f6" strokeWidth="1.5" opacity="0.9" />
          )}
          {showEma20 && (
            <polyline points={getPolylinePoints((c) => c.ema20)} fill="none" stroke="#06b6d4" strokeWidth="1.6" opacity="0.95" />
          )}

          {/* Candlesticks & Interactive Hitboxes */}
          {candles.map((c, i) => {
            const centerX = padding.left + i * candleWidth + candleWidth / 2;
            const rectX = padding.left + i * candleWidth + (candleWidth - barWidth) / 2;
            const yOpen = priceToY(c.open);
            const yClose = priceToY(c.close);
            const yHigh = priceToY(c.high);
            const yLow = priceToY(c.low);

            const isBullish = c.close >= c.open;
            const candleColor = isBullish ? "#10b981" : "#ef4444";
            const topBody = Math.min(yOpen, yClose);
            const bodyHeight = Math.max(Math.abs(yClose - yOpen), 2);

            return (
              <g key={i}>
                {/* Wick */}
                <line x1={centerX} y1={yHigh} x2={centerX} y2={yLow} stroke={candleColor} strokeWidth="1.2" />

                {/* Candle Body */}
                <rect
                  x={rectX}
                  y={topBody}
                  width={barWidth}
                  height={bodyHeight}
                  fill={candleColor}
                  rx="1"
                  style={{
                    filter: isBullish ? "drop-shadow(0 0 2px rgba(16,185,129,0.3))" : "drop-shadow(0 0 2px rgba(239,68,68,0.3))",
                  }}
                />

                {/* Pattern Badges */}
                {showPatterns && c.pattern && (
                  <g>
                    <rect
                      x={centerX - 35}
                      y={yHigh - 22}
                      width="70"
                      height="16"
                      rx="8"
                      fill="rgba(15, 23, 42, 0.9)"
                      stroke="#f59e0b"
                      strokeWidth="1"
                    />
                    <text x={centerX} y={yHigh - 11} fill="#fbbf24" fontSize="9" fontWeight="700" textAnchor="middle">
                      {c.pattern}
                    </text>
                  </g>
                )}

                {/* Trading Signal Execution Markers */}
                {showSignals && c.signalMarker && (
                  <g>
                    {c.signalMarker === "BUY" ? (
                      <g>
                        <circle cx={centerX} cy={yLow + 16} r="10" fill="#10b981" />
                        <path d={`M ${centerX - 5} ${yLow + 19} L ${centerX} ${yLow + 11} L ${centerX + 5} ${yLow + 19} Z`} fill="#ffffff" />
                        <text x={centerX} y={yLow + 36} fill="#10b981" fontSize="10" fontWeight="bold" textAnchor="middle">
                          BUY +1%
                        </text>
                      </g>
                    ) : (
                      <g>
                        <circle cx={centerX} cy={yHigh - 16} r="10" fill="#ef4444" />
                        <path d={`M ${centerX - 5} ${yHigh - 19} L ${centerX} ${yHigh - 11} L ${centerX + 5} ${yHigh - 19} Z`} fill="#ffffff" />
                        <text x={centerX} y={yHigh - 30} fill="#ef4444" fontSize="10" fontWeight="bold" textAnchor="middle">
                          EXIT
                        </text>
                      </g>
                    )}
                  </g>
                )}

                {/* Invisible Hover Rect */}
                <rect
                  x={padding.left + i * candleWidth}
                  y={padding.top}
                  width={candleWidth}
                  height={chartHeight}
                  fill="transparent"
                  style={{ cursor: "crosshair" }}
                  onMouseEnter={() => setHoveredIndex(i)}
                />
              </g>
            );
          })}

          {/* Crosshair when hovered */}
          {hoveredIndex !== null && (
            <g>
              <line
                x1={padding.left + hoveredIndex * candleWidth + candleWidth / 2}
                y1={padding.top}
                x2={padding.left + hoveredIndex * candleWidth + candleWidth / 2}
                y2={padding.top + chartHeight}
                stroke="rgba(255,255,255,0.3)"
                strokeDasharray="3 3"
              />
              <line
                x1={padding.left}
                y1={priceToY(candles[hoveredIndex].close)}
                x2={width - padding.right}
                y2={priceToY(candles[hoveredIndex].close)}
                stroke="rgba(255,255,255,0.3)"
                strokeDasharray="3 3"
              />
              {/* Price badge on axis */}
              <rect
                x={width - padding.right + 2}
                y={priceToY(candles[hoveredIndex].close) - 10}
                width="62"
                height="20"
                fill="#1e293b"
                stroke="#38bdf8"
                rx="4"
              />
              <text
                x={width - padding.right + 33}
                y={priceToY(candles[hoveredIndex].close) + 4}
                fill="#ffffff"
                fontSize="10"
                fontFamily="monospace"
                fontWeight="bold"
                textAnchor="middle"
              >
                {candles[hoveredIndex].close.toFixed(1)}
              </text>
            </g>
          )}

          {/* Time axis labels */}
          {candles.filter((_, idx) => idx % Math.ceil(candles.length / 6) === 0).map((c, idx) => {
            const candleIdx = candles.indexOf(c);
            const x = padding.left + candleIdx * candleWidth + candleWidth / 2;
            const timeLabel = new Date(c.open_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            return (
              <text key={idx} x={x} y={height - 15} fill="#64748b" fontSize="10" textAnchor="middle" fontFamily="monospace">
                {timeLabel}
              </text>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
