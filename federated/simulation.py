"""
Federated Learning Simulation — Checkpoint 10.

End-to-end simulation script that:
1. Generates non-IID transaction data across 5+ simulated clients
2. Trains local models on each client
3. Runs FL rounds with FedAvg aggregation
4. Reports convergence and evaluation metrics

Privacy guarantee: Raw transaction records remain on local client nodes;
only model parameter updates are aggregated centrally.
"""

import numpy as np
import json
from typing import Dict, List, Any

from federated.client import FederatedClient, ClientConfig
from federated.server import FederatedServer, ServerConfig


def generate_non_iid_data(
    num_clients: int = 5,
    samples_per_client: int = 200,
    anomaly_base_rate: float = 0.1,
    seed: int = 42
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Generate non-IID transaction datasets for FL clients.

    Each client gets a different distribution to simulate real-world
    heterogeneity where different users/regions have different spending patterns.

    Features: [amount, time_of_day, recipient_diversity, velocity, balance_ratio]
    """
    rng = np.random.RandomState(seed)

    client_data = {}

    # Define non-IID distribution parameters per client
    client_profiles = [
        {"name": "urban_professional", "mean_amount": 2000, "std_amount": 1500, "peak_hours": [9, 18], "anomaly_rate": 0.08},
        {"name": "student", "mean_amount": 300, "std_amount": 200, "peak_hours": [12, 22], "anomaly_rate": 0.12},
        {"name": "small_business", "mean_amount": 5000, "std_amount": 3000, "peak_hours": [8, 17], "anomaly_rate": 0.15},
        {"name": "rural_farmer", "mean_amount": 800, "std_amount": 400, "peak_hours": [6, 14], "anomaly_rate": 0.06},
        {"name": "frequent_trader", "mean_amount": 10000, "std_amount": 8000, "peak_hours": [10, 16], "anomaly_rate": 0.10},
        {"name": "retiree", "mean_amount": 1500, "std_amount": 800, "peak_hours": [9, 15], "anomaly_rate": 0.05},
        {"name": "gig_worker", "mean_amount": 600, "std_amount": 500, "peak_hours": [7, 23], "anomaly_rate": 0.11},
    ]

    for i in range(num_clients):
        profile = client_profiles[i % len(client_profiles)]
        client_id = f"client_{i+1}_{profile['name']}"

        n = samples_per_client
        n_anomalies = int(n * profile["anomaly_rate"])
        n_normal = n - n_anomalies

        # Normal transactions
        normal_amounts = rng.normal(profile["mean_amount"], profile["std_amount"], n_normal).clip(10)
        normal_hours = rng.normal(np.mean(profile["peak_hours"]), 3, n_normal).clip(0, 23)
        normal_diversity = rng.uniform(0.2, 0.8, n_normal)
        normal_velocity = rng.exponential(2, n_normal).clip(0, 20)
        normal_balance_ratio = rng.uniform(0.05, 0.5, n_normal)

        # Anomalous transactions (different distribution)
        anom_amounts = rng.exponential(profile["mean_amount"] * 3, n_anomalies).clip(10)
        anom_hours = rng.uniform(0, 24, n_anomalies)
        anom_diversity = rng.uniform(0.0, 0.2, n_anomalies)
        anom_velocity = rng.exponential(10, n_anomalies).clip(0, 50)
        anom_balance_ratio = rng.uniform(0.6, 1.0, n_anomalies)

        features = np.vstack([
            np.column_stack([normal_amounts, normal_hours, normal_diversity, normal_velocity, normal_balance_ratio]),
            np.column_stack([anom_amounts, anom_hours, anom_diversity, anom_velocity, anom_balance_ratio])
        ])

        labels = np.concatenate([np.zeros(n_normal), np.ones(n_anomalies)])

        # Shuffle
        idx = rng.permutation(n)
        features = features[idx]
        labels = labels[idx]

        client_data[client_id] = {"features": features, "labels": labels}

    return client_data


def run_simulation(
    num_clients: int = 5,
    num_rounds: int = 10,
    samples_per_client: int = 200,
    seed: int = 42,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run a full federated learning simulation.

    Returns:
        Simulation results with round-by-round metrics and final evaluation.
    """
    if verbose:
        print("=" * 70)
        print("FEDERATED LEARNING SIMULATION — Privacy-Preserving Anomaly Detection")
        print("=" * 70)
        print(f"\nClients: {num_clients} | Rounds: {num_rounds} | Samples/client: {samples_per_client}")
        print(f"Privacy: Raw data NEVER leaves client nodes\n")

    # Step 1: Generate non-IID data
    client_data = generate_non_iid_data(
        num_clients=num_clients,
        samples_per_client=samples_per_client,
        seed=seed
    )

    # Step 2: Initialize clients and server
    clients = []
    for client_id, data in client_data.items():
        config = ClientConfig(client_id=client_id, num_samples=len(data["features"]))
        client = FederatedClient(config)
        client.load_data(data["features"], data["labels"])
        clients.append(client)

    server_config = ServerConfig(
        num_rounds=num_rounds,
        min_clients=min(3, num_clients),
        convergence_threshold=0.001
    )
    server = FederatedServer(server_config)

    for client in clients:
        server.register_client(client.client_id)

    # Step 3: Run FL rounds
    round_results = []

    for round_num in range(1, num_rounds + 1):
        if verbose:
            print(f"--- Round {round_num}/{num_rounds} ---")

        # Each client trains locally
        client_params = []
        for client in clients:
            metrics = client.train_local()
            params = client.get_model_parameters()
            client_params.append(params)

            if verbose:
                print(f"  {client.client_id}: {metrics['num_samples']} samples, "
                      f"{metrics['anomalies_detected']} anomalies detected")

        # Server aggregates
        round_result = server.run_round(client_params)
        round_results.append(round_result)

        if verbose:
            print(f"  -> Global convergence delta: {round_result['convergence_delta']:.6f}")

        # Distribute global parameters back to clients
        if round_result.get("global_parameters"):
            for client in clients:
                client.receive_global_parameters(round_result["global_parameters"])

        # Check convergence
        if round_result.get("is_complete"):
            if verbose:
                print(f"\n[OK] FL {'converged' if round_result.get('status') == 'converged' else 'completed'} "
                      f"after {round_num} rounds")
            break

    # Step 4: Final evaluation
    if verbose:
        print(f"\n{'=' * 70}")
        print("FINAL EVALUATION (post-FL)")
        print(f"{'=' * 70}")

    eval_results = []
    for client in clients:
        eval_metrics = client.evaluate()
        eval_results.append({
            "client_id": client.client_id,
            **eval_metrics
        })
        if verbose:
            print(f"  {client.client_id}:")
            print(f"    Precision: {eval_metrics.get('precision', 0):.4f} | "
                  f"Recall: {eval_metrics.get('recall', 0):.4f} | "
                  f"F1: {eval_metrics.get('f1', 0):.4f}")

    # Aggregate evaluation
    avg_f1 = np.mean([e.get("f1", 0) for e in eval_results])
    avg_precision = np.mean([e.get("precision", 0) for e in eval_results])
    avg_recall = np.mean([e.get("recall", 0) for e in eval_results])

    summary = server.get_summary()

    result = {
        "simulation_config": {
            "num_clients": num_clients,
            "num_rounds": num_rounds,
            "samples_per_client": samples_per_client,
            "seed": seed
        },
        "training_summary": summary,
        "round_results": round_results,
        "evaluation": {
            "per_client": eval_results,
            "aggregate": {
                "mean_precision": round(avg_precision, 4),
                "mean_recall": round(avg_recall, 4),
                "mean_f1": round(avg_f1, 4)
            }
        },
        "privacy_guarantee": "Raw transaction records remained on local client nodes. "
                           "Only model parameter updates were aggregated centrally."
    }

    if verbose:
        print(f"\nAggregate: Precision={avg_precision:.4f} | Recall={avg_recall:.4f} | F1={avg_f1:.4f}")
        print(f"\n[OK] Privacy guarantee: {result['privacy_guarantee']}")

    return result


if __name__ == "__main__":
    results = run_simulation(
        num_clients=5,
        num_rounds=10,
        samples_per_client=200,
        seed=42,
        verbose=True
    )

    # Save results
    import os
    out_path = os.path.join(os.path.dirname(__file__), "..", "experiments", "fl_simulation_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Convert numpy types for JSON serialization
    def convert(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=convert)

    print(f"\nResults saved to: {out_path}")
