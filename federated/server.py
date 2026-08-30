from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from federated.client import FederatedClient
from federated.strategy import fedavg


@dataclass
class FederatedServer:
    """
    Coordinates federated learning rounds.

    The server sends global model weights to clients, receives only
    updated model weights, and aggregates them using FedAvg.
    """

    global_weights: np.ndarray

    def train_round(
        self,
        clients: list[FederatedClient],
        learning_rate: float = 0.01,
        epochs: int = 20,
    ) -> np.ndarray:
        """
        Run one complete federated learning round.
        """

        if not clients:
            raise ValueError("At least one client is required.")

        client_updates = []
        client_sample_counts = []

        for client in clients:
            updated_weights = client.train(
                global_weights=self.global_weights,
                learning_rate=learning_rate,
                epochs=epochs,
            )

            client_updates.append(updated_weights)
            client_sample_counts.append(client.sample_count)

        self.global_weights = fedavg(
            client_weights=client_updates,
            client_sample_counts=client_sample_counts,
        )

        return self.global_weights