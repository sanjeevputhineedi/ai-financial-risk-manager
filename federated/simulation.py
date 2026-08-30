from __future__ import annotations

import numpy as np

from federated.client import FederatedClient
from federated.server import FederatedServer


def create_synthetic_clients(
    num_clients: int = 5,
    samples_per_client: int = 100,
    seed: int = 42,
) -> list[FederatedClient]:
    """
    Create simulated users with different transaction behaviour.

    Each client represents a different user's device/account.
    Their raw transaction data remains local.
    """

    rng = np.random.default_rng(seed)
    clients = []

    for i in range(num_clients):
        user_bias = rng.normal(0, 0.5)

        features = rng.normal(
            loc=user_bias,
            scale=1.0,
            size=(samples_per_client, 2),
        )

        risk_signal = (
            0.8 * features[:, 0]
            + 1.2 * features[:, 1]
            + rng.normal(0, 0.5, samples_per_client)
        )

        labels = (risk_signal > 0).astype(float)

        clients.append(
            FederatedClient(
                client_id=f"user_{i + 1}",
                features=features,
                labels=labels,
            )
        )

    return clients


def evaluate_model(
    weights: np.ndarray,
    clients: list[FederatedClient],
) -> float:
    """
    Evaluate the global model across all simulated clients.
    """

    correct_predictions = 0
    total_samples = 0

    for client in clients:
        logits = client.features @ weights
        probabilities = 1 / (1 + np.exp(-logits))
        predictions = (probabilities >= 0.5).astype(float)

        correct_predictions += np.sum(
            predictions == client.labels
        )

        total_samples += len(client.labels)

    if total_samples == 0:
        return 0.0

    return correct_predictions / total_samples


def run_simulation(
    num_clients: int = 5,
    samples_per_client: int = 100,
    rounds: int = 10,
) -> np.ndarray:
    """
    Run multiple Federated Learning rounds.
    """

    clients = create_synthetic_clients(
        num_clients=num_clients,
        samples_per_client=samples_per_client,
    )

    server = FederatedServer(
        global_weights=np.zeros(2)
    )

    print("\nStarting Federated Learning Simulation\n")

    for round_number in range(1, rounds + 1):
        weights = server.train_round(
            clients=clients,
            learning_rate=0.05,
            epochs=10,
        )

        print(
            f"Round {round_number}/{rounds} "
            f"| Global weights: {np.round(weights, 4)}"
        )

    accuracy = evaluate_model(
        weights=server.global_weights,
        clients=clients,
    )

    print("\nFederated Learning Simulation Completed")
    print(f"Global model accuracy: {accuracy:.2%}")

    return server.global_weights


if __name__ == "__main__":
    run_simulation()