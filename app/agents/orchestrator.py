import uuid
import time
from typing import Dict, Any, Optional
from app.graph.workflow import advisor_workflow
from app.graph.state import AdvisorState
from app.logging_config import logger
from app.repositories.approval_repository import ApprovalRepository


class OrchestratorAgent:
    """High-level Orchestrator Agent coordinating state machine execution and persistence."""

    def __init__(self, repository: Optional[ApprovalRepository] = None):
        self.repository = repository or ApprovalRepository()

    async def run_analysis_pipeline(self, client_input: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        req_id = request_id or f"req_{uuid.uuid4().hex[:10]}"
        client_id = client_input.get("client_id", "UNKNOWN")

        start_time = time.time()
        logger.info(
            f"Orchestrator starting pipeline for client {client_id}",
            extra={"request_id": req_id, "agent": "orchestrator", "event": "start_pipeline", "client_id": client_id}
        )

        initial_state: AdvisorState = {
            "request_id": req_id,
            "client_id": client_id,
            "client_input": client_input,
            "crm_context_available": False,
            "anomalies": [],
            "historical_memories": [],
            "validation_passed": False,
            "requires_human_review": False,
            "status": "processing",
            "execution_logs": ["Orchestrator initialized workflow."]
        }

        try:
            final_state = await advisor_workflow.ainvoke(initial_state)

            status = final_state.get("status", "completed")
            requires_hitl = final_state.get("requires_human_review", False)

            # Save state to SQLite database
            self.repository.save_request(
                request_id=req_id,
                client_id=client_id,
                status=status,
                input_data=client_input,
                analysis_data=final_state.get("analysis"),
                insights_data=final_state.get("insights"),
                requires_human_review=requires_hitl
            )

            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Orchestrator completed pipeline for {req_id} with status '{status}' in {latency_ms}ms",
                extra={"request_id": req_id, "agent": "orchestrator", "event": "pipeline_complete", "status": status, "latency_ms": latency_ms}
            )

            return final_state

        except Exception as e:
            logger.error(
                f"Pipeline execution error for {req_id}: {e}",
                extra={"request_id": req_id, "agent": "orchestrator", "event": "pipeline_error", "error": str(e)}
            )
            self.repository.save_request(
                request_id=req_id,
                client_id=client_id,
                status="FAILED",
                input_data=client_input
            )
            raise e
