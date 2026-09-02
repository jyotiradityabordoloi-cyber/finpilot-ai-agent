from typing import TypedDict, List, Dict, Any, Optional


class InvestigationState(TypedDict, total=False):
    # User request
    user_request: str

    # Investigation target
    transaction_id: Optional[str]
    vendor: Optional[str]

    # Financial information
    transaction_amount: Optional[float]
    historical_average: Optional[float]
    invoice_amount: Optional[float]
    difference: Optional[float]

    # Investigation results
    finding_type: Optional[str]
    severity: Optional[str]
    confidence: Optional[float]

    # Evidence collected during investigation
    evidence: List[Dict[str, Any]]

    # Agent execution information
    tools_called: List[str]
    investigation_steps: List[str]

    # Final result
    finding: Optional[str]
    recommendation: Optional[str]

    # Human review
    status: Optional[str]