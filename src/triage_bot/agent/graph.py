from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from triage_bot.agent.nodes import TriageNodes
from triage_bot.agent.state import TriageState
from triage_bot.github.client import GitHubClient


def _after_fetch(state: TriageState) -> str:
    return END if state.get("skipped") else "classify"


def _after_classify(state: TriageState) -> str:
    classification = state.get("classification")
    return "check_repro" if classification and "bug" in classification.labels else "suggest_assignee"


def build_graph(llm: BaseChatModel, gh: GitHubClient, allowed_labels: list[str]):
    nodes = TriageNodes(llm, gh, allowed_labels)
    graph = StateGraph(TriageState)

    graph.add_node("fetch_context", nodes.fetch_context)
    graph.add_node("classify", nodes.classify)
    graph.add_node("check_repro", nodes.check_repro)
    graph.add_node("suggest_assignee", nodes.suggest_assignee)
    graph.add_node("act", nodes.act)

    graph.add_edge(START, "fetch_context")
    graph.add_conditional_edges("fetch_context", _after_fetch, ["classify", END])
    graph.add_conditional_edges("classify", _after_classify, ["check_repro", "suggest_assignee"])
    graph.add_edge("check_repro", "suggest_assignee")
    graph.add_edge("suggest_assignee", "act")
    graph.add_edge("act", END)

    return graph.compile()
