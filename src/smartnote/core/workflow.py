"""
LangGraph 워크플로우

노트 저장 프로세스를 관리합니다:
1. enhance_content: 내용 분석 + 보완 (Claude API)
2. user_feedback: 사용자 피드백
3. save_note: 저장
"""

from smartnote.rag.embedding_store import EmbeddingStore
from smartnote.storage.obsidian import ObsidianStorage
from smartnote.storage.notion import NotionStorage
from .classifier import CategoryClassifier  # .만 붙였을 시 같은 폴더

from typing import Literal
from typing_extensions import TypedDict
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

from prompt_toolkit import prompt  # 한글 전각문제 해결 라이브러리

console = Console()
# 임베딩 DB 초기화
store = EmbeddingStore()

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


def _select_category(result: dict) -> tuple[str, str]:
    """방법4: confidence 기반 카테고리 선택 UX"""
    primary = result["primary_category"]
    sub_category = result["subcategory"]
    confidence = result["confidence"]
    suggestions = result.get("suggestions", [])

    if confidence > 0.8:
        console.print(
            f"\n[green]✅ 카테고리 추천: {primary} / {sub_category}[/green] "
            f"[dim]({confidence:.0%} - {result['reason']})[/dim]"
        )
        answer = prompt("[Y/n] > ").strip().lower()
        if answer in ("", "y"):
            return primary, sub_category

    # confidence 낮거나 사용자가 n 입력
    candidates = [result] + suggestions[:2]  # 1순위 + 2,3 순위
    console.print("\n[yellow]📊 카테고리 선택:[/yellow]")
    for i, c in enumerate(candidates, 1):  # 2, 3순위만
        star = "⭐" if i == 1 else "  "
        console.print(
            f"  {i}. [bold]{c['primary_category']} /{c['subcategory']}[/bold] "
            f"({c['confidence']:.0%}) {star}"
        )
        console.print(f"     [dim]{c['reason']}[/dim]")
    console.print(f"  {len(candidates) + 1}. 직접 입력")

    while True:
        choice = prompt(f"선택 [1-{len(candidates) + 1}] > ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                c = candidates[idx]
                return c["primary_category"], c["subcategory"]
            elif idx == len(candidates):
                cat = prompt("대분류 > ").strip()
                sub_category = prompt("중분류 > ").strip()
                return cat, sub_category
        console.print("[red]올바른 번호를 입력하세요.[/red]")


def _normalize_tag(tag: str) -> str:
    """영문 태그는 소문자, 한글은 그대로"""
    if any("\uac00" <= c <= "\ud7a3" for c in tag):
        return tag.strip()
    return tag.lower().strip()


def node_enhance(state: NoteState) -> NoteState:
    """노드 1: 내용 분석 + 보완"""

    with console.status("[cyan]내용 보완 중...[/cyan]", spinner="dots"):
        result = enhance_content(
            original_content=state["original_content"],
            title=state["title"],
            feedback=state.get("user_feedback_text", ""),  # key값이 존재하지 않을수도
            previous_enhanced=state.get("enhanced_content", ""),  # 이전 보완된 글
        )

    state["enhanced_content"] = result["enhanced_content"]
    state["metadata"] = result["metadata"]
    return state


def node_feedback(state: NoteState) -> NoteState:
    """노드 2: 사용자 피드백"""
    print("\n📋 사용자 피드백 대기...")
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
        console.print(
            "\n[bold][[green]A[/green]] Accept  [[yellow]E[/yellow]] Edit  [[red]Q[/red]] Quit[/bold]"
        )
        choice = prompt(" > ").strip().upper()

        if choice == "A":
            # 1. 카테고리 호출 (글 작성을 Accept 했을 때)
            with console.status(
                "[magenta]카테고리 분류 중...[/magenta]", spinner="dots"
            ):
                classifier = CategoryClassifier()
                result = classifier.classify(
                    state["enhanced_content"], state["metadata"].get("title", "")
                )

            # 2. 카테고리 선택  UX
            category, subcategory = _select_category(result)
            state["metadata"]["category"] = category
            state["metadata"]["subcategory"] = subcategory

            # 3. 태그 추가 UX
            existing_tags = state["metadata"].get("tags", [])
            console.print(f"\n[cyan]🏷️  적용 태그: {','.join(existing_tags)}[/cyan]")

            # TODO: 이 부분 UX 수정
            extra = prompt("추가할 태그? (없으면 Enter) > ").strip()
            added = [t.strip() for t in extra.split(",") if t.strip()] if extra else []
            all_tags = existing_tags + added
            # 소문자 정규화
            state["metadata"]["tags"] = [_normalize_tag(t) for t in all_tags]

            # 4. 승인
            state["user_approved"] = True
            state["user_feedback"] = "approved"
            break
        elif choice == "E":
            console.print("[yellow]수정 요청 내용을 입력하세요:[/yellow]")
            feedback_text = prompt(" > ").strip()
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
    related_notes = store.search_related(
        state["enhanced_content"],
        top_k=3,
        cur_title=state["metadata"].get("title", state["title"]),
    )
    saved_paths = {}
    # Obsidian 저장 (항상)
    obsidian = ObsidianStorage()
    obsidian_path = obsidian.save(
        state["enhanced_content"], state["metadata"], related_notes
    )
    saved_paths["obsidian"] = obsidian_path

    # Notion 저장 (skip_notion이 False일 때만)
    if not state["skip_notion"]:
        try:
            notion = NotionStorage()
            notion_url = notion.save(state["enhanced_content"], state["metadata"])
            saved_paths["notion"] = notion_url
        except Exception as e:
            print(f"⚠️ Notion 저장 실패 (Obsidian은 저장됨): {e}")
    # 저장 후 임베딩 DB에도 저장
    store.add_note(
        note_id=str(obsidian_path),  # 같은 이름일 시 UPSERT
        content=state["enhanced_content"],
        metadata={
            "title": state["metadata"].get("title", state["title"]),
            "category": state["metadata"].get("category", ""),
            "subcategory": state["metadata"].get("subcategory", ""),
            "tags": ", ".join(state["metadata"].get("tags", [])),
            "file_path": str(obsidian_path),
        },
    )

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
