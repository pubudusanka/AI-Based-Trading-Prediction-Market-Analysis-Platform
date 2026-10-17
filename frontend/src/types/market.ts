export interface Candle {
  open_time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema20?: number;
  ema50?: number;
  ema200?: number;
  bbUpper?: number;
  bbLower?: number;
  pattern?: string;
  signalMarker?: "BUY" | "SELL";
}

export interface PredictionData {
  symbol: string;
  timeframe: string;
  candleTime: string;
  modelVersion: string;
  prediction: "UP" | "DOWN" | "NEUTRAL";
  probabilityUp: number;
  probabilityDown: number;
  probabilityNeutral: number;
  topFactors: Array<{
    feature: string;
    impact: number;
    description: string;
  }>;
  disclaimer: string;
}

export interface TradingSignalData {
  symbol: string;
  timeframe: string;
  timestamp: string;
  signal: "BUY" | "SELL" | "HOLD" | "NO_SIGNAL";
  mlPrediction: string;
  probabilityUp: number;
  probabilityDown: number;
  technicalScore: number;
  riskAcceptable: boolean;
  suggestedEntry: number;
  suggestedTakeProfit: number;
  suggestedStopLoss: number;
  riskRewardRatio: number;
  reasoning: string;
}

export interface RiskStatusData {
  currentCapital: number;
  peakCapital: number;
  currentDrawdownPct: number;
  dailyPnl: number;
  openPositions: number;
  consecutiveLosses: number;
  cooldownRemainingCandles: number;
  isKillSwitchActive: boolean;
  maxDailyLossPct: number;
  maxDrawdownLimitPct: number;
}

export interface BacktestMetricsData {
  strategyVersion: string;
  modelVersion: string;
  symbol: string;
  timeframe: string;
  initialCapital: number;
  totalTrades: number;
  winRatePct: number;
  profitFactor: number;
  maxDrawdownPct: number;
  sharpeRatio: number;
  sortinoRatio: number;
  totalReturnPct: number;
  trades: Array<{
    tradeId: string;
    side: "BUY" | "SELL";
    entryTime: string;
    entryPrice: number;
    exitTime: string;
    exitPrice: number;
    exitReason: string;
    netPnl: number;
    outcome: "WIN" | "LOSS";
  }>;
}

export interface ModelInfoData {
  version: string;
  modelType: string;
  datasetVersion: string;
  status: string;
  rocAuc: number;
  brierScore: number;
  logLoss: number;
  ece: number;
  calibrationMethod: string;
  createdAt: string;
  sha256Hash: string;
}

export interface DataQualityData {
  symbol: string;
  timeframe: string;
  provider: string;
  latestCandleTime: string;
  totalCandles: number;
  coveragePct: number;
  missingGaps: number;
  duplicateCount: number;
  abnormalVolumeCount: number;
  isFresh: boolean;
  statusMessage: string;
}

export interface NotificationItem {
  id?: string;
  type?: "BUY_SIGNAL" | "SELL_SIGNAL" | "RISK_ALERT" | "DATA_QUALITY_ALERT" | "INFO";
  title: string;
  message: string;
  timestamp: string;
  symbol?: string;
  signal?: string;
  confidence?: number;
  read?: boolean;
}

export interface NotificationSettings {
  notificationsEnabled: boolean;
  soundEnabled: boolean;
  minConfidenceThreshold: number;
}

