"""
Tests for the analytics engine.
"""

import pandas as pd
import numpy as np
import pytest
from backend.analytics.engine import AnalyticsEngine


@pytest.fixture
def engine():
    return AnalyticsEngine()


@pytest.fixture
def sample_df():
    np.random.seed(0)
    n = 100
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "revenue": np.random.normal(1000, 200, n),
        "units": np.random.randint(10, 100, n),
        "region": np.random.choice(["North", "South", "East", "West"], n),
    })


def test_describe_shape(engine, sample_df):
    result = engine.describe(sample_df)
    assert result["shape"]["rows"] == 100
    assert result["shape"]["columns"] == 4


def test_describe_numeric_stats(engine, sample_df):
    result = engine.describe(sample_df)
    revenue_col = next(c for c in result["columns"] if c["name"] == "revenue")
    assert "mean" in revenue_col
    assert revenue_col["min"] < revenue_col["max"]


def test_anomaly_detection(engine, sample_df):
    # Inject a clear outlier
    sample_df.loc[0, "revenue"] = 999999.0
    result = engine.detect_anomalies(sample_df, "revenue")
    assert result["iqr_method"]["outlier_count"] >= 1
    assert 999999.0 in result["iqr_method"]["outlier_values"]


def test_trend_analysis(engine, sample_df):
    # Add a clear upward trend
    sample_df["trend_col"] = np.arange(100) * 10.0
    result = engine.trend_analysis(sample_df, "trend_col", "date")
    assert result["trend"]["direction"] == "upward"
    assert result["trend"]["slope"] > 0


def test_correlation(engine, sample_df):
    result = engine.correlate(sample_df, "revenue", "units")
    assert "pearson_correlation" in result
    assert -1.0 <= result["pearson_correlation"] <= 1.0


def test_segment_categorical(engine, sample_df):
    result = engine.segment(sample_df, "region")
    assert result["type"] == "categorical"
    assert len(result["segments"]) <= 4


def test_segment_numeric(engine, sample_df):
    result = engine.segment(sample_df, "revenue")
    assert result["type"] == "numeric_bins"
    assert len(result["segments"]) == 5


def test_forecast(engine, sample_df):
    result = engine.forecast(sample_df, "revenue", "date", periods=7)
    assert result["forecast_periods"] == 7
    assert len(result["forecasts"]) == 7
    assert all("lower_ci" in f and "upper_ci" in f for f in result["forecasts"])
