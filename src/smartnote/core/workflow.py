"""
LangGraph 워크플로우

노트 저장 프로세스를 관리합니다:
1. enhance_content: 내용 분석 + 보완 (Claude API)
2. user_feedback: 사용자 피드백
3. save_note: 저장

[보류] analyze / classify 노드는 Day 5 (Category System) 구현 시 추가 예정
"""

from smartnote.storage.obsidian import ObsidianStorage
from smartnote.storage.notion import NotionStorage

from typing import Literal
from typing_extensions import TypedDict
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

console = Console()

# LangGraph 임포트
from langgraph.graph import StateGraph, END

from .enhancer import enhance_content


class NoteState(TypedDict):
    """워크플로우 상태"""

    # 입력
    original_content: str
    title: str
    file_path: str
    skip_notion: bool

    # 보완 결과
    enhanced_content: str
    metadata: dict

    # 사용자 피드백
    user_approved: bool
    user_feedback: str
    user_feedback_text: str  # ← 추가

    # 최종 결과
    saved_paths: dict


def node_enhance(state: NoteState) -> NoteState:
    """노드 1: 내용 분석 + 보완"""
    print("✨ 내용 보완 중...")

    result = enhance_content(
        original_content=state["original_content"],
        title=state["title"],
        feedback=state.get("user_feedback_text", ""),  # key값이 존재하지 않을수도
    )

    state["enhanced_content"] = result["enhanced_content"]
    state["metadata"] = result["metadata"]
    return state


def node_feedback(state: NoteState) -> NoteState:
    """노드 2: 사용자 피드백"""
    print("\n📋 사용자 피드백 대기...")

    # TODO: Rich로 원본 vs 보완본 diff 표시
    console.print(
        Panel(
            Markdown(state["original_content"]),
            title="[bold yellow]원본[/bold yellow]",
            border_style="yellow",
        )
    )

    console.print(
        Panel(
            Markdown(state["enhanced_content"]),
            title="[bold cyan]보완본[/bold cyan]",
            border_style="cyan",
        )
    )

    while True:
        choice = input("\n[A] Accept  [E] Edit  [Q] Quit > ").strip().upper()

        if choice == "A":
            state["user_approved"] = True
            state["user_feedback"] = "approved"
            break
        elif choice == "E":
            feedback_text = input("수정 요청 내용: ").strip()
            state["user_feedback_text"] = feedback_text
            state["user_feedback"] = "edit"
            break
        elif choice == "Q":
            raise SystemExit(0)
        else:
            print("A, E, Q 중 하나를 입력하세요.")

    return state


def node_save(state: NoteState) -> NoteState:
    """노드 3: 저장"""
    print("💾 저장 중...")
    saved_paths = {}
    # Obsidian 저장 (항상)
    obsidian = ObsidianStorage()
    obsidian_path = obsidian.save(state["enhanced_content"], state["metadata"])
    saved_paths["obsidian"] = obsidian_path

    # Notion 저장 (skip_notion이 False일 때만)
    if not state["skip_notion"]:
        try:
            notion = NotionStorage()
            notion_url = notion.save(state["enhanced_content"], state["metadata"])
            saved_paths["notion"] = notion_url
        except Exception as e:
            print(f"⚠️ Notion 저장 실패 (Obsidian은 저장됨): {e}")

    state["saved_paths"] = saved_paths
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
    from pathlib import Path

    file_path = Path("tmp/react_렌더링_사이클.md")
    content = file_path.read_text(encoding="utf-8")
    print("🚀 LangGraph 워크플로우 테스트\n")

    initial_state: NoteState = {
        "original_content": content,
        "title": "react 렌더링 사이클",
        "file_path": file_path,
        "skip_notion": False,
        "enhanced_content": "",
        "metadata": {},
        "user_approved": False,
        "user_feedback": "",
        "saved_paths": {},
        "user_feedback_text": "",
    }

    app = create_workflow()
    result = app.invoke(initial_state)

    print("\n" + "=" * 50)
    print("✅ 워크플로우 완료!")
    print("=" * 50)
    print(f"📋 메타데이터: {result['metadata']}")
    print(f"💾 저장: {result['saved_paths']}")
    print("=" * 50)
