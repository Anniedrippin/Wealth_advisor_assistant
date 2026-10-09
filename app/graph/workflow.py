from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from app.graph.state import AdvisorState
from app.agents.data_fetcher import DataFetcherAgent
from app.agents.analyzer import AnalyzerAgent
from app.agents.insight_agent import InsightAgent
from app.agents.validator import GuardrailValidator
from app.logging_config import logger


# Instantiate agents
data_fetcher_agent = DataFetcherAgent()
analyzer_agent = AnalyzerAgent()
insight_agent = InsightAgent()
validator = GuardrailValidator()


async def data_fetcher_node(state: AdvisorState) -> AdvisorState:
    request_id = state["request_id"]
    client_input = state["client_input"]
    result = await data_fetcher_agent.execute(client_input, request_id)
    return {
        "client_id": result["client_id"],
        "normalized_client_data": result["normalized_client_data"],
        "crm_context": result["crm_context"],
        "crm_context_available": result["crm_context_available"],
        "execution_logs": state.get("execution_logs", []) + ["Data Fetcher completed."]
    }


def analyzer_node(state: AdvisorState) -> AdvisorState:
    request_id = state["request_id"]
    normalized_data = state["normalized_client_data"]
    result = analyzer_agent.execute(normalized_data, request_id)
    return {
        "analysis": result["analysis"],
        "anomalies": result["anomalies"],
        "execution_logs": state.get("execution_logs", []) + [f"Analyzer completed ({len(result['anomalies'])} anomalies)."]
    }


async def insight_node(state: AdvisorState) -> AdvisorState:
    request_id = state["request_id"]
    client_id = state["client_id"]
    normalized_data = state["normalized_client_data"]
    analysis = state["analysis"]
    anomalies = state["anomalies"]
    crm_context = state.get("crm_context")

    result = await insight_agent.execute(
        client_id=client_id,
        normalized_data=normalized_data,
        analysis_dict=analysis,
        anomalies_list=anomalies,
        crm_context=crm_context,
        request_id=request_id
    )

    return {
        "insights": result["insights"],
        "historical_memories": result["historical_memories"],
        "execution_logs": state.get("execution_logs", []) + ["Insight Agent completed."]
    }


def validator_node(state: AdvisorState) -> AdvisorState:
    request_id = state["request_id"]
    client_id = state["client_id"]
    insights = state["insights"]

    passed, error_msg = validator.validate(insights, client_id, request_id)

    if not passed:
        # If validation failed, fallback to deterministic generator
        logger.warning(f"Guardrail validation failed: {error_msg}. Applying deterministic fallback.", extra={"request_id": request_id})
        fallback_insight = insight_agent._generate_deterministic_fallback(
            client_id=client_id,
            normalized_data=state["normalized_client_data"],
            analysis_dict=state["analysis"],
            anomalies_list=state["anomalies"],
            crm_context=state.get("crm_context"),
            memories=state.get("historical_memories", [])
        )
        return {
            "insights": fallback_insight.model_dump(),
            "validation_passed": True,
            "validation_error": error_msg,
            "execution_logs": state.get("execution_logs", []) + [f"Validator corrected insights ({error_msg})."]
        }

    return {
        "validation_passed": True,
        "validation_error": None,
        "execution_logs": state.get("execution_logs", []) + ["Validator passed successfully."]
    }


def hitl_evaluator_node(state: AdvisorState) -> AdvisorState:
    insights = state["insights"]
    anomalies = state.get("anomalies", [])
    overall_risk = insights.get("overall_risk", "LOW")

    high_severity_anomalies = any(a.get("severity") == "HIGH" for a in anomalies)
    requires_hitl = (
        high_severity_anomalies or
        overall_risk == "HIGH" or
        insights.get("requires_human_review", False) or
        insights.get("confidence", 1.0) < 0.75
    )

    status = "PENDING_HUMAN_REVIEW" if requires_hitl else "completed"

    return {
        "requires_human_review": requires_hitl,
        "status": status,
        "execution_logs": state.get("execution_logs", []) + [f"HITL Evaluator completed (Requires Review: {requires_hitl})."]
    }


def build_advisor_graph() -> StateGraph:
    graph = StateGraph(AdvisorState)

    graph.add_node("data_fetcher", data_fetcher_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("insight_agent", insight_node)
    graph.add_node("validator", validator_node)
    graph.add_node("hitl_evaluator", hitl_evaluator_node)

    graph.set_entry_point("data_fetcher")
    graph.add_edge("data_fetcher", "analyzer")
    graph.add_edge("analyzer", "insight_agent")
    graph.add_edge("insight_agent", "validator")
    graph.add_edge("validator", "hitl_evaluator")
    graph.add_edge("hitl_evaluator", END)

    return graph.compile()


advisor_workflow = build_advisor_graph()
