from langgraph.graph import StateGraph, END

from app.agent.state import CampaignState, EvaluationState
from app.agent.nodes import (
    load_company_and_leads,
    dispatch_calls,
    load_lead_by_call,
    evaluate_transcript,
    persist_outcome,
)

def build_campaign_graph():
    """
    Graph used when a manager clicks "Trigger Campaign".

    Flow:
        load_company_and_leads  →  dispatch_calls  →  END

    The dispatch node calls Vapi for every pending lead and marks them
    as CALL_INITIATED. Vapi takes it from there and fires a webhook
    when each call finishes.
    """
    graph = StateGraph(CampaignState)

    graph.add_node("load_company_and_leads", load_company_and_leads)
    graph.add_node("dispatch_calls", dispatch_calls)

    graph.set_entry_point("load_company_and_leads")
    graph.add_edge("load_company_and_leads", "dispatch_calls")
    graph.add_edge("dispatch_calls", END)

    return graph.compile()


def build_evaluation_graph():
    """
    Graph triggered by the Vapi webhook after a call ends.

    Flow:
        load_lead_by_call  →  evaluate_transcript  →  persist_outcome  →  END

    The evaluation node uses Claude to read the transcript and decide
    if the lead is QUALIFIED, NOT_INTERESTED, or NEEDS_REVIEW.
    """
    graph = StateGraph(EvaluationState)

    graph.add_node("load_lead_by_call", load_lead_by_call)
    graph.add_node("evaluate_transcript", evaluate_transcript)
    graph.add_node("persist_outcome", persist_outcome)

    graph.set_entry_point("load_lead_by_call")
    graph.add_edge("load_lead_by_call", "evaluate_transcript")
    graph.add_edge("evaluate_transcript", "persist_outcome")
    graph.add_edge("persist_outcome", END)

    return graph.compile()


# Compiled once at import time — reused for every request
campaign_graph = build_campaign_graph()
evaluation_graph = build_evaluation_graph()
