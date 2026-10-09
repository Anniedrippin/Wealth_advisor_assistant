import re
from typing import Dict, Any, Tuple, Optional
from app.logging_config import logger
from app.models.advisory import AdvisoryInsight


FORBIDDEN_PATTERNS = [
    r"guaranteed\s+return",
    r"risk-free\s+profit",
    r"100%\s+safe\s+investment",
    r"buy\s+this\s+stock",
    r"sell\s+this\s+stock"
]


class GuardrailValidator:
    """Validation layer enforcing financial safety, compliance, and schema sanity."""

    def validate(
        self,
        insights_dict: Dict[str, Any],
        client_id: str,
        request_id: str
    ) -> Tuple[bool, Optional[str]]:
        logger.info("Guardrail Validator checking advisory insights", extra={"request_id": request_id, "agent": "validator", "event": "start"})

        try:
            insight = AdvisoryInsight(**insights_dict)
        except Exception as e:
            err = f"Schema validation error: {e}"
            logger.warning(err, extra={"request_id": request_id, "agent": "validator"})
            return False, err

        # 1. Bounded recommendation count
        if len(insight.recommendations) == 0 or len(insight.recommendations) > 10:
            err = f"Invalid recommendation count: {len(insight.recommendations)}. Must be between 1 and 10."
            logger.warning(err, extra={"request_id": request_id, "agent": "validator"})
            return False, err

        # 2. Risk level sanity check
        if insight.overall_risk not in ["LOW", "MEDIUM", "HIGH"]:
            err = f"Invalid risk level: {insight.overall_risk}"
            logger.warning(err, extra={"request_id": request_id, "agent": "validator"})
            return False, err

        # 3. Compliance text check for forbidden guarantee phrases
        recs_text = " ".join([r.recommendation for r in insight.recommendations])
        full_text = f"{insight.executive_summary} {' '.join(insight.key_findings)} {recs_text}"
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                err = f"Compliance violation: text contains forbidden guarantee pattern '{pattern}'"
                logger.warning(err, extra={"request_id": request_id, "agent": "validator"})
                return False, err

        logger.info("Guardrail Validator passed successfully", extra={"request_id": request_id, "agent": "validator", "event": "passed"})
        return True, None
