"""
Federated Learning Strategy — Checkpoint 10.

Custom aggregation strategy for combining client model updates.
Implements FedAvg-style parameter averaging with convergence tracking.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AggregationResult:
    """Result of a single FL aggregation round."""
    round_number: int
    num_clients: int
    global_offset: float
    global_mean_anomaly_score: float
    global_anomaly_ratio: float
    client_metrics: List[Dict[str, Any]]
    convergence_delta: float = 0.0
    converged: bool = False


class FedAvgStrategy:
    """
    Federated Averaging (FedAvg) strategy for aggregating client model updates.

    Computes weighted average of client parameters based on dataset size.
    Tracks convergence across rounds.
    """

    def __init__(
        self,
        min_clients: int = 3,
        convergence_threshold: float = 0.001,
        max_rounds: int = 20
    ):
        self.min_clients = min_clients
        self.convergence_threshold = convergence_threshold
        self.max_rounds = max_rounds
        self.round_history: List[AggregationResult] = []
        self.previous_global_offset: Optional[float] = None

    def aggregate(
        self,
        round_number: int,
        client_parameters: List[Dict[str, Any]]
    ) -> AggregationResult:
        """
        Aggregate client model parameters using weighted FedAvg.

        Args:
            round_number: Current FL round
            client_parameters: List of parameter dicts from each client

        Returns:
            AggregationResult with global parameters
        """
        valid_params = [p for p in client_parameters if p.get("n_estimators")]

        if len(valid_params) < self.min_clients:
            raise ValueError(
                f"Insufficient clients: {len(valid_params)} < {self.min_clients}"
            )

        # Weighted FedAvg by dataset size
        total_samples = sum(p.get("num_training_samples", 1) for p in valid_params)

        # Aggregate offset (model decision boundary)
        global_offset = sum(
            p["offset"] * p.get("num_training_samples", 1) / total_samples
            for p in valid_params
        )

        # Aggregate anomaly scores
        global_mean_score = sum(
            p["mean_anomaly_score"] * p.get("num_training_samples", 1) / total_samples
            for p in valid_params
        )

        # Aggregate anomaly ratios
        global_anomaly_ratio = sum(
            p["anomaly_ratio"] * p.get("num_training_samples", 1) / total_samples
            for p in valid_params
        )

        # Convergence tracking
        convergence_delta = 0.0
        converged = False
        if self.previous_global_offset is not None:
            convergence_delta = abs(global_offset - self.previous_global_offset)
            converged = convergence_delta < self.convergence_threshold

        self.previous_global_offset = global_offset

        result = AggregationResult(
            round_number=round_number,
            num_clients=len(valid_params),
            global_offset=global_offset,
            global_mean_anomaly_score=global_mean_score,
            global_anomaly_ratio=global_anomaly_ratio,
            client_metrics=[
                {
                    "client_id": p["client_id"],
                    "samples": p.get("num_training_samples", 0),
                    "anomaly_ratio": round(p["anomaly_ratio"], 4)
                }
                for p in valid_params
            ],
            convergence_delta=convergence_delta,
            converged=converged
        )

        self.round_history.append(result)
        return result

    def get_global_parameters(self) -> Dict[str, Any]:
        """Get the latest global parameters for distribution to clients."""
        if not self.round_history:
            return {}

        latest = self.round_history[-1]
        return {
            "global_offset": latest.global_offset,
            "global_mean_anomaly_score": latest.global_mean_anomaly_score,
            "global_anomaly_ratio": latest.global_anomaly_ratio,
            "round_number": latest.round_number,
            "converged": latest.converged
        }

    def get_convergence_history(self) -> List[Dict[str, float]]:
        """Return convergence metrics across all rounds."""
        return [
            {
                "round": r.round_number,
                "delta": r.convergence_delta,
                "offset": r.global_offset,
                "anomaly_ratio": r.global_anomaly_ratio,
                "num_clients": r.num_clients
            }
            for r in self.round_history
        ]
