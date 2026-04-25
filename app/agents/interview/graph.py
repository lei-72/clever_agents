"""Interview Agent LangGraph 状态机定义。"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import AsyncInterviewNodes
from .state import InterviewAgentState


def build_interview_graph(nodes: AsyncInterviewNodes):
    """构建四阶段有限状态机。"""

    graph = StateGraph(InterviewAgentState)
    graph.add_node("intro_stage", nodes.intro_stage)
    graph.add_node("tech_stage", nodes.tech_stage)
    graph.add_node("project_stage", nodes.project_stage)
    graph.add_node("report_stage", nodes.report_stage)
    graph.add_node("apply_answer", nodes.apply_answer)
    graph.add_node("finalize_report", nodes.finalize_report)

    graph.add_edge(START, "intro_stage")
    graph.add_edge("intro_stage", "apply_answer")
    graph.add_conditional_edges(
        "apply_answer",
        nodes.route_after_answer,
        {
            "intro_stage": "intro_stage",
            "tech_stage": "tech_stage",
            "project_stage": "project_stage",
            "report_stage": "report_stage",
            "finalize_report": "finalize_report",
            "end": END,
        },
    )
    graph.add_edge("tech_stage", "apply_answer")
    graph.add_edge("project_stage", "apply_answer")
    graph.add_edge("report_stage", "finalize_report")
    graph.add_conditional_edges(
        "finalize_report",
        nodes.route_after_report,
        {"finalize_report": "finalize_report", "end": END},
    )
    return graph.compile()
