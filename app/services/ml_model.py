"""
app/services/ml_model.py
────────────────────────
Anomaly-detection risk scoring using IsolationForest.

Features:
  - 5 engineered features for better accuracy
  - Human-readable risk explanations per record
  - Graceful fallback to rule-based scoring when data is insufficient
  - Model persisted to disk; auto-reloads on next run
"""

from __future__ import annotations

import os
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import config
from app.utils.logger import logger

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

FEATURES = [
    "transaction_volume",
    "compliance_score",
    "compliance_ratio",        # compliance_score / 100
    "volume_per_compliance",   # transaction_volume / (compliance_score + 1)
    "risk_flag",               # 1 if compliance < 50, else 0
]


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["compliance_ratio"] = out["compliance_score"] / 100.0
    out["volume_per_compliance"] = out["transaction_volume"] / (out["compliance_score"] + 1)
    out["risk_flag"] = (out["compliance_score"] < 50).astype(int)
    return out[FEATURES].fillna(0)


def _fallback_risk(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Rule-based scoring when there isn't enough data to train."""
    risk = np.clip(100.0 - df["compliance_score"].values, 0, 100)
    predictions = np.where(risk >= config.RISK_HIGH_THRESHOLD, -1, 1)
    logger.warning("Using fallback rule-based risk scoring.")
    return risk, predictions


class ModelManager:
    def __init__(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        self.model: IsolationForest | None = None
        self.scaler: StandardScaler | None = None

    def _is_ready(self) -> bool:
        return self.model is not None and self.scaler is not None

    def train(self, df: pd.DataFrame) -> bool:
        """Train IsolationForest. Returns True on success."""
        if df.empty or len(df) < 10:
            logger.warning(f"Not enough data to train ({len(df)} records). Need ≥ 10.")
            return False
        try:
            X = _build_features(df)
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            self.model = IsolationForest(
                contamination=config.MODEL_CONTAMINATION,
                random_state=42,
                n_estimators=200,
            )
            self.model.fit(X_scaled)
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.scaler, SCALER_PATH)
            logger.info(f"Model trained on {len(df)} records and saved.")
            return True
        except Exception as exc:
            logger.error(f"Training failed: {exc}")
            return False

    def load(self) -> bool:
        try:
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            logger.info("Model loaded from disk.")
            return True
        except Exception:
            return False

    def predict_risk(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (risk_scores 0-100, predictions 1=normal/-1=anomaly)."""
        if df.empty:
            return np.array([]), np.array([])
        if len(df) < 10:
            return _fallback_risk(df)
        if not self._is_ready():
            if not self.load():
                if not self.train(df):
                    return _fallback_risk(df)
        try:
            X = _build_features(df)
            X_scaled = self.scaler.transform(X)
            raw_scores = self.model.decision_function(X_scaled)
            predictions = self.model.predict(X_scaled)
            score_min, score_max = raw_scores.min(), raw_scores.max()
            if score_max - score_min < 1e-10:
                risk = np.full(len(raw_scores), 50.0)
            else:
                risk = (1 - (raw_scores - score_min) / (score_max - score_min)) * 100
            return risk, predictions
        except Exception as exc:
            logger.error(f"Prediction failed, using fallback: {exc}")
            return _fallback_risk(df)

    def get_risk_explanation(self, row: pd.Series) -> str:
        """Generate a human-readable explanation for a record's risk level."""
        reasons = []
        if row.get("compliance_score", 100) < 50:
            reasons.append(f"low compliance score ({row['compliance_score']:.1f}%)")
        if row.get("transaction_volume", 0) > 100_000:
            reasons.append(f"high transaction volume (₹{row['transaction_volume']:,.0f})")
        if row.get("risk_score", 0) >= config.RISK_CRITICAL_THRESHOLD:
            reasons.append("flagged as statistical anomaly by ML model")
        return ", ".join(reasons) if reasons else "within normal parameters"


# Singleton shared across the app
model_manager = ModelManager()