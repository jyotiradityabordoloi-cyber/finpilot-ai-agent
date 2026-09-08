from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from agents.state import InvestigationState
from agents.tools import (
    investigate_transaction,
    create_finding,
)


def investigate_node(state: InvestigationState) -> Dict[str, Any]:
    """
    Run the deterministic financial investigation.
    """

    transaction_id = state.get("transaction_id")

    if not transaction_id:
        return {
            "status": "error",
            "investigation_steps": [
                "Transaction ID was not provided."
            ],
        }

    result = investigate_transaction(transaction_id)

    return {
        "status": result["status"],
        "vendor": result.get("vendor"),
        "transaction_amount": result.get("amount"),
        "severity": result.get("severity"),
        "evidence": result.get("evidence", []),
        "investigation_steps": [
            "Analyzed transaction",
            "Checked historical spending",
            "Matched invoice",
            "Checked for duplicate transactions",
        ],
    }


def finding_node(state: InvestigationState) -> Dict[str, Any]:
    """
    Convert investigation evidence into a structured finding.
    """

    investigation = {
        "status": state.get("status"),
        "transaction_id": state.get("transaction_id"),
        "vendor": state.get("vendor"),
        "amount": state.get("transaction_amount"),
        "severity": state.get("severity"),
        "evidence": state.get("evidence", []),
    }

    result = create_finding(investigation)

    return {
        "finding": result.get("finding"),
        "recommendation": (
            result.get("finding", {}).get("recommendation")
            if result.get("finding")
            else None
        ),
    }


def build_investigation_graph():
    """
    Build the FinPilot investigation graph.
    """

    graph = StateGraph(InvestigationState)

    graph.add_node("investigate", investigate_node)
    graph.add_node("create_finding", finding_node)

    graph.add_edge(START, "investigate")
    graph.add_edge("investigate", "create_finding")
    graph.add_edge("create_finding", END)

    return graph.compile()


finpilot_graph = build_investigation_graph()