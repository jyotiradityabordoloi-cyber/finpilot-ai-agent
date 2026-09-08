from pathlib import Path
from typing import Dict, Any

import pandas as pd


# Project data directory
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def analyze_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Retrieve and analyze a financial transaction.
    """

    transactions = pd.read_csv(DATA_DIR / "transactions.csv")

    matches = transactions[
        transactions["transaction_id"] == transaction_id
    ]

    if matches.empty:
        return {
            "status": "error",
            "transaction_id": transaction_id,
            "message": f"Transaction {transaction_id} not found.",
        }

    transaction = matches.iloc[0]

    return {
        "status": "success",
        "transaction_id": transaction["transaction_id"],
        "date": transaction["date"],
        "vendor": transaction["vendor"],
        "category": transaction["category"],
        "amount": float(transaction["amount"]),
        "invoice_id": transaction["invoice_id"],
    }


def detect_duplicates(transaction_id: str) -> Dict[str, Any]:
    """
    Check whether a transaction may be duplicated.
    """

    transactions = pd.read_csv(DATA_DIR / "transactions.csv")

    matches = transactions[
        transactions["transaction_id"] == transaction_id
    ]

    if matches.empty:
        return {
            "status": "error",
            "transaction_id": transaction_id,
            "message": f"Transaction {transaction_id} not found.",
        }

    transaction = matches.iloc[0]

    possible_duplicates = transactions[
        (transactions["transaction_id"] != transaction_id)
        & (transactions["vendor"] == transaction["vendor"])
        & (transactions["amount"] == transaction["amount"])
        & (transactions["invoice_id"] == transaction["invoice_id"])
    ]

    return {
        "status": "success",
        "transaction_id": transaction_id,
        "possible_duplicate": not possible_duplicates.empty,
        "duplicate_transaction_ids": possible_duplicates[
            "transaction_id"
        ].tolist(),
    }


def match_invoice(transaction_id: str) -> Dict[str, Any]:
    """
    Match a transaction against its associated invoice.
    """

    transactions = pd.read_csv(DATA_DIR / "transactions.csv")
    invoices = pd.read_csv(DATA_DIR / "invoices.csv")

    transaction_matches = transactions[
        transactions["transaction_id"] == transaction_id
    ]

    if transaction_matches.empty:
        return {
            "status": "error",
            "transaction_id": transaction_id,
            "message": f"Transaction {transaction_id} not found.",
        }

    transaction = transaction_matches.iloc[0]

    invoice_matches = invoices[
        invoices["invoice_id"] == transaction["invoice_id"]
    ]

    if invoice_matches.empty:
        return {
            "status": "missing_invoice",
            "transaction_id": transaction_id,
            "invoice_id": transaction["invoice_id"],
            "transaction_amount": float(transaction["amount"]),
        }

    invoice = invoice_matches.iloc[0]

    transaction_amount = float(transaction["amount"])
    invoice_amount = float(invoice["invoice_amount"])

    difference = transaction_amount - invoice_amount

    return {
        "status": "success",
        "transaction_id": transaction_id,
        "invoice_id": invoice["invoice_id"],
        "transaction_amount": round(transaction_amount, 2),
        "invoice_amount": round(invoice_amount, 2),
        "difference": round(difference, 2),
        "invoice_matches": difference == 0,
    }


def analyze_historical_spending(
    vendor: str,
    current_transaction_id: str,
) -> Dict[str, Any]:
    """
    Compare a transaction against the vendor's previous spending history.
    """

    transactions = pd.read_csv(DATA_DIR / "transactions.csv")

    current_matches = transactions[
        transactions["transaction_id"] == current_transaction_id
    ]

    if current_matches.empty:
        return {
            "status": "error",
            "transaction_id": current_transaction_id,
            "message": (
                f"Transaction {current_transaction_id} not found."
            ),
        }

    current = current_matches.iloc[0]

    if current["vendor"] != vendor:
        return {
            "status": "error",
            "transaction_id": current_transaction_id,
            "message": "Vendor does not match transaction.",
        }

    current_date = pd.to_datetime(current["date"])
    current_amount = float(current["amount"])

    vendor_transactions = transactions[
        (transactions["vendor"] == vendor)
        & (pd.to_datetime(transactions["date"]) < current_date)
    ]

    if vendor_transactions.empty:
        return {
            "status": "insufficient_history",
            "vendor": vendor,
            "transaction_id": current_transaction_id,
            "current_amount": round(current_amount, 2),
            "historical_transactions": 0,
        }

    historical_average = float(
        vendor_transactions["amount"].mean()
    )

    difference = current_amount - historical_average

    deviation_percentage = (
        difference / historical_average * 100
        if historical_average
        else 0
    )

    if deviation_percentage >= 200:
        risk_level = "HIGH"
    elif deviation_percentage >= 50:
        risk_level = "MEDIUM"
    else:
        risk_level = "NORMAL"

    return {
        "status": "success",
        "transaction_id": current_transaction_id,
        "vendor": vendor,
        "current_amount": round(current_amount, 2),
        "historical_average": round(historical_average, 2),
        "difference": round(difference, 2),
        "deviation_percentage": round(deviation_percentage, 2),
        "risk_level": risk_level,
        "historical_transactions": len(vendor_transactions),
    }


def check_missing_documentation(
    transaction_id: str,
) -> Dict[str, Any]:
    """
    Check whether supporting documentation exists.
    """

    transactions = pd.read_csv(DATA_DIR / "transactions.csv")
    invoices = pd.read_csv(DATA_DIR / "invoices.csv")

    matches = transactions[
        transactions["transaction_id"] == transaction_id
    ]

    if matches.empty:
        return {
            "status": "error",
            "transaction_id": transaction_id,
            "message": f"Transaction {transaction_id} not found.",
        }

    transaction = matches.iloc[0]

    invoice_matches = invoices[
        invoices["invoice_id"] == transaction["invoice_id"]
    ]

    return {
        "status": "success",
        "transaction_id": transaction_id,
        "invoice_id": transaction["invoice_id"],
        "documentation_available": not invoice_matches.empty,
    }


def analyze_vendor(vendor: str) -> Dict[str, Any]:
    """
    Analyze vendor activity and spending patterns.
    """

    transactions = pd.read_csv(DATA_DIR / "transactions.csv")

    vendor_transactions = transactions[
        transactions["vendor"].str.lower() == vendor.lower()
    ]

    if vendor_transactions.empty:
        return {
            "status": "vendor_not_found",
            "vendor": vendor,
        }

    total_spend = float(vendor_transactions["amount"].sum())
    average_transaction = float(
        vendor_transactions["amount"].mean()
    )

    return {
        "status": "success",
        "vendor": vendor,
        "transaction_count": len(vendor_transactions),
        "total_spend": round(total_spend, 2),
        "average_transaction": round(average_transaction, 2),
    }

def investigate_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Run a multi-signal investigation for a transaction.

    This function combines deterministic financial checks into a
    structured investigation result that can later be consumed
    by the FinPilot AI agent.
    """

    transaction_result = analyze_transaction(transaction_id)

    if transaction_result["status"] != "success":
        return transaction_result

    vendor = transaction_result["vendor"]

    historical_result = analyze_historical_spending(
        vendor,
        transaction_id,
    )

    invoice_result = match_invoice(transaction_id)

    duplicate_result = detect_duplicates(transaction_id)

    evidence = []

    if historical_result.get("risk_level") in {"HIGH", "MEDIUM"}:
        evidence.append(
            {
                "type": "historical_spending",
                "risk_level": historical_result["risk_level"],
                "deviation_percentage": historical_result[
                    "deviation_percentage"
                ],
                "difference": historical_result["difference"],
            }
        )

    if invoice_result.get("invoice_matches") is False:
        evidence.append(
            {
                "type": "invoice_mismatch",
                "transaction_amount": invoice_result[
                    "transaction_amount"
                ],
                "invoice_amount": invoice_result["invoice_amount"],
                "difference": invoice_result["difference"],
            }
        )

    if duplicate_result.get("possible_duplicate"):
        evidence.append(
            {
                "type": "possible_duplicate",
                "duplicate_transaction_ids": duplicate_result[
                    "duplicate_transaction_ids"
                ],
            }
        )

    if len(evidence) >= 2:
        severity = "HIGH"
    elif len(evidence) == 1:
        severity = "MEDIUM"
    else:
        severity = "NORMAL"

    if evidence:
        status = "exception_detected"
    else:
        status = "no_exception"

    return {
        "status": status,
        "transaction_id": transaction_id,
        "vendor": vendor,
        "amount": transaction_result["amount"],
        "severity": severity,
        "evidence": evidence,
        "checks": {
            "transaction_analysis": transaction_result,
            "historical_spending": historical_result,
            "invoice_matching": invoice_result,
            "duplicate_detection": duplicate_result,
        },
    }

def create_finding(investigation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert investigation evidence into a structured financial finding.

    This layer uses deterministic rules to summarize known evidence.
    The AI agent can later improve the explanation and reasoning,
    but it should not replace the underlying financial calculations.
    """

    if investigation.get("status") != "exception_detected":
        return {
            "status": "no_exception",
            "finding": None,
        }

    transaction_id = investigation["transaction_id"]
    vendor = investigation["vendor"]
    amount = investigation["amount"]
    severity = investigation["severity"]
    evidence = investigation["evidence"]

    evidence_descriptions = []

    has_historical_anomaly = False
    has_invoice_mismatch = False
    has_duplicate = False

    for item in evidence:

        if item["type"] == "historical_spending":
            has_historical_anomaly = True

            evidence_descriptions.append(
                "Spending is significantly above the vendor's "
                "historical average."
            )

        elif item["type"] == "invoice_mismatch":
            has_invoice_mismatch = True

            evidence_descriptions.append(
                "The transaction amount does not match "
                "the available invoice."
            )

        elif item["type"] == "possible_duplicate":
            has_duplicate = True

            evidence_descriptions.append(
                "Another transaction has matching vendor, "
                "amount, and invoice information."
            )

    if has_historical_anomaly and has_invoice_mismatch:
        title = f"{vendor} transaction requires review"

        summary = (
            f"Transaction {transaction_id} for ₹{amount:,.2f} "
            f"shows both unusual historical spending and an "
            f"invoice mismatch."
        )

        recommendation = (
            "Review the transaction and supporting documentation "
            "before reconciliation."
        )

    elif has_duplicate:
        title = f"Potential duplicate payment: {vendor}"

        summary = (
            f"Transaction {transaction_id} appears to have a "
            "matching transaction."
        )

        recommendation = (
            "Review the matching transaction before processing "
            "or reconciling the payment."
        )

    elif has_historical_anomaly:
        title = f"Unusual {vendor} spending"

        summary = (
            f"Transaction {transaction_id} is significantly "
            "above the vendor's historical spending pattern."
        )

        recommendation = (
            "Review the transaction and confirm the business reason "
            "for the increase."
        )

    elif has_invoice_mismatch:
        title = f"Invoice mismatch: {vendor}"

        summary = (
            f"Transaction {transaction_id} does not match "
            "the available invoice."
        )

        recommendation = (
            "Review the invoice and transaction details "
            "before reconciliation."
        )

    else:
        title = f"Financial exception: {transaction_id}"

        summary = (
            f"Transaction {transaction_id} requires additional review."
        )

        recommendation = (
            "Review the available evidence before reconciliation."
        )

    finding = {
        "title": title,
        "severity": severity,
        "summary": summary,
        "evidence": evidence,
        "recommendation": recommendation,
        "confidence": 0.95,
        "requires_human_review": True,
    }

    return {
        "status": "finding_created",
        "transaction_id": transaction_id,
        "finding": finding,
    }