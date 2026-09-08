from typing import TypedDict, List, Dict, Any, Optional


class Evidence(TypedDict, total=False):
    """Evidence collected during a financial investigation."""

    type: str
    description: str
    value: Any


class InvestigationFinding(TypedDict, total=False):
    """Structured finding produced by FinPilot."""

    title: str
    severity: str
    summary: str
    evidence: List[Evidence]
    recommendation: str
    confidence: float
    requires_human_review: bool


class InvestigationState(TypedDict, total=False):
    """State passed between FinPilot investigation steps."""

    user_request: str

    transaction_id: Optional[str]
    vendor: Optional[str]
    transaction_amount: Optional[float]

    historical_average: Optional[float]
    invoice_amount: Optional[float]
    difference: Optional[float]

    finding_type: Optional[str]
    severity: Optional[str]
    confidence: Optional[float]

    evidence: List[Evidence]
    tools_called: List[str]
    investigation_steps: List[str]

    finding: Optional[InvestigationFinding]

    recommendation: Optional[str]
    status: Optional[str]