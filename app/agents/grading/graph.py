"""Grading Agent LangGraph 状态机定义。"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from .nodes import AsyncGradingNodes
from .state import GradingAgentState


def build_grading_graph(nodes: AsyncGradingNodes):
    """构建 Grading Agent 状态机。"""

    graph = StateGraph(GradingAgentState)
    graph.add_node("grade_questions", nodes.grade_questions)
    graph.add_node("build_teacher_review", nodes.build_teacher_review)
    graph.add_node("build_learning_analysis", nodes.build_learning_analysis)
    graph.add_node("finalize_totals", nodes.finalize_totals)

    graph.set_entry_point("grade_questions")
    graph.add_edge("grade_questions", "build_teacher_review")
    graph.add_edge("build_teacher_review", "build_learning_analysis")
    graph.add_edge("build_learning_analysis", "finalize_totals")
    graph.add_edge("finalize_totals", END)
    return graph.compile()
