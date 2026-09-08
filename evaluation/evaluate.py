from pathlib import Path
import sys

import pandas as pd


# ---------------------------------------------------------
# Project configuration
# ---------------------------------------------------------

# evaluation/evaluate.py
#        ↓
# finpilot/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allow Python to import the agents package
sys.path.insert(0, str(PROJECT_ROOT))

from agents.tools import investigate_transaction


DATA_DIR = PROJECT_ROOT / "data"


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

def evaluate_exception_detection() -> None:
    """
    Compare FinPilot's investigation results against
    the known ground truth dataset.
    """

    ground_truth = pd.read_csv(
        DATA_DIR / "ground_truth.csv"
    )

    transactions = pd.read_csv(
        DATA_DIR / "transactions.csv"
    )

    results = []

    # Run FinPilot against every transaction
    for _, transaction in transactions.iterrows():

        transaction_id = transaction["transaction_id"]

        investigation = investigate_transaction(
            transaction_id
        )

        # What FinPilot predicted
        predicted_exception = (
            investigation.get("status")
            == "exception_detected"
        )

        # What the ground truth says
        ground_truth_match = ground_truth[
            ground_truth["transaction_id"]
            == transaction_id
        ]

        actual_exception = (
            bool(ground_truth_match["is_exception"].any())
            if not ground_truth_match.empty
            else False
        )

        results.append(
            {
                "transaction_id": transaction_id,
                "predicted_exception": predicted_exception,
                "actual_exception": actual_exception,
            }
        )

    results_df = pd.DataFrame(results)

    # -----------------------------------------------------
    # Confusion matrix
    # -----------------------------------------------------

    true_positive = (
        (results_df["predicted_exception"])
        & (results_df["actual_exception"])
    ).sum()

    false_positive = (
        (results_df["predicted_exception"])
        & (~results_df["actual_exception"])
    ).sum()

    false_negative = (
        (~results_df["predicted_exception"])
        & (results_df["actual_exception"])
    ).sum()

    true_negative = (
        (~results_df["predicted_exception"])
        & (~results_df["actual_exception"])
    ).sum()

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    precision = (
        true_positive
        / (true_positive + false_positive)
        if true_positive + false_positive
        else 0
    )

    recall = (
        true_positive
        / (true_positive + false_negative)
        if true_positive + false_negative
        else 0
    )

    accuracy = (
        (true_positive + true_negative)
        / len(results_df)
        if len(results_df)
        else 0
    )

    false_positive_rate = (
        false_positive
        / (false_positive + true_negative)
        if false_positive + true_negative
        else 0
    )

    # -----------------------------------------------------
    # Print evaluation report
    # -----------------------------------------------------

    print()
    print("========================================")
    print("        FinPilot Evaluation")
    print("========================================")

    print()
    print(f"Transactions evaluated : {len(results_df)}")

    print()
    print("Confusion Matrix")
    print("----------------")
    print(f"True positives         : {true_positive}")
    print(f"False positives        : {false_positive}")
    print(f"False negatives        : {false_negative}")
    print(f"True negatives         : {true_negative}")

    print()
    print("Metrics")
    print("----------------")
    print(f"Precision              : {precision:.2%}")
    print(f"Recall                 : {recall:.2%}")
    print(f"Accuracy               : {accuracy:.2%}")
    print(f"False positive rate    : {false_positive_rate:.2%}")

    print()
    print("Transaction Results")
    print("----------------")

    print(
        results_df.to_string(index=False)
    )

    print()
    print("========================================")


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    evaluate_exception_detection()