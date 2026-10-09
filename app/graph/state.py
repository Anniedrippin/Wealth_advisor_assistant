from typing import TypedDict, Optional, List, Dict, Any


class AdvisorState(TypedDict, total=False):
    request_id: str
    client_id: str
    client_input: Dict[str, Any]
    normalized_client_data: Optional[Dict[str, Any]]
    crm_context: Optional[Dict[str, Any]]
    crm_context_available: bool
    analysis: Optional[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    historical_memories: List[str]
    insights: Optional[Dict[str, Any]]
    validation_passed: bool
    validation_error: Optional[str]
    requires_human_review: bool
    status: str
    execution_logs: List[str]
    error: Optional[str]
