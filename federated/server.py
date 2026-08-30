"""
Federated Learning Server — Checkpoint 10.

Central aggregation server that:
1. Coordinates FL rounds across clients
2. Collects model parameter updates (not raw data)
3. Aggregates using FedAvg strategy
4. Distributes global model back to clients
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from federated.strategy import FedAvgStrategy, AggregationResult


@dataclass
class ServerConfig:
    """Server configuration for federated learning."""
    num_rounds: int = 10
    min_clients: int = 3
    convergence_threshold: float = 0.001
    max_rounds: int = 20


class FederatedServer:
    """
    Central FL server that orchestrates the federated learning process.
    """

    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.strategy = FedAvgStrategy(
            min_clients=self.config.min_clients,
            convergence_threshold=self.config.convergence_threshold,
            max_rounds=self.config.max_rounds
        )
        self.current_round = 0
        self.clients_registered: List[str] = []
        self.round_results: List[AggregationResult] = []
        self.is_complete = False

    def register_client(self, client_id: str):
        """Register a client to participate in FL."""
        if client_id not in self.clients_registered:
            self.clients_registered.append(client_id)

    def run_round(self, client_parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute one round of federated learning.

        Args:
            client_parameters: List of parameter dicts from each client

        Returns:
            Round summary with global parameters
        """
        self.current_round += 1

        try:
            result = self.strategy.aggregate(self.current_round, client_parameters)
            self.round_results.append(result)

            if result.converged or self.current_round >= self.config.num_rounds:
                self.is_complete = True

            return {
                "round": self.current_round,
                "status": "converged" if result.converged else "in_progress",
                "global_parameters": self.strategy.get_global_parameters(),
                "num_clients": result.num_clients,
                "convergence_delta": result.convergence_delta,
                "is_complete": self.is_complete,
                "client_summaries": result.client_metrics
            }

        except Exception as e:
            return {
                "round": self.current_round,
                "status": "error",
                "error": str(e),
                "is_complete": False
            }

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the entire FL training process."""
        return {
            "total_rounds": self.current_round,
            "registered_clients": len(self.clients_registered),
            "is_complete": self.is_complete,
            "converged": self.round_results[-1].converged if self.round_results else False,
            "final_global_parameters": self.strategy.get_global_parameters(),
            "convergence_history": self.strategy.get_convergence_history()
        }
