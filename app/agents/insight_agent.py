import json
import time
from typing import Dict, Any, Optional, List
from app.config import settings
from app.logging_config import logger
from app.models.advisory import AdvisoryInsight, Recommendation
from app.models.transaction import Anomaly
from app.tools.base import MemoryTool
from app.tools.memory import ChromaMemoryTool, InMemoryFallbackTool


SYSTEM_PROMPT = """You are a senior Wealth Advisor AI Assistant.
Your job is to produce structured advisory insights based strictly on provided financial analysis, detected anomalies, CRM context, and historical client memory.

STRICT ADVISORY RULES:
1. NEVER invent transaction data, financial numbers, or client facts not present in the context.
2. NEVER override or ignore the provided deterministic anomaly detection results.
3. NEVER promise guaranteed investment returns, or recommend specific buy/sell stock trades. Frame all output as advisory insights for decision support (e.g. "Review emergency fund coverage", "Discuss portfolio allocation with a qualified advisor").
4. If CRM context or specific data is missing, explicitly note that it is unavailable.
5. Return ONLY a valid JSON object matching the requested schema. No markdown wrapping outside JSON.

JSON Schema format:
{
  "overall_risk": "LOW" | "MEDIUM" | "HIGH",
  "executive_summary": "Brief summary of client status",
  "key_findings": ["Finding 1", "Finding 2"],
  "recommendations": [
    {
      "priority": "HIGH" | "MEDIUM" | "LOW",
      "area": "Cash Flow" | "Emergency Fund" | "Risk Management" | "Goal Alignment",
      "recommendation": "Actionable advice",
      "reason": "Data-backed justification"
    }
  ],
  "follow_up_questions": ["Question 1"],
  "requires_human_review": true | false,
  "confidence": 0.95
}
"""


class InsightAgent:
    """Agent responsible for generating structured advisory insights using LLM or deterministic fallback."""

    def __init__(self, memory_tool: Optional[MemoryTool] = None):
        self.memory_tool = memory_tool or ChromaMemoryTool()
        self.fallback_memory_tool = InMemoryFallbackTool()

    async def execute(
        self,
        client_id: str,
        normalized_data: Dict[str, Any],
        analysis_dict: Dict[str, Any],
        anomalies_list: List[Dict[str, Any]],
        crm_context: Optional[Dict[str, Any]],
        request_id: str
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("Insight Agent started execution", extra={"request_id": request_id, "agent": "insight_agent", "event": "start"})

        # 1. Retrieve Historical Memories for Client
        memories: List[str] = []
        try:
            memories = await self.memory_tool.retrieve_memories(client_id=client_id)
            if not memories:
                memories = await self.fallback_memory_tool.retrieve_memories(client_id=client_id)
        except Exception as e:
            logger.error(f"Failed memory retrieval: {e}", extra={"request_id": request_id, "agent": "insight_agent", "error": str(e)})

        # 2. Try LLM Generation via Groq API (if key available)
        insight: Optional[AdvisoryInsight] = None
        used_llm = False

        if settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip():
            try:
                insight = await self._generate_groq_insight(
                    client_id=client_id,
                    normalized_data=normalized_data,
                    analysis_dict=analysis_dict,
                    anomalies_list=anomalies_list,
                    crm_context=crm_context,
                    memories=memories,
                    request_id=request_id
                )
                if insight:
                    used_llm = True
            except Exception as e:
                logger.warning(
                    f"Groq LLM call failed or produced malformed response: {e}. Falling back to deterministic advisory template.",
                    extra={"request_id": request_id, "agent": "insight_agent", "event": "llm_fallback", "error": str(e)}
                )

        # 3. Deterministic Fallback if LLM unavailable or failed
        if not insight:
            logger.info("Using deterministic advisory insight fallback generator", extra={"request_id": request_id, "agent": "insight_agent"})
            insight = self._generate_deterministic_fallback(
                client_id=client_id,
                normalized_data=normalized_data,
                analysis_dict=analysis_dict,
                anomalies_list=anomalies_list,
                crm_context=crm_context,
                memories=memories
            )

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Insight Agent complete. Risk: {insight.overall_risk}, Used LLM: {used_llm}, Latency: {latency_ms}ms",
            extra={
                "request_id": request_id,
                "agent": "insight_agent",
                "event": "complete",
                "overall_risk": insight.overall_risk,
                "used_llm": used_llm,
                "latency_ms": latency_ms
            }
        )

        # Store summary in long-term memory
        try:
            summary_text = f"Advisory Session for Client {client_id}: Risk level={insight.overall_risk}. Key findings: {'; '.join(insight.key_findings[:2])}"
            await self.memory_tool.store_memory(client_id=client_id, summary=summary_text)
            await self.fallback_memory_tool.store_memory(client_id=client_id, summary=summary_text)
        except Exception as e:
            logger.error(f"Failed storing memory: {e}", extra={"request_id": request_id, "error": str(e)})

        return {
            "insights": insight.model_dump(),
            "historical_memories": memories
        }

    async def _generate_groq_insight(
        self,
        client_id: str,
        normalized_data: Dict[str, Any],
        analysis_dict: Dict[str, Any],
        anomalies_list: List[Dict[str, Any]],
        crm_context: Optional[Dict[str, Any]],
        memories: List[str],
        request_id: str
    ) -> Optional[AdvisoryInsight]:
        import httpx

        prompt_payload = {
            "client_id": client_id,
            "financial_data": normalized_data,
            "analysis": analysis_dict,
            "detected_anomalies": anomalies_list,
            "crm_context": crm_context or "CRM context unavailable",
            "historical_memories": memories or "No previous memories found"
        }

        user_content = f"Analyze the following client financial data and generate structured advisory insights in JSON format:\n\n{json.dumps(prompt_payload, indent=2)}"

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        body = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
            if resp.status_code == 200:
                res_data = resp.json()
                content = res_data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                # Map anomalies back into parsed structure if omitted
                if "anomalies" not in parsed or not parsed["anomalies"]:
                    parsed["anomalies"] = anomalies_list
                return AdvisoryInsight(**parsed)
            else:
                logger.error(f"Groq API HTTP error {resp.status_code}: {resp.text}", extra={"request_id": request_id})
                return None

    def _generate_deterministic_fallback(
        self,
        client_id: str,
        normalized_data: Dict[str, Any],
        analysis_dict: Dict[str, Any],
        anomalies_list: List[Dict[str, Any]],
        crm_context: Optional[Dict[str, Any]],
        memories: List[str]
    ) -> AdvisoryInsight:
        income = analysis_dict.get("income", 0.0)
        expenses = analysis_dict.get("expenses", 0.0)
        expense_ratio = analysis_dict.get("expense_ratio", 0.0)
        net_cash_flow = analysis_dict.get("net_cash_flow", 0.0)
        savings_rate = analysis_dict.get("savings_rate", 0.0)

        high_severity_anomalies = [a for a in anomalies_list if a.get("severity") == "HIGH"]
        
        # Calculate Risk Tier Deterministically
        if high_severity_anomalies or expense_ratio > 0.85 or savings_rate < 0.10:
            overall_risk = "HIGH"
        elif expense_ratio > 0.60 or len(anomalies_list) > 0:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        key_findings = [
            f"Monthly income of ${income:,.2f} against expenses of ${expenses:,.2f} results in net cash flow of ${net_cash_flow:,.2f}.",
            f"Current expense ratio is {expense_ratio*100:.1f}%, leaving a savings rate of {savings_rate*100:.1f}%."
        ]

        if not crm_context:
            key_findings.append("Note: Additional CRM context was unavailable for this analysis.")

        recs: List[Recommendation] = []

        if high_severity_anomalies:
            for anom in high_severity_anomalies:
                recs.append(
                    Recommendation(
                        priority="HIGH",
                        area="Transaction Safety & Cash Flow",
                        recommendation=f"Review anomalous activity flagged for transaction/category: {anom.get('transaction_id')}.",
                        reason=anom.get("reason", "Anomalous transaction value detected.")
                    )
                )

        if expense_ratio > 0.70:
            recs.append(
                Recommendation(
                    priority="HIGH",
                    area="Expense Control",
                    recommendation="Review fixed vs discretionary expenses to lower monthly burn rate.",
                    reason=f"High expense ratio ({expense_ratio*100:.1f}%) reduces cash buffer."
                )
            )

        if savings_rate < 0.20:
            recs.append(
                Recommendation(
                    priority="MEDIUM",
                    area="Savings & Emergency Fund",
                    recommendation="Aim to allocate at least 20% of net monthly income toward liquid emergency reserves.",
                    reason=f"Current savings rate ({savings_rate*100:.1f}%) is below recommended threshold."
                )
            )

        if not recs:
            recs.append(
                Recommendation(
                    priority="LOW",
                    area="Wealth Maintenance",
                    recommendation="Maintain existing financial discipline and review long-term investment goals annually.",
                    reason="Client maintains healthy savings rate and balanced expense ratio."
                )
            )

        anomalies_objs = [Anomaly(**a) for a in anomalies_list]

        return AdvisoryInsight(
            overall_risk=overall_risk,
            executive_summary=f"Automated advisory analysis for client {client_id}. Overall financial risk profile is evaluated as {overall_risk}.",
            key_findings=key_findings,
            anomalies=anomalies_objs,
            recommendations=recs,
            follow_up_questions=[
                "Are there upcoming planned major capital expenditures?",
                "Has your primary financial goal shifted recently?"
            ],
            requires_human_review=(overall_risk == "HIGH" or len(high_severity_anomalies) > 0),
            confidence=0.85 if crm_context else 0.70
        )
