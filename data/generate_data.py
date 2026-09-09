from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).parent


def create_transactions() -> pd.DataFrame:
    """
    Create a controlled synthetic transaction dataset.

    The dataset contains:
    - Normal recurring transactions
    - Moderate spending changes
    - Legitimate spending spikes
    - Historical anomalies
    - Duplicate payments
    - Similar but legitimate transactions
    - Invoice mismatches
    - Missing invoices
    - New vendors
    """

    transactions = []

    # ---------------------------------------------------------
    # Normal recurring vendor activity
    # ---------------------------------------------------------

    normal_vendors = [
        ("AWS", "Cloud Infrastructure", [12200, 13100, 13600, 13800]),
        ("Slack", "Software", [8500, 8500, 9000, 8800]),
        ("Office Depot", "Office Supplies", [4200, 4500, 4300, 4400]),
        ("Atlassian", "Software", [7200, 7300, 7400, 7500]),
        ("HubSpot", "Marketing", [11000, 11200, 11500, 11400]),
        ("Zoom", "Software", [5000, 5100, 5200, 5300]),
        ("Canva", "Software", [3200, 3300, 3400, 3500]),
        ("Deloitte", "Professional Services", [25000, 25500, 26000, 26500]),
    ]

    transaction_counter = 1001
    invoice_counter = 1001

    months = [
        ("2026-05-05", "2026-05-04"),
        ("2026-06-05", "2026-06-04"),
        ("2026-07-05", "2026-07-04"),
        ("2026-08-05", "2026-08-04"),
    ]

    for vendor, category, amounts in normal_vendors:

        for index, (transaction_date, invoice_date) in enumerate(months):

            amount = amounts[index]

            transactions.append(
                [
                    f"TXN-{transaction_counter}",
                    transaction_date,
                    vendor,
                    category,
                    amount,
                    f"INV-{invoice_counter}",
                    "normal_recurring",
                ]
            )

            transaction_counter += 1
            invoice_counter += 1

    # ---------------------------------------------------------
    # Moderate spending increase
    # Expected: NORMAL
    # ---------------------------------------------------------

    transactions.append(
        [
            "TXN-1050",
            "2026-08-12",
            "Notion",
            "Software",
            9000,
            "INV-1050",
            "moderate_spending_increase",
        ]
    )

    # ---------------------------------------------------------
    # Legitimate large spending spike
    # Expected: NORMAL
    #
    # This is intentionally difficult for a simple anomaly rule.
    # ---------------------------------------------------------

    transactions.append(
        [
            "TXN-1051",
            "2026-08-13",
            "AWS",
            "Cloud Infrastructure",
            45000,
            "INV-1051",
            "legitimate_spending_spike",
        ]
    )

    # ---------------------------------------------------------
    # Extreme unexplained spending
    # Expected: EXCEPTION / HIGH
    # ---------------------------------------------------------

    transactions.append(
        [
            "TXN-1052",
            "2026-08-14",
            "AWS",
            "Cloud Infrastructure",
            87500,
            "INV-1052",
            "extreme_spending_anomaly",
        ]
    )

    # ---------------------------------------------------------
    # Exact duplicate payment
    # Expected: EXCEPTION / HIGH
    # ---------------------------------------------------------

    transactions.append(
        [
            "TXN-1053",
            "2026-08-15",
            "Adobe",
            "Software",
            15000,
            "INV-1053",
            "duplicate_payment",
        ]
    )

    transactions.append(
        [
            "TXN-1054",
            "2026-08-15",
            "Adobe",
            "Software",
            15000,
            "INV-1053",
            "duplicate_payment",
        ]
    )

    # ---------------------------------------------------------
    # Similar but legitimate transactions
    # Expected: NORMAL
    #
    # Same vendor and similar amount, but different invoices.
    # ---------------------------------------------------------

    transactions.append(
        [
            "TXN-1055",
            "2026-08-16",
            "Microsoft",
            "Software",
            15000,
            "INV-1055",
            "similar_legitimate_transactions",
        ]
    )

    transactions.append(
        [
            "TXN-1056",
            "2026-08-20",
            "Microsoft",
            "Software",
            14950,
            "INV-1056",
            "similar_legitimate_transactions",
        ]
    )

    # ---------------------------------------------------------
    # Invoice mismatch
    # Expected: EXCEPTION / MEDIUM
    # ---------------------------------------------------------

    transactions.append(
        [
            "TXN-1057",
            "2026-08-18",
            "Dell",
            "Hardware",
            25000,
            "INV-1057",
            "invoice_mismatch",
        ]
    )

    # ---------------------------------------------------------
    # Missing invoice
    # Expected: EXCEPTION / MEDIUM
    # ---------------------------------------------------------

    transactions.append(
        [
            "TXN-1058",
            "2026-08-19",
            "Amazon Business",
            "Office Supplies",
            7800,
            "INV-MISSING-1058",
            "missing_invoice",
        ]
    )

    # ---------------------------------------------------------
    # New vendor with no history
    # Expected: REVIEW_REQUIRED
    # ---------------------------------------------------------

    transactions.append(
        [
            "TXN-1059",
            "2026-08-21",
            "NewVendor Ltd",
            "Professional Services",
            18000,
            "INV-1059",
            "new_vendor",
        ]
    )

    return pd.DataFrame(
        transactions,
        columns=[
            "transaction_id",
            "date",
            "vendor",
            "category",
            "amount",
            "invoice_id",
            "scenario",
        ],
    )


def create_invoices() -> pd.DataFrame:
    """Create invoice records for the synthetic transactions."""

    transactions = create_transactions()

    invoices = []

    for _, transaction in transactions.iterrows():

        scenario = transaction["scenario"]

        # Missing invoice scenario intentionally has no invoice.
        if scenario == "missing_invoice":
            continue

        invoice_amount = float(transaction["amount"])

        # Intentional invoice mismatch.
        if scenario == "invoice_mismatch":
            invoice_amount = 21500

        invoices.append(
            [
                transaction["invoice_id"],
                transaction["date"],
                transaction["vendor"],
                invoice_amount,
            ]
        )

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
    """
    Define expected outcomes for evaluation.

    Expected states:
    - NORMAL
    - EXCEPTION
    - REVIEW_REQUIRED
    """

    ground_truth = [
        ["TXN-1050", "NORMAL", "MEDIUM", "Moderate spending increase"],
        [
            "TXN-1051",
            "NORMAL",
            "NORMAL",
            "Legitimate large spending spike with supporting invoice",
        ],
        [
            "TXN-1052",
            "EXCEPTION",
            "HIGH",
            "Extreme unexplained spending",
        ],
        [
            "TXN-1053",
            "EXCEPTION",
            "HIGH",
            "Potential duplicate payment",
        ],
        [
            "TXN-1054",
            "EXCEPTION",
            "HIGH",
            "Potential duplicate payment",
        ],
        [
            "TXN-1055",
            "NORMAL",
            "NORMAL",
            "Similar transaction with separate invoice",
        ],
        [
            "TXN-1056",
            "NORMAL",
            "NORMAL",
            "Similar transaction with separate invoice",
        ],
        [
            "TXN-1057",
            "EXCEPTION",
            "MEDIUM",
            "Invoice amount mismatch",
        ],
        [
            "TXN-1058",
            "EXCEPTION",
            "MEDIUM",
            "Missing invoice documentation",
        ],
        [
            "TXN-1059",
            "REVIEW_REQUIRED",
            "MEDIUM",
            "New vendor with insufficient history",
        ],
    ]

    return pd.DataFrame(
        ground_truth,
        columns=[
            "transaction_id",
            "expected_state",
            "expected_severity",
            "reason",
        ],
    )


def main() -> None:
    """Generate all FinPilot synthetic datasets."""

    transactions = create_transactions()
    invoices = create_invoices()
    ground_truth = create_ground_truth()

    transactions.to_csv(
        DATA_DIR / "transactions.csv",
        index=False,
    )

    invoices.to_csv(
        DATA_DIR / "invoices.csv",
        index=False,
    )

    ground_truth.to_csv(
        DATA_DIR / "ground_truth.csv",
        index=False,
    )

    print("FinPilot robust synthetic dataset created.")
    print(f"Transactions: {len(transactions)}")
    print(f"Invoices: {len(invoices)}")
    print(f"Ground-truth cases: {len(ground_truth)}")


if __name__ == "__main__":
    main()