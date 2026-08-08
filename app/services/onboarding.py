from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class CandidateMemoryState(TypedDict):
    answers: list[str]
    candidate: str


def _create_candidate(state: CandidateMemoryState) -> CandidateMemoryState:
    first_answer = state["answers"][0] if state["answers"] else ""
    compact_answer = first_answer.replace("\n", " ").strip()[:60]
    if "共同爱好" in first_answer:
        candidate = "你希望认识有共同爱好、相处轻松的人。"
    elif "同城" in first_answer or "活动" in first_answer:
        candidate = "你希望认识同城、可以一起参加活动的人。"
    elif "星灵" in first_answer:
        candidate = "你目前更希望先在轻松、没有压力的对话中慢慢认识自己。"
    elif compact_answer:
        candidate = f"你希望在没有压力的情况下，慢慢认识可以自然聊天的人；你提到“{compact_answer}”。"
    else:
        candidate = "你希望在没有压力的情况下，慢慢认识可以自然聊天的人。"
    return {**state, "candidate": candidate}


def _build_graph():
    graph = StateGraph(CandidateMemoryState)
    graph.add_node("create_candidate", _create_candidate)
    graph.add_edge(START, "create_candidate")
    graph.add_edge("create_candidate", END)
    return graph.compile()


candidate_memory_graph = _build_graph()


def create_candidate_memory(answers: list[str]) -> str:
    result = candidate_memory_graph.invoke({"answers": answers, "candidate": ""})
    return result["candidate"]
