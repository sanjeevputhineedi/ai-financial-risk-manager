from __future__ import annotations

from typing import Iterable

import numpy as np


def fedavg(
    client_weights: Iterable[np.ndarray],
    client_sample_counts: Iterable[int],
) -> np.ndarray:
    """
    Federated Averaging (FedAvg).

    Combines locally trained client model parameters without sharing
    the clients' raw transaction data.
    """

    weights = list(client_weights)
    sample_counts = list(client_sample_counts)

    if not weights:
        raise ValueError("At least one client update is required.")

    if len(weights) != len(sample_counts):
        raise ValueError(
            "client_weights and client_sample_counts must have the same length."
        )

    total_samples = sum(sample_counts)

    if total_samples <= 0:
        raise ValueError("Total number of samples must be greater than zero.")

    aggregated = np.zeros_like(weights[0], dtype=float)

    for client_weight, sample_count in zip(weights, sample_counts):
        aggregated += client_weight * (sample_count / total_samples)

    return aggregated