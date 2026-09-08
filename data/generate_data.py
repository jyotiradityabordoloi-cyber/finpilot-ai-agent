from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).parent


def create_transactions() -> pd.DataFrame:
    """Create synthetic transaction data for FinPilot."""

    transactions = [
        # Normal AWS transactions
        ["TXN-1001", "2026-05-05", "AWS", "Cloud Infrastructure", 12200, "INV-1001"],
        ["TXN-1002", "2026-06-05", "AWS", "Cloud Infrastructure", 13100, "INV-1002"],
        ["TXN-1003", "2026-07-05", "AWS", "Cloud Infrastructure", 13600, "INV-1003"],

        # Deliberate anomaly: unusually high amount
        ["TXN-1004", "2026-08-05", "AWS", "Cloud Infrastructure", 87500, "INV-1004"],

        # Normal Slack transactions
        ["TXN-1005", "2026-05-10", "Slack", "Software", 8500, "INV-1005"],
        ["TXN-1006", "2026-06-10", "Slack", "Software", 8500, "INV-1006"],
        ["TXN-1007", "2026-07-10", "Slack", "Software", 9000, "INV-1007"],
        ["TXN-1008", "2026-08-10", "Slack", "Software", 8800, "INV-1008"],

        # Normal office supplies
        ["TXN-1009", "2026-07-15", "Office Depot", "Office Supplies", 4200, "INV-1009"],
        ["TXN-1010", "2026-08-15", "Office Depot", "Office Supplies", 4500, "INV-1010"],

        # Deliberate duplicate
        ["TXN-1011", "2026-08-18", "Adobe", "Software", 15000, "INV-1011"],
        ["TXN-1012", "2026-08-18", "Adobe", "Software", 15000, "INV-1011"],
    ]

    return pd.DataFrame(
        transactions,
        columns=[
            "transaction_id",
            "date",
            "vendor",
            "category",
            "amount",
            "invoice_id",
        ],
    )


def create_invoices() -> pd.DataFrame:
    """Create synthetic invoice data."""

    invoices = [
        ["INV-1001", "2026-05-04", "AWS", 12200],
        ["INV-1002", "2026-06-04", "AWS", 13100],
        ["INV-1003", "2026-07-04", "AWS", 13600],

        # Deliberate mismatch with TXN-1004
        ["INV-1004", "2026-08-04", "AWS", 53100],

        ["INV-1005", "2026-05-09", "Slack", 8500],
        ["INV-1006", "2026-06-09", "Slack", 8500],
        ["INV-1007", "2026-07-09", "Slack", 9000],
        ["INV-1008", "2026-08-09", "Slack", 8800],

        ["INV-1009", "2026-07-14", "Office Depot", 4200],
        ["INV-1010", "2026-08-14", "Office Depot", 4500],

        ["INV-1011", "2026-08-17", "Adobe", 15000],
    ]

    return pd.DataFrame(
        invoices,
        columns=[
            "invoice_id",
            "invoice_date",
            "vendor",
            "invoice_amount",
        ],
    )


def create_ground_truth() -> pd.DataFrame:
    """Define known issues for evaluation."""

    ground_truth = [
        ["TXN-1004", True, True, "HIGH", "Historical anomaly + invoice mismatch"],
        ["TXN-1011", True, False, "HIGH", "Potential duplicate payment"],
        ["TXN-1012", True, False, "HIGH", "Potential duplicate payment"],
    ]

    return pd.DataFrame(
        ground_truth,
        columns=[
            "transaction_id",
            "is_exception",
            "invoice_mismatch",
            "expected_severity",
            "reason",
        ],
    )


def main() -> None:
    """Generate all synthetic FinPilot datasets."""

    transactions = create_transactions()
    invoices = create_invoices()
    ground_truth = create_ground_truth()

    transactions.to_csv(DATA_DIR / "transactions.csv", index=False)
    invoices.to_csv(DATA_DIR / "invoices.csv", index=False)
    ground_truth.to_csv(DATA_DIR / "ground_truth.csv", index=False)

    print("FinPilot synthetic dataset created.")
    print(f"Transactions: {len(transactions)}")
    print(f"Invoices: {len(invoices)}")
    print(f"Ground-truth exceptions: {len(ground_truth)}")


if __name__ == "__main__":
    main()