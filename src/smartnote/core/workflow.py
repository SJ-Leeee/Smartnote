"""
LangGraph 워크플로우

노트 저장 프로세스를 관리합니다:
1. enhance_content: 내용 분석 + 보완 (Claude API)
2. user_feedback: 사용자 피드백
3. save_note: 저장

[보류] analyze / classify 노드는 Day 5 (Category System) 구현 시 추가 예정
"""

from typing import Literal
from typing_extensions import TypedDict

# LangGraph 임포트
from langgraph.graph import StateGraph, END

from .enhancer import enhance_content


class NoteState(TypedDict):
    """워크플로우 상태"""

    # 입력
    original_content: str
    title: str
    file_path: str
    skip_tistory: bool

    # 보완 결과
    enhanced_content: str
    metadata: dict

    # 사용자 피드백
    user_approved: bool
    user_feedback: str

    # 최종 결과
    saved_paths: dict


def node_enhance(state: NoteState) -> NoteState:
    """노드 1: 내용 분석 + 보완"""
    print("✨ 내용 보완 중...")

    result = enhance_content(
        original_content=state["original_content"],
        title=state["title"],
    )

    state["enhanced_content"] = result["enhanced_content"]
    state["metadata"] = result["metadata"]
    return state


def node_feedback(state: NoteState) -> NoteState:
    """노드 2: 사용자 피드백"""
    print("\n📋 사용자 피드백 대기...")

    # TODO: Rich로 원본 vs 보완본 diff 표시
    # TODO: 사용자 입력 받기 (Accept/Reject/Edit)

    # 임시: 자동 승인
    state["user_approved"] = True
    state["user_feedback"] = "approved"
    return state


def node_save(state: NoteState) -> NoteState:
    """노드 3: 저장"""
    print("💾 저장 중...")

    # TODO: Obsidian 저장
    # TODO: Tistory 저장 (skip_tistory가 False일 때)

    state["saved_paths"] = {
        "obsidian": "/path/to/vault/Category/note.md (TODO)",
        "tistory": (
            "https://blog.tistory.com/123 (TODO)" if not state["skip_tistory"] else None
        ),
    }

    return state


def should_continue(state: NoteState) -> Literal["enhance", "save"]:
    """조건부 분기: 피드백 후 다음 단계 결정"""

    if state["user_feedback"] == "edit":
        return "enhance"  # 다시 보완
    else:
        return "save"  # 저장


def create_workflow():
    """워크플로우 생성"""

    workflow = StateGraph(NoteState)

    # 노드 추가
    workflow.add_node("enhance", node_enhance)
    workflow.add_node("feedback", node_feedback)
    workflow.add_node("save", node_save)

    # 엣지 연결
    workflow.set_entry_point("enhance")
    workflow.add_edge("enhance", "feedback")

    # 조건부 분기: feedback 후 다음 단계 결정
    workflow.add_conditional_edges(
        "feedback",
        should_continue,
        {"enhance": "enhance", "save": "save"},
    )

    workflow.add_edge("save", END)

    return workflow.compile()


# 테스트 코드
if __name__ == "__main__":
    print("🚀 LangGraph 워크플로우 테스트\n")

    initial_state: NoteState = {
        "original_content": "# Rust Ownership\n변수가 scope를 벗어나면 메모리가 자동 해제됨.",
        "title": "Rust Ownership",
        "file_path": "test.md",
        "skip_tistory": False,
        "enhanced_content": "",
        "metadata": {},
        "user_approved": False,
        "user_feedback": "",
        "saved_paths": {},
    }

    app = create_workflow()
    result = app.invoke(initial_state)

    print("\n" + "=" * 50)
    print("✅ 워크플로우 완료!")
    print("=" * 50)
    print(f"📋 메타데이터: {result['metadata']}")
    print(f"💾 저장: {result['saved_paths']}")
    print("=" * 50)
