"""
Checkpoint R6 — Transaction Graph
====================================
Builds a transaction graph (sender / recipient / merchant nodes;
payment / report / refund edges) using NetworkX, and derives
network-level risk signals — so a recipient can be flagged as risky
due to *who they're connected to*, even with few direct complaints.
"""

from __future__ import annotations
import networkx as nx
import numpy as np


class TransactionGraph:
    def __init__(self):
        self.g = nx.MultiDiGraph()

    # ---- construction ----
    def add_node(self, node_id: str, node_type: str, suspicious: bool = False, **attrs):
        self.g.add_node(node_id, node_type=node_type, suspicious=suspicious, **attrs)

    def add_payment(self, sender_id: str, recipient_id: str, amount: float, day: int = 0):
        self.g.add_edge(sender_id, recipient_id, edge_type="payment", amount=amount, day=day)

    def add_report(self, reporter_id: str, recipient_id: str, category: str, day: int = 0):
        self.g.add_edge(reporter_id, recipient_id, edge_type="report", category=category, day=day)

    def add_refund(self, recipient_id: str, sender_id: str, amount: float, day: int = 0):
        self.g.add_edge(recipient_id, sender_id, edge_type="refund", amount=amount, day=day)

    def mark_suspicious(self, node_id: str, suspicious: bool = True):
        if node_id in self.g.nodes:
            self.g.nodes[node_id]["suspicious"] = suspicious

    # ---- feature extraction (R6 acceptance) ----
    def features_for(self, recipient_id: str) -> dict:
        if recipient_id not in self.g.nodes:
            return self._empty_features()

        # direct neighbors (both directions: who pays them, who they pay/refund)
        predecessors = set(self.g.predecessors(recipient_id))
        successors = set(self.g.successors(recipient_id))
        neighbors = predecessors | successors
        unique_counterparties = len(neighbors)

        suspicious_neighbors = sum(
            1 for n in neighbors if self.g.nodes.get(n, {}).get("suspicious", False)
        )
        suspicious_neighbor_ratio = (
            suspicious_neighbors / unique_counterparties if unique_counterparties else 0.0
        )

        # incoming/outgoing volume from payment edges
        incoming = sum(
            data.get("amount", 0)
            for u, v, data in self.g.in_edges(recipient_id, data=True)
            if data.get("edge_type") == "payment"
        )
        outgoing = sum(
            data.get("amount", 0)
            for u, v, data in self.g.out_edges(recipient_id, data=True)
            if data.get("edge_type") in ("payment", "refund")
        )
        incoming_outgoing_ratio = incoming / outgoing if outgoing > 0 else (incoming if incoming > 0 else 0.0)

        # concentration: how much of incoming volume comes from the top sender (Herfindahl-ish)
        sender_volumes: dict[str, float] = {}
        for u, v, data in self.g.in_edges(recipient_id, data=True):
            if data.get("edge_type") == "payment":
                sender_volumes[u] = sender_volumes.get(u, 0) + data.get("amount", 0)
        if sender_volumes and incoming > 0:
            shares = np.array(list(sender_volumes.values())) / incoming
            transaction_concentration = float(np.sum(shares ** 2))  # HHI, 0=diffuse, 1=single sender
        else:
            transaction_concentration = 0.0

        # velocity: payments per unique day observed
        days = [
            data.get("day", 0)
            for u, v, data in self.g.in_edges(recipient_id, data=True)
            if data.get("edge_type") == "payment"
        ]
        span = (max(days) - min(days) + 1) if days else 1
        transaction_velocity = len(days) / span if span else 0.0

        # cluster indicator: is this node in a connected component that
        # contains a disproportionate share of suspicious nodes?
        undirected = self.g.to_undirected()
        component = nx.node_connected_component(undirected, recipient_id)
        comp_suspicious = sum(1 for n in component if self.g.nodes.get(n, {}).get("suspicious", False))
        cluster_risk_indicator = comp_suspicious / len(component) if component else 0.0

        return {
            "unique_counterparties": unique_counterparties,
            "suspicious_counterparties": suspicious_neighbors,
            "suspicious_neighbor_ratio": round(suspicious_neighbor_ratio, 4),
            "transaction_concentration": round(transaction_concentration, 4),
            "incoming_outgoing_ratio": round(incoming_outgoing_ratio, 4),
            "transaction_velocity": round(transaction_velocity, 4),
            "cluster_risk_indicator": round(cluster_risk_indicator, 4),
        }

    @staticmethod
    def _empty_features() -> dict:
        return {
            "unique_counterparties": 0,
            "suspicious_counterparties": 0,
            "suspicious_neighbor_ratio": 0.0,
            "transaction_concentration": 0.0,
            "incoming_outgoing_ratio": 0.0,
            "transaction_velocity": 0.0,
            "cluster_risk_indicator": 0.0,
        }


def build_demo_graph() -> TransactionGraph:
    """
    Demonstrates R6's acceptance criterion: a recipient with clean direct
    stats but many suspicious neighbors should still show elevated graph risk.
    """
    tg = TransactionGraph()

    tg.add_node("clean_recipient", "recipient")
    for i in range(5):
        sender = f"sender_{i}"
        suspicious = i < 3  # 3 of 5 counterparties are flagged elsewhere
        tg.add_node(sender, "sender", suspicious=suspicious)
        tg.add_payment(sender, "clean_recipient", amount=500, day=i)

    return tg


if __name__ == "__main__":
    tg = build_demo_graph()
    print("Graph-linked recipient (3/5 neighbors suspicious, 0 direct complaints):")
    print(tg.features_for("clean_recipient"))
