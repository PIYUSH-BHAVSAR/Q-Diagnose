"""
backend/benchmarking/risk_stratification.py
Owner: Piyush & Radha
Phase: 11 — Benchmarking & PS Deliverable 4

Risk Stratification & Sensitivity/Specificity Threshold Tuning Engine.
Fulfills Problem Statement Deliverable 4:
  - "Early risk stratification" (HIGH_RISK / MODERATE_RISK / LOW_RISK)
  - "Threshold tuning for sensitivity/specificity"

Clinical Utility:
  Standard ML uses threshold tau = 0.5.
  In disease screening (cancer, cardiovascular), false negatives carry severe clinical penalty.
  Lowering threshold tau (e.g. to 0.35) increases Recall (Sensitivity) to catch early-stage disease.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import numpy as np

from backend.benchmarking.metrics import MetricsCalculator


class RiskStratifier:
    """
    Categorizes predicted disease probabilities into clinical risk tiers.
    """

    HIGH_RISK_THRESHOLD = 0.70
    MODERATE_RISK_THRESHOLD = 0.35

    @classmethod
    def stratify(cls, probability_score: float) -> dict:
        """
        Classify a single patient probability score into a risk tier with clinical recommendations.
        """
        score = float(probability_score)
        if score >= cls.HIGH_RISK_THRESHOLD:
            risk_level = "HIGH_RISK"
            action = "Urgent diagnostic confirmation and specialist referral required."
            color = "#dc2626"  # Red
        elif score >= cls.MODERATE_RISK_THRESHOLD:
            risk_level = "MODERATE_RISK"
            action = "Intermediate risk — recommended for 3-month follow-up screening."
            color = "#d97706"  # Amber
        else:
            risk_level = "LOW_RISK"
            action = "Low risk — maintain standard routine health monitoring."
            color = "#16a34a"  # Green

        return {
            "probability_score": round(score, 4),
            "risk_level": risk_level,
            "action_recommendation": action,
            "color_code": color,
        }

    @classmethod
    def stratify_batch(cls, scores: np.ndarray) -> List[dict]:
        """Classify a batch of probability scores."""
        return [cls.stratify(s) for s in scores]


class ThresholdTuner:
    """
    Computes optimal classification decision thresholds to optimize Sensitivity (Recall) vs Specificity.
    """

    @classmethod
    def find_optimal_threshold(
        cls,
        y_true: np.ndarray,
        y_scores: np.ndarray,
        target_sensitivity: float = 0.90,
    ) -> dict:
        """
        Find decision threshold tau in [0.05, 0.95] that achieves target sensitivity (recall).

        Returns:
            dict containing optimal threshold, achieved sensitivity, specificity, and confusion matrix.
        """
        best_threshold = 0.50
        best_metrics = MetricsCalculator.compute(y_true, (y_scores >= 0.5).astype(int), y_scores)
        best_dist = float("inf")

        thresholds = np.linspace(0.05, 0.95, 91)
        grid_results = []

        for tau in thresholds:
            y_pred = (y_scores >= tau).astype(int)
            m = MetricsCalculator.compute(y_true, y_pred, y_scores)

            grid_results.append({
                "threshold": round(float(tau), 2),
                "sensitivity": m["recall"],
                "specificity": m["specificity"],
                "f1_score": m["f1_score"],
                "accuracy": m["accuracy"],
            })

            # Check closeness to target sensitivity while maximizing specificity
            if m["recall"] >= target_sensitivity:
                dist = (m["recall"] - target_sensitivity) + (1.0 - m["specificity"])
                if dist < best_dist:
                    best_dist = dist
                    best_threshold = float(tau)
                    best_metrics = m

        return {
            "target_sensitivity": target_sensitivity,
            "optimal_threshold": round(best_threshold, 2),
            "achieved_sensitivity": best_metrics["recall"],
            "achieved_specificity": best_metrics["specificity"],
            "achieved_accuracy": best_metrics["accuracy"],
            "achieved_f1_score": best_metrics["f1_score"],
            "confusion_matrix": best_metrics["confusion_matrix"],
            "threshold_grid": grid_results[:10],  # sample grid for frontend
        }
