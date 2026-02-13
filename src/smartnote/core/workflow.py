"""
LangGraph 워크플로우

노트 저장 프로세스를 관리합니다:
1. analyze_content: 내용 분석
2. classify_category: 카테고리 분류
3. enhance_content: 내용 보완
4. user_feedback: 사용자 피드백
5. save_note: 저장
"""

from typing import TypedDict, Annotated, Literal
from typing_extensions import TypedDict

# TODO: LangGraph 임포트
# from langgraph.graph import StateGraph, END

from .analyzer import analyze_content
from .classifier import classify_category
from .enhancer import enhance_content


class NoteState(TypedDict):
    """워크플로우 상태"""
    # 입력
    original_content: str
    title: str
    file_path: str
    skip_tistory: bool

    # 분석 결과
    analysis: dict
    classification: dict

    # 보완 결과
    enhanced_content: str
    metadata: dict

    # 사용자 피드백
    user_approved: bool
    user_feedback: str

    # 최종 결과
    saved_paths: dict


def node_analyze(state: NoteState) -> NoteState:
    """노드 1: 내용 분석"""
    print("🔍 내용 분석 중...")

    analysis = analyze_content(
        content=state["original_content"],
        title=state["title"]
    )

    state["analysis"] = analysis
    return state


def node_classify(state: NoteState) -> NoteState:
    """노드 2: 카테고리 분류"""
    print("📂 카테고리 분류 중...")

    classification = classify_category(
        content=state["original_content"],
        title=state["title"],
        analysis=state["analysis"]
    )

    state["classification"] = classification
    return state


def node_enhance(state: NoteState) -> NoteState:
    """노드 3: 내용 보완"""
    print("✨ 내용 보완 중...")

    result = enhance_content(
        original_content=state["original_content"],
        analysis=state["analysis"],
        classification=state["classification"]
    )

    state["enhanced_content"] = result["enhanced_content"]
    state["metadata"] = result["metadata"]
    return state


def node_feedback(state: NoteState) -> NoteState:
    """노드 4: 사용자 피드백"""
    print("\n📋 사용자 피드백 대기...")

    # TODO: Rich로 diff 표시
    # TODO: 사용자 입력 받기 (Accept/Reject/Edit)

    # 임시: 자동 승인
    state["user_approved"] = True
    state["user_feedback"] = "approved"
    return state


def node_save(state: NoteState) -> NoteState:
    """노드 5: 저장"""
    print("💾 저장 중...")

    # TODO: Obsidian 저장
    # TODO: Tistory 저장 (skip_tistory가 False일 때)
    # TODO: 서브분류 체크 (10개 이상)

    state["saved_paths"] = {
        "obsidian": "/path/to/vault/Category/note.md (TODO)",
        "tistory": "https://blog.tistory.com/123 (TODO)" if not state["skip_tistory"] else None
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

    # TODO: LangGraph로 실제 워크플로우 구성
    # workflow = StateGraph(NoteState)
    # workflow.add_node("analyze", node_analyze)
    # workflow.add_node("classify", node_classify)
    # workflow.add_node("enhance", node_enhance)
    # workflow.add_node("feedback", node_feedback)
    # workflow.add_node("save", node_save)
    #
    # workflow.set_entry_point("analyze")
    # workflow.add_edge("analyze", "classify")
    # workflow.add_edge("classify", "enhance")
    # workflow.add_edge("enhance", "feedback")
    # workflow.add_conditional_edges(
    #     "feedback",
    #     should_continue,
    #     {"enhance": "enhance", "save": "save"}
    # )
    # workflow.add_edge("save", END)
    #
    # return workflow.compile()

    # 임시: 간단한 순차 실행 함수 반환
    return simple_workflow


def simple_workflow(initial_state: NoteState) -> NoteState:
    """임시 워크플로우 (LangGraph 없이)"""

    state = initial_state

    # 순차 실행
    state = node_analyze(state)
    state = node_classify(state)
    state = node_enhance(state)
    state = node_feedback(state)

    # 조건부 분기
    if should_continue(state) == "save":
        state = node_save(state)
    else:
        # 다시 enhance (실제로는 루프)
        state = node_enhance(state)
        state = node_save(state)

    return state


# 테스트 코드
if __name__ == "__main__":
    initial_state: NoteState = {
        "original_content": "# Test\nContent",
        "title": "Test",
        "file_path": "test.md",
        "skip_tistory": False,
        "analysis": {},
        "classification": {},
        "enhanced_content": "",
        "metadata": {},
        "user_approved": False,
        "user_feedback": "",
        "saved_paths": {}
    }

    workflow = create_workflow()
    result = workflow(initial_state)

    print("\n✅ 워크플로우 완료!")
    print(f"저장 경로: {result['saved_paths']}")
