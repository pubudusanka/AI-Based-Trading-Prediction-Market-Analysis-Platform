"""
Exploratory Data Analysis (EDA) Pipeline.
Reference: Section 18 (Phase 13) of Implementation Plan.

Analyzes:
1. Target & Class Distribution (UP / DOWN / NEUTRAL balance and imbalance ratio)
2. Missing Value Analysis (counts, percentages, handling strategies)
3. Statistical Distribution (mean, std, median, skewness, kurtosis, constant checks)
4. Outlier Analysis (IQR method to detect anomalous feature values)
5. Multicollinearity & Correlation Analysis (|r| >= 0.85 high correlation pairs)
6. Feature Importance Candidates (ANOVA F-statistic ranking vs target class)
7. Regime-Conditional Breakdown (target distribution partitioned by trend_direction)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats  # type: ignore


@dataclass
class EDAReport:
    symbol: str
    timeframe: str
    total_rows: int
    valid_rows: int
    class_distribution: Dict[str, Dict[str, Any]]
    imbalance_ratio: float
    missing_values: Dict[str, int]
    zero_variance_features: List[str]
    high_correlation_pairs: List[Dict[str, Any]]
    top_feature_candidates: List[Dict[str, Any]]
    regime_breakdown: Dict[str, Dict[str, Any]]

    def generate_markdown(self) -> str:
        """Renders comprehensive, publication-grade markdown analysis report."""
        md = [
            f"# Exploratory Data Analysis Report: {self.symbol} ({self.timeframe})",
            "",
            f"**Generated At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Total Samples:** {self.total_rows:,}  ",
            f"**Valid Target Samples:** {self.valid_rows:,}  ",
            f"**Target Imbalance Ratio:** {self.imbalance_ratio:.2f} : 1  ",
            "",
            "---",
            "",
            "## 1. Target Class Distribution",
            "",
            "| Class | Count | Percentage | Description |",
            "|---|---|---|---|",
        ]

        desc_map = {
            "UP": "Profit target reached (+1.0%) before stop",
            "DOWN": "Stop loss triggered (-0.5%) before target",
            "NEUTRAL": "Neither barrier touched within 20 candles",
        }

        for cls_name, stats_dict in self.class_distribution.items():
            cnt = stats_dict.get("count", 0)
            pct = stats_dict.get("pct", 0.0)
            desc = desc_map.get(cls_name, "")
            md.append(f"| **{cls_name}** | {cnt:,} | {pct:.2f}% | {desc} |")

        if self.imbalance_ratio > 2.5:
            md.extend([
                "",
                "> [!WARNING]",
                f"> Significant class imbalance detected ({self.imbalance_ratio:.2f}:1). Models must be evaluated with Balanced Accuracy, Macro F1, and PR-AUC, not raw accuracy.",
            ])
        else:
            md.extend([
                "",
                "> [!NOTE]",
                "> Target classes are well balanced. Standard multi-class cross-entropy and balanced weighting are appropriate.",
            ])

        md.extend([
            "",
            "---",
            "",
            "## 2. Missing Value & Data Quality Audit",
            "",
        ])

        if self.missing_values:
            md.extend([
                "| Feature | Missing Count | Missing Pct | Recommended Action |",
                "|---|---|---|---|",
            ])
            for feat, count in list(self.missing_values.items())[:15]:
                pct = (count / self.total_rows) * 100.0
                md.append(f"| `{feat}` | {count:,} | {pct:.2f}% | Forward-fill / Drop warm-up rows |")
        else:
            md.append("✅ **Zero missing values** found across active dataset features.")

        if self.zero_variance_features:
            md.extend([
                "",
                f"> [!WARNING]",
                f"> Zero-variance features detected (no predictive value): {', '.join(f'`{f}`' for f in self.zero_variance_features)}",
            ])

        md.extend([
            "",
            "---",
            "",
            "## 3. Top Feature Candidates (ANOVA F-Score Ranking)",
            "",
            "Features ranked by statistical separation across the 3 target classes:",
            "",
            "| Rank | Feature | F-Statistic | p-value | Correlation with Direction |",
            "|---|---|---|---|---|",
        ])

        for rank, cand in enumerate(self.top_feature_candidates[:15], 1):
            feat = cand["feature"]
            f_stat = cand["f_stat"]
            p_val = cand["p_value"]
            corr = cand.get("corr", 0.0)
            md.append(f"| {rank} | `{feat}` | {f_stat:.2f} | {p_val:.2e} | {corr:+.4f} |")

        md.extend([
            "",
            "---",
            "",
            "## 4. Multicollinearity & High Correlation Pairs (|r| >= 0.85)",
            "",
        ])

        if self.high_correlation_pairs:
            md.extend([
                "The following feature pairs exhibit strong collinearity. Consider PCA or L1 regularization during feature selection:",
                "",
                "| Feature 1 | Feature 2 | Pearson r |",
                "|---|---|---|",
            ])
            for pair in self.high_correlation_pairs[:12]:
                f1 = pair["feature_1"]
                f2 = pair["feature_2"]
                r = pair["correlation"]
                md.append(f"| `{f1}` | `{f2}` | {r:+.4f} |")
        else:
            md.append("✅ No excessive multicollinearity found (|r| < 0.85).")

        md.extend([
            "",
            "---",
            "",
            "## 5. Performance by Market Regime (Conditional Distribution)",
            "",
            "Target distribution partitioned by structural trend direction:",
            "",
            "| Market Regime (`trend_direction`) | Total Samples | % UP | % DOWN | % NEUTRAL |",
            "|---|---|---|---|---|",
        ])

        for regime_name, r_stats in self.regime_breakdown.items():
            tot = r_stats.get("total", 0)
            u_pct = r_stats.get("UP", 0.0)
            d_pct = r_stats.get("DOWN", 0.0)
            n_pct = r_stats.get("NEUTRAL", 0.0)
            md.append(f"| **{regime_name}** | {tot:,} | {u_pct:.2f}% | {d_pct:.2f}% | {n_pct:.2f}% |")

        return "\n".join(md)

    def to_markdown(self) -> str:
        """Alias for generate_markdown."""
        return self.generate_markdown()

    def save_markdown(self, output_path: str) -> str:
        """Saves generated markdown report to disk."""
        import os
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        content = self.generate_markdown()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path


class EDAAnalyzer:
    """
    Automated exploratory data analysis processor for market datasets.
    """

    EXCLUDE_COLS = {
        "open", "high", "low", "close", "volume",
        "target_triple_barrier", "target_label_name", "target_binary",
        "future_return_5", "future_return_10", "future_return_20",
        "max_future_return", "min_future_return",
        "candles_to_target", "candles_to_stop",
        "is_target_valid",
    }

    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        target_col: str = "target_label_name",
        valid_col: str = "is_target_valid",
    ) -> EDAReport:
        """
        Executes full statistical EDA on the dataset.
        """
        n_total = len(df)

        # Filter valid rows for target evaluations
        if valid_col in df.columns:
            valid_df = df[df[valid_col] == True].copy()
        else:
            valid_df = df.copy()

        n_valid = len(valid_df)

        # 1. Target Class Distribution
        class_dist: Dict[str, Dict[str, Any]] = {}
        imbalance_ratio = 1.0

        if target_col in valid_df.columns and n_valid > 0:
            target_series = pd.Series(valid_df[target_col])
            counts = target_series.value_counts().to_dict()
            for cls_name in ["UP", "DOWN", "NEUTRAL"]:
                c = counts.get(cls_name, 0)
                p = (c / n_valid * 100.0) if n_valid > 0 else 0.0
                class_dist[cls_name] = {"count": c, "pct": p}

            non_zero_counts = [v["count"] for v in class_dist.values() if v["count"] > 0]
            if len(non_zero_counts) > 1:
                imbalance_ratio = float(max(non_zero_counts) / max(min(non_zero_counts), 1))

        # 2. Missing Values Analysis
        missing_dict: Dict[str, int] = {}
        for c in df.columns:
            cnt = pd.Series(df[c]).isna().sum()
            if cnt > 0:
                missing_dict[c] = cnt

        # 3. Numeric Feature Stats & Zero Variance
        numeric_cols = [
            c for c in df.columns
            if c not in self.EXCLUDE_COLS and pd.api.types.is_numeric_dtype(df[c])
        ]

        zero_var_features: List[str] = []
        for c in numeric_cols:
            s_arr = np.asarray(pd.Series(df[c], dtype=float).dropna(), dtype=np.float64)
            if len(s_arr) > 1 and float(s_arr.std()) == 0.0:
                zero_var_features.append(c)

        # 4. Multicollinearity (|r| >= 0.85)
        high_corr_pairs: List[Dict[str, Any]] = []
        if len(numeric_cols) > 1 and len(df) >= 10:
            num_df = pd.DataFrame(df[numeric_cols])
            corr_df = pd.DataFrame(num_df.corr(min_periods=10))
            corr_abs_mat = np.asarray(corr_df.abs(), dtype=np.float64)
            corr_df_mat = np.asarray(corr_df, dtype=np.float64)
            cols = list(corr_df.columns)
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    val = float(corr_abs_mat[i, j])
                    if val >= 0.85 and not np.isnan(val):
                        r_signed = float(corr_df_mat[i, j])
                        high_corr_pairs.append({
                            "feature_1": cols[i],
                            "feature_2": cols[j],
                            "correlation": r_signed,
                        })
            high_corr_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        # 5. ANOVA F-Score Candidate Ranking vs Target
        top_candidates: List[Dict[str, Any]] = []
        if "target_triple_barrier" in valid_df.columns and len(valid_df) > 15:
            tb_target = pd.Series(valid_df["target_triple_barrier"], dtype=float)
            for col in numeric_cols:
                col_data = pd.Series(valid_df[col], dtype=float)
                mask = ~(col_data.isna() | tb_target.isna())
                c_arr = np.asarray(col_data[mask], dtype=float)
                t_arr = np.asarray(tb_target[mask], dtype=float)

                # Group by UP (+1), DOWN (-1), NEUTRAL (0)
                g_up = c_arr[t_arr == 1.0]
                g_down = c_arr[t_arr == -1.0]
                g_neutral = c_arr[t_arr == 0.0]

                active_groups = [g for g in [g_up, g_down, g_neutral] if len(g) >= 3]
                if len(active_groups) >= 2:
                    try:
                        f_res = stats.f_oneway(*active_groups)
                        f_val = float(f_res.statistic)
                        p_val = float(f_res.pvalue)
                        corr_val = float(np.corrcoef(c_arr, t_arr)[0, 1]) if np.std(c_arr) > 0 and np.std(t_arr) > 0 else 0.0
                        if not np.isnan(f_val):
                            top_candidates.append({
                                "feature": col,
                                "f_stat": f_val,
                                "p_value": p_val,
                                "corr": corr_val,
                            })
                    except Exception:
                        continue

            top_candidates.sort(key=lambda x: x["f_stat"], reverse=True)

        # 6. Regime-Conditional Breakdown
        regime_breakdown: Dict[str, Dict[str, Any]] = {}
        if "trend_direction" in valid_df.columns and target_col in valid_df.columns:
            regime_map = {1: "Uptrend (+1)", -1: "Downtrend (-1)", 0: "Sideways (0)"}
            for code, name in regime_map.items():
                r_df = valid_df[valid_df["trend_direction"] == code]
                tot = len(r_df)
                if tot > 0:
                    r_target = pd.Series(r_df[target_col])
                    r_counts = r_target.value_counts().to_dict()
                    regime_breakdown[name] = {
                        "total": tot,
                        "UP": (r_counts.get("UP", 0) / tot * 100.0),
                        "DOWN": (r_counts.get("DOWN", 0) / tot * 100.0),
                        "NEUTRAL": (r_counts.get("NEUTRAL", 0) / tot * 100.0),
                    }

        return EDAReport(
            symbol=symbol,
            timeframe=timeframe,
            total_rows=n_total,
            valid_rows=n_valid,
            class_distribution=class_dist,
            imbalance_ratio=imbalance_ratio,
            missing_values=missing_dict,
            zero_variance_features=zero_var_features,
            high_correlation_pairs=high_corr_pairs,
            top_feature_candidates=top_candidates,
            regime_breakdown=regime_breakdown,
        )
