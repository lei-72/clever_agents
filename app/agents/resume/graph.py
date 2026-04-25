"""Resume Agent LangGraph 状态机定义。"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import AsyncResumeNodes
from .state import ResumeAgentState


def build_resume_graph(nodes: AsyncResumeNodes):
    """构建 Resume Agent 状态机（三组并行评审）。"""

    graph = StateGraph(ResumeAgentState)
    graph.add_node("review_group_a", nodes.review_group_a)
    graph.add_node("review_group_b", nodes.review_group_b)
    graph.add_node("review_group_c", nodes.review_group_c)
    graph.add_node("merge_report", nodes.merge_report)

    graph.add_edge(START, "review_group_a")
    graph.add_edge(START, "review_group_b")
    graph.add_edge(START, "review_group_c")
    graph.add_edge("review_group_a", "merge_report")
    graph.add_edge("review_group_b", "merge_report")
    graph.add_edge("review_group_c", "merge_report")
    graph.add_edge("merge_report", END)
    return graph.compile()
