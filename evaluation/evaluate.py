from pathlib import Path
import sys

import pandas as pd


# ---------------------------------------------------------
# Project configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from agents.tools import investigate_transaction


DATA_DIR = PROJECT_ROOT / "data"


# ---------------------------------------------------------
# State mapping
# ---------------------------------------------------------

def get_predicted_state(investigation: dict) -> str:
    """
    Convert FinPilot's internal investigation status
    into a product-level state.
    """

    status = investigation.get("status")

    if status == "exception_detected":
        return "EXCEPTION"

    if status == "review_required":
        return "REVIEW_REQUIRED"

    if status == "no_exception":
        return "NORMAL"

    return "UNKNOWN"


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

def evaluate_state_classification() -> None:
    """
    Compare FinPilot predictions against ground truth.

    The evaluator measures:
    - State accuracy
    - Per-state performance
    - Incorrect classifications
    """

    ground_truth = pd.read_csv(
        DATA_DIR / "ground_truth.csv"
    )

    transactions = pd.read_csv(
        DATA_DIR / "transactions.csv"
    )

    results = []

    # -----------------------------------------------------
    # Run FinPilot against every transaction
    # -----------------------------------------------------

    for _, transaction in transactions.iterrows():

        transaction_id = transaction["transaction_id"]

        investigation = investigate_transaction(
            transaction_id
        )

        predicted_state = get_predicted_state(
            investigation
        )

        ground_truth_match = ground_truth[
            ground_truth["transaction_id"]
            == transaction_id
        ]

        if ground_truth_match.empty:
            expected_state = "UNKNOWN"
        else:
            expected_state = ground_truth_match.iloc[0][
                "expected_state"
            ]

        results.append(
            {
                "transaction_id": transaction_id,
                "predicted_state": predicted_state,
                "expected_state": expected_state,
            }
        )

    results_df = pd.DataFrame(results)

    # -----------------------------------------------------
    # Overall accuracy
    # -----------------------------------------------------

    correct = (
        results_df["predicted_state"]
        == results_df["expected_state"]
    ).sum()

    total = len(results_df)

    accuracy = (
        correct / total
        if total
        else 0
    )

    # -----------------------------------------------------
    # Per-state performance
    # -----------------------------------------------------

    states = [
        "NORMAL",
        "EXCEPTION",
        "REVIEW_REQUIRED",
    ]

    state_metrics = []

    for state in states:

        actual = (
            results_df["expected_state"] == state
        )

        predicted = (
            results_df["predicted_state"] == state
        )

        true_positive = (
            actual & predicted
        ).sum()

        actual_count = actual.sum()

        predicted_count = predicted.sum()

        recall = (
            true_positive / actual_count
            if actual_count
            else 0
        )

        precision = (
            true_positive / predicted_count
            if predicted_count
            else 0
        )

        state_metrics.append(
            {
                "state": state,
                "expected": actual_count,
                "predicted": predicted_count,
                "precision": precision,
                "recall": recall,
            }
        )

    metrics_df = pd.DataFrame(state_metrics)

    # -----------------------------------------------------
    # Incorrect classifications
    # -----------------------------------------------------

    incorrect = results_df[
        results_df["predicted_state"]
        != results_df["expected_state"]
    ]

    # -----------------------------------------------------
    # Print evaluation report
    # -----------------------------------------------------

    print()
    print("========================================")
    print("        FinPilot Evaluation")
    print("========================================")

    print()
    print(f"Transactions evaluated : {total}")
    print(f"Correct classifications : {correct}")
    print(f"Overall accuracy        : {accuracy:.2%}")

    print()
    print("State Performance")
    print("-----------------")

    for _, row in metrics_df.iterrows():

        print(
            f"{row['state']:<18}"
            f" Precision: {row['precision']:.2%}  "
            f"Recall: {row['recall']:.2%}"
        )

    print()
    print("Incorrect Classifications")
    print("-------------------------")

    if incorrect.empty:

        print("None 🎯")

    else:

        print(
            incorrect.to_string(
                index=False
            )
        )

    print()
    print("Transaction Results")
    print("-------------------")

    print(
        results_df.to_string(
            index=False
        )
    )

    print()
    print("========================================")


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    evaluate_state_classification()