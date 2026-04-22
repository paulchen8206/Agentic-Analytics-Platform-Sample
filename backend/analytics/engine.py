"""
Core analytics engine: statistics, anomaly detection, trends, forecasting.
"""

import math
from typing import Any
import numpy as np
import pandas as pd
from scipy import stats


class AnalyticsEngine:

    # ------------------------------------------------------------------
    # Describe
    # ------------------------------------------------------------------

    def describe(self, df: pd.DataFrame) -> dict:
        info: dict[str, Any] = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": [],
            "missing_values": df.isnull().sum().to_dict(),
            "dtypes": df.dtypes.astype(str).to_dict(),
        }
        for col in df.columns:
            col_info: dict[str, Any] = {"name": col, "dtype": str(df[col].dtype)}
            if pd.api.types.is_numeric_dtype(df[col]):
                s = df[col].dropna()
                col_info.update({
                    "min": float(s.min()) if len(s) else None,
                    "max": float(s.max()) if len(s) else None,
                    "mean": float(s.mean()) if len(s) else None,
                    "median": float(s.median()) if len(s) else None,
                    "std": float(s.std()) if len(s) else None,
                    "skewness": float(s.skew()) if len(s) > 2 else None,
                })
            else:
                col_info.update({
                    "unique_count": int(df[col].nunique()),
                    "top_values": df[col].value_counts().head(5).to_dict(),
                })
            info["columns"].append(col_info)
        return info

    # ------------------------------------------------------------------
    # Natural Language Query
    # ------------------------------------------------------------------

    def natural_language_query(self, df: pd.DataFrame, query: str) -> dict:
        """Simple keyword-based NL query handler (no LLM dependency)."""
        q = query.lower()
        results: dict[str, Any] = {"query": query, "results": []}

        # Aggregations
        if any(kw in q for kw in ["sum", "total"]):
            num_cols = df.select_dtypes(include="number").columns.tolist()
            results["results"] = {col: float(df[col].sum()) for col in num_cols}
        elif any(kw in q for kw in ["average", "mean", "avg"]):
            num_cols = df.select_dtypes(include="number").columns.tolist()
            results["results"] = {col: float(df[col].mean()) for col in num_cols}
        elif "count" in q:
            results["results"] = {"row_count": len(df)}
        elif any(kw in q for kw in ["max", "maximum", "highest", "top"]):
            num_cols = df.select_dtypes(include="number").columns.tolist()
            results["results"] = {col: float(df[col].max()) for col in num_cols}
        elif any(kw in q for kw in ["min", "minimum", "lowest"]):
            num_cols = df.select_dtypes(include="number").columns.tolist()
            results["results"] = {col: float(df[col].min()) for col in num_cols}
        else:
            results["results"] = df.head(10).to_dict(orient="records")

        return results

    # ------------------------------------------------------------------
    # Anomaly Detection (IQR + Z-Score)
    # ------------------------------------------------------------------

    def detect_anomalies(self, df: pd.DataFrame, column: str) -> dict:
        if column not in df.columns:
            return {"error": f"Column '{column}' not found"}
        series = df[column].dropna()
        if not pd.api.types.is_numeric_dtype(series):
            return {"error": f"Column '{column}' is not numeric"}

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        iqr_outliers = series[(series < lower) | (series > upper)]

        z_scores = np.abs(stats.zscore(series))
        z_outliers = series[z_scores > 3]

        return {
            "column": column,
            "total_values": len(series),
            "iqr_method": {
                "lower_bound": float(lower),
                "upper_bound": float(upper),
                "outlier_count": len(iqr_outliers),
                "outlier_percentage": round(len(iqr_outliers) / len(series) * 100, 2),
                "outlier_values": iqr_outliers.head(20).tolist(),
            },
            "zscore_method": {
                "threshold": 3.0,
                "outlier_count": len(z_outliers),
                "outlier_percentage": round(len(z_outliers) / len(series) * 100, 2),
                "outlier_values": z_outliers.head(20).tolist(),
            },
            "statistics": {
                "mean": float(series.mean()),
                "std": float(series.std()),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
            },
        }

    # ------------------------------------------------------------------
    # Trend Analysis
    # ------------------------------------------------------------------

    def trend_analysis(self, df: pd.DataFrame, column: str, time_col: str) -> dict:
        if column not in df.columns or time_col not in df.columns:
            return {"error": "Column(s) not found"}
        temp = df[[time_col, column]].dropna().copy()
        try:
            temp[time_col] = pd.to_datetime(temp[time_col])
        except Exception:
            pass
        temp = temp.sort_values(time_col)

        values = temp[column].values.astype(float)
        n = len(values)
        x = np.arange(n)
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)

        # Period-over-period change
        mid = n // 2
        first_half_mean = float(np.mean(values[:mid])) if mid > 0 else None
        second_half_mean = float(np.mean(values[mid:])) if mid > 0 else None
        pct_change = None
        if first_half_mean and first_half_mean != 0:
            pct_change = round((second_half_mean - first_half_mean) / abs(first_half_mean) * 100, 2)

        return {
            "column": column,
            "time_column": time_col,
            "data_points": n,
            "trend": {
                "direction": "upward" if slope > 0 else "downward" if slope < 0 else "flat",
                "slope": round(float(slope), 6),
                "r_squared": round(float(r_value ** 2), 4),
                "p_value": round(float(p_value), 6),
                "significant": p_value < 0.05,
            },
            "period_comparison": {
                "first_half_mean": first_half_mean,
                "second_half_mean": second_half_mean,
                "pct_change": pct_change,
            },
            "rolling_averages": temp.set_index(time_col)[column]
                .rolling(min(7, max(2, n // 10)))
                .mean()
                .dropna()
                .tail(30)
                .reset_index()
                .rename(columns={time_col: "date", column: "rolling_avg"})
                .assign(date=lambda d: d["date"].astype(str))
                .to_dict(orient="records"),
        }

    # ------------------------------------------------------------------
    # Correlation
    # ------------------------------------------------------------------

    def correlate(self, df: pd.DataFrame, col_a: str, col_b: str) -> dict:
        if col_a not in df.columns or col_b not in df.columns:
            return {"error": "Column(s) not found"}
        pair = df[[col_a, col_b]].dropna()
        if len(pair) < 3:
            return {"error": "Not enough data points"}
        corr, p_value = stats.pearsonr(pair[col_a], pair[col_b])
        spearman_corr, _ = stats.spearmanr(pair[col_a], pair[col_b])

        strength = "very strong" if abs(corr) > 0.8 else "strong" if abs(corr) > 0.6 else \
                   "moderate" if abs(corr) > 0.4 else "weak" if abs(corr) > 0.2 else "negligible"
        direction = "positive" if corr > 0 else "negative"

        return {
            "col_a": col_a, "col_b": col_b,
            "pearson_correlation": round(float(corr), 4),
            "spearman_correlation": round(float(spearman_corr), 4),
            "p_value": round(float(p_value), 6),
            "significant": p_value < 0.05,
            "interpretation": f"{strength} {direction} correlation",
            "data_points": len(pair),
        }

    # ------------------------------------------------------------------
    # Segmentation
    # ------------------------------------------------------------------

    def segment(self, df: pd.DataFrame, column: str) -> dict:
        if column not in df.columns:
            return {"error": f"Column '{column}' not found"}
        series = df[column].dropna()

        if pd.api.types.is_numeric_dtype(series):
            bins = pd.cut(series, bins=5)
            counts = bins.value_counts().sort_index()
            return {
                "column": column,
                "type": "numeric_bins",
                "segments": [
                    {"range": str(k), "count": int(v), "pct": round(v / len(series) * 100, 2)}
                    for k, v in counts.items()
                ],
            }
        else:
            counts = series.value_counts()
            return {
                "column": column,
                "type": "categorical",
                "total_categories": int(counts.shape[0]),
                "segments": [
                    {"value": str(k), "count": int(v), "pct": round(v / len(series) * 100, 2)}
                    for k, v in counts.head(20).items()
                ],
            }

    # ------------------------------------------------------------------
    # Forecasting (simple linear extrapolation + Holt's exponential smoothing)
    # ------------------------------------------------------------------

    def forecast(self, df: pd.DataFrame, column: str, time_col: str, periods: int = 7) -> dict:
        if column not in df.columns or time_col not in df.columns:
            return {"error": "Column(s) not found"}
        temp = df[[time_col, column]].dropna().copy()
        try:
            temp[time_col] = pd.to_datetime(temp[time_col])
        except Exception:
            pass
        temp = temp.sort_values(time_col)
        values = temp[column].values.astype(float)
        n = len(values)

        if n < 4:
            return {"error": "Not enough data for forecasting (need at least 4 points)"}

        # Holt's double exponential smoothing
        alpha, beta = 0.3, 0.1
        level, trend = values[0], values[1] - values[0]
        smoothed = [level + trend]
        for v in values[1:]:
            prev_level = level
            level = alpha * v + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
            smoothed.append(level + trend)

        forecasts = [level + (i + 1) * trend for i in range(periods)]

        # Residual std for confidence interval
        residuals = values - np.array(smoothed[:n])
        res_std = float(np.std(residuals))

        return {
            "column": column,
            "historical_points": n,
            "forecast_periods": periods,
            "forecasts": [
                {
                    "period": i + 1,
                    "value": round(float(v), 4),
                    "lower_ci": round(float(v - 1.96 * res_std), 4),
                    "upper_ci": round(float(v + 1.96 * res_std), 4),
                }
                for i, v in enumerate(forecasts)
            ],
            "method": "Holt double exponential smoothing",
            "trend_direction": "upward" if trend > 0 else "downward" if trend < 0 else "flat",
        }
