"""
Federated Learning Client — Checkpoint 10.

Each client trains a local anomaly detector on its private transaction data,
then sends only model parameter updates (not raw data) to the central server.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import IsolationForest
from dataclasses import dataclass, field


@dataclass
class ClientConfig:
    """Configuration for a federated learning client."""
    client_id: str
    num_samples: int = 200
    anomaly_ratio: float = 0.1
    data_distribution: str = "non_iid"  # "iid" or "non_iid"


@dataclass
class LocalDataset:
    """Private local transaction dataset — never leaves the client."""
    client_id: str
    features: np.ndarray = field(default_factory=lambda: np.array([]))
    labels: np.ndarray = field(default_factory=lambda: np.array([]))
    num_samples: int = 0


class FederatedClient:
    """
    A single FL client node that:
    1. Holds private local transaction data
    2. Trains a local model on that data
    3. Extracts and sends model parameters (not raw data) to the server
    4. Receives aggregated parameters from the server
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self.client_id = config.client_id
        self.local_data: Optional[LocalDataset] = None
        self.model = IsolationForest(
            n_estimators=50,
            contamination=config.anomaly_ratio,
            random_state=42
        )
        self.training_metrics: Dict[str, Any] = {}

    def load_data(self, features: np.ndarray, labels: np.ndarray):
        """Load private local dataset — this data never leaves the client."""
        self.local_data = LocalDataset(
            client_id=self.client_id,
            features=features,
            labels=labels,
            num_samples=len(features)
        )

    def train_local(self) -> Dict[str, Any]:
        """
        Train the local model on private data.
        Returns training metrics (NOT raw data).
        """
        if self.local_data is None or self.local_data.num_samples == 0:
            return {"error": "No local data available"}

        self.model.fit(self.local_data.features)

        # Compute local metrics
        predictions = self.model.predict(self.local_data.features)
        scores = self.model.score_samples(self.local_data.features)

        anomaly_count = int(np.sum(predictions == -1))
        normal_count = int(np.sum(predictions == 1))

        self.training_metrics = {
            "client_id": self.client_id,
            "num_samples": self.local_data.num_samples,
            "anomalies_detected": anomaly_count,
            "normal_detected": normal_count,
            "mean_score": float(np.mean(scores)),
            "std_score": float(np.std(scores)),
            "status": "trained"
        }

        return self.training_metrics

    def get_model_parameters(self) -> Dict[str, Any]:
        """
        Extract model parameters to send to the server.
        PRIVACY: Only statistical parameters are shared, never raw data.
        """
        if not hasattr(self.model, "estimators_") or self.model.estimators_ is None:
            return {"client_id": self.client_id, "parameters": None}

        # Extract aggregate statistics from the isolation forest
        # These are model parameters, not data
        params = {
            "client_id": self.client_id,
            "n_estimators": len(self.model.estimators_),
            "offset": float(self.model.offset_),
            "max_samples": int(self.model.max_samples_),
            "mean_anomaly_score": self.training_metrics.get("mean_score", 0),
            "std_anomaly_score": self.training_metrics.get("std_score", 0),
            "anomaly_ratio": self.training_metrics.get("anomalies_detected", 0) /
                           max(self.training_metrics.get("num_samples", 1), 1),
            "num_training_samples": self.local_data.num_samples if self.local_data else 0
        }

        return params

    def receive_global_parameters(self, global_params: Dict[str, Any]):
        """
        Receive aggregated parameters from the server.
        In a full FL implementation, this would update model weights.
        Here we update the decision threshold based on global consensus.
        """
        if "global_offset" in global_params:
            # Blend local and global offsets
            local_weight = 0.3
            self.model.offset_ = (
                local_weight * self.model.offset_ +
                (1 - local_weight) * global_params["global_offset"]
            )

    def evaluate(self) -> Dict[str, float]:
        """Evaluate the model on local data after receiving global update."""
        if self.local_data is None:
            return {}

        predictions = self.model.predict(self.local_data.features)
        scores = self.model.score_samples(self.local_data.features)

        # Compare predictions with true labels
        true_anomalies = self.local_data.labels == 1
        pred_anomalies = predictions == -1

        tp = int(np.sum(true_anomalies & pred_anomalies))
        fp = int(np.sum(~true_anomalies & pred_anomalies))
        fn = int(np.sum(true_anomalies & ~pred_anomalies))
        tn = int(np.sum(~true_anomalies & ~pred_anomalies))

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-6)

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "mean_anomaly_score": float(np.mean(scores))
        }
