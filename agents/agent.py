from typing import Any, Dict

from langchain.agents import create_agent
from langchain.tools import tool

from agents.llm import create_llm
from agents.tools import (
    analyze_transaction,
    analyze_historical_spending,
    match_invoice,
    detect_duplicates,
)


@tool
def get_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Retrieve the details of a financial transaction.

    Use this when you need to understand a transaction before
    deciding which financial checks are relevant.
    """
    return analyze_transaction(transaction_id)


@tool
def check_historical_spending(
    vendor: str,
    transaction_id: str,
) -> Dict[str, Any]:
    """
    Compare a transaction against the vendor's historical spending.

    Use this when investigating whether the transaction amount
    is unusual compared with previous spending.
    """
    return analyze_historical_spending(
        vendor,
        transaction_id,
    )


@tool
def check_invoice_match(transaction_id: str) -> Dict[str, Any]:
    """
    Compare a transaction amount with its associated invoice.

    Use this when checking whether the financial transaction
    is supported by matching invoice evidence.
    """
    return match_invoice(transaction_id)


@tool
def check_duplicate_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Check whether a transaction may be duplicated.

    Use this when investigating potential duplicate payments.
    """
    return detect_duplicates(transaction_id)


SYSTEM_PROMPT = """
You are FinPilot, an AI financial investigation agent.

Your job is to investigate financial exceptions using reliable
deterministic tools.

IMPORTANT RULES:

1. Never invent financial evidence.
2. Never perform financial calculations yourself when a tool can
   provide the calculation.
3. Use tools to gather evidence.
4. You may call multiple tools when necessary.
5. Clearly distinguish evidence from interpretation.
6. If evidence is insufficient, say so.
7. Never approve payments.
8. Never move money.
9. Never modify accounting records.
10. Never close a financial period.
11. Consequential financial decisions must remain with a human.

When investigating a transaction:

1. First understand the transaction.
2. Determine which additional checks are relevant.
3. Call the appropriate financial tools.
4. Combine the evidence.
5. Explain why the transaction may require attention.
6. Recommend a next step for human review.

The deterministic Python tools are the source of truth for
financial calculations.
"""


def create_finpilot_agent():
    """
    Create the FinPilot tool-using AI agent.
    """

    llm = create_llm()

    return create_agent(
        model=llm,
        tools=[
            get_transaction,
            check_historical_spending,
            check_invoice_match,
            check_duplicate_transaction,
        ],
        system_prompt=SYSTEM_PROMPT,
    )


finpilot_agent = create_finpilot_agent()