from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FederatedClient:
    """
    Simulated federated-learning client.

    Each client keeps its transaction data locally and trains a small
    personalized risk model. Only model parameters are returned.
    """

    client_id: str
    features: np.ndarray
    labels: np.ndarray

    def train(
        self,
        global_weights: np.ndarray,
        learning_rate: float = 0.01,
        epochs: int = 20,
    ) -> np.ndarray:
        """
        Train a simple logistic-regression model locally using
        gradient descent and return updated weights.
        """

        weights = global_weights.astype(float).copy()

        if len(self.features) == 0:
            return weights

        for _ in range(epochs):
            logits = self.features @ weights
            predictions = 1 / (1 + np.exp(-logits))

            gradient = (
                self.features.T @ (predictions - self.labels)
            ) / len(self.features)

            weights -= learning_rate * gradient

        return weights

    @property
    def sample_count(self) -> int:
        """Return the number of local training samples."""
        return len(self.features)