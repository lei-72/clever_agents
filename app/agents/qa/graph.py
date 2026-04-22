"""QA Agent LangGraph 状态机定义。"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from .nodes import AsyncQANodes, build_query_classifier
from .state import QAAgentState


def build_qa_graph(nodes: AsyncQANodes):
    """构建 QA Agent 状态机。"""

    graph = StateGraph(QAAgentState)
    graph.add_node("classify_query", build_query_classifier())
    graph.add_node("load_history", nodes.load_history)
    graph.add_node("retrieve_documents", nodes.retrieve_documents)
    graph.add_node("generate_answer", nodes.generate_answer)
    graph.add_node("evaluate_confidence", nodes.evaluate_confidence)
    graph.add_node("persist_history", nodes.persist_history)

    graph.set_entry_point("classify_query")
    graph.add_edge("classify_query", "load_history")
    graph.add_edge("load_history", "retrieve_documents")
    graph.add_edge("retrieve_documents", "generate_answer")
    graph.add_edge("generate_answer", "evaluate_confidence")
    graph.add_edge("evaluate_confidence", "persist_history")
    graph.add_edge("persist_history", END)
    return graph.compile()
