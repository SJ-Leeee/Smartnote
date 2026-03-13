"""
LangGraph 워크플로우

노트 저장 프로세스를 관리합니다:
1. enhance_content: 내용 분석 + 보완 (Claude API)
2. user_feedback: 사용자 피드백
3. save_note: 저장
"""

import time
from pathlib import Path
from smartnote.core.judge import judge_quality
from smartnote.core.score_logger import log_score
from smartnote.rag.embedding_store import EmbeddingStore
from smartnote.storage.obsidian import ObsidianStorage
from smartnote.storage.notion import NotionStorage
from .classifier import CategoryClassifier  # .만 붙였을 시 같은 폴더

from typing import Annotated, Literal
from typing_extensions import TypedDict
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

from prompt_toolkit import prompt  # 한글 전각문제 해결 라이브러리

# LangGraph 임포트
from langgraph.graph import StateGraph, END

from .enhancer import enhance_content

console = Console()
# 임베딩 DB 초기화
store = EmbeddingStore()


def _merge_dict(a: dict, b: dict) -> dict:
    """Annotated 키 덮어쓰는 방식 정의"""
    return {**a, **b}


class NoteState(TypedDict):
    """워크플로우 상태"""

    # 입력
    original_content: str
    title: str
    file_path: str
    skip_notion: bool

    # 보완 결과
    enhanced_content: str
    metadata: Annotated[dict, _merge_dict]  # 병렬접근

    # 사용자 피드백
    user_approved: bool
    user_feedback: str
    user_feedback_text: str  # ← 추가

    # 최종 결과
    saved_paths: dict

    # 병렬화
    related_notes: list
    classify_result: dict  # node_classify의 raw LLM 결과

    # 평가점수
    quality_scores: dict

    # 자동 재시도 횟수
    judge_retry_count: int


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

    scores = state.get("quality_scores")
    if scores:
        issues_text = (
            "\n"
            + "\n".join(
                f"[yellow]{i+1}. {issue}[/yellow]"
                for i, issue in enumerate(scores["issues"])
            )
            if scores.get("issues")
            else ""
        )
        console.print(
            Panel(
                f"[cyan]원본보존[/]{scores['original_preservation']}/10  "
                f"[cyan]태그품질[/] {scores['tag_quality']}/10  "
                f"[cyan]가독성[/] {scores['readability']}/10  "
                f"→ [bold]총점 {scores['total']}/10[/]" + issues_text,
                title="[bold green]Judge 평가[/bold green]",
                border_style="green",
            )
        )

    while True:
        console.print(
            "\n[bold][[green]A[/green]] Accept  [[yellow]E[/yellow]] Edit  [[red]Q[/red]] Quit[/bold]"
        )
        choice = prompt(" > ").strip().upper()

        if choice == "A":
            # 카테고리화 + 선택UX + 태그선택UX
            # 승인
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


def node_classify(state: NoteState) -> NoteState:
    t0 = time.time()  # 현재시간
    # 1. 카테고리 호출 (글 작성을 Accept 했을 때)
    with console.status("[magenta]카테고리 분류 중...[/magenta]", spinner="dots"):
        classifier = CategoryClassifier()
        result = classifier.classify(
            state["enhanced_content"], state["metadata"].get("title", "")
        )
    classify_time = time.time() - t0
    console.print(f"[dim]⏱ classify: {classify_time:.2f}s[/dim]")
    state["metadata"]["_classify_time"] = classify_time  # 분류시간 state에 저장
    # 카테고리 UX 삭제
    return {
        "classify_result": result,
        "metadata": {
            **state["metadata"],
            "_classify_time": classify_time,
        },
    }


def node_find_related(state: NoteState) -> NoteState:
    t0 = time.time()
    related_notes = store.search_related(
        state["enhanced_content"],
        top_k=3,
        cur_title=state["metadata"].get("title", state["title"]),
    )
    find_related_time = time.time() - t0
    console.print(f"[dim]⏱ find_related: {find_related_time:.2f}s[/dim]")  # db접근 시간
    return {
        "related_notes": related_notes,
        "metadata": {**state["metadata"], "_find_related_time": find_related_time},
    }


def node_user_input(state: NoteState) -> dict:
    """병렬작업끝나고 UX종합 실행"""
    # 카테고리 선택
    category, subcategory = _select_category(state["classify_result"])
    # 태그
    new_metadata = _node_add_tags(state)

    classify_t = state["metadata"].get("_classify_time", 0)
    find_t = state["metadata"].get("_find_related_time", 0)
    wall_time = max(classify_t, find_t)  # 실제 병렬 소요 시간
    console.print(
        f"[dim]⏱ classify: {classify_t:.2f}s | find_related: {find_t:.2f}s | 병렬 소요: {wall_time:.2f}s[/dim]"
    )

    return {
        "metadata": {
            **new_metadata,
            "category": category,
            "subcategory": subcategory,
        }
    }


def _node_add_tags(state: NoteState) -> NoteState:
    """태그 추가 UX"""
    existing_tags = state["metadata"].get("tags", [])
    console.print(f"\n[cyan]🏷️  적용 태그: {','.join(existing_tags)}[/cyan]")
    # TODO: 이 부분 UX 수정
    extra = prompt("추가할 태그? (없으면 Enter) > ").strip()
    added = [t.strip() for t in extra.split(",") if t.strip()] if extra else []
    # 소문자 정규화
    state["metadata"]["tags"] = [_normalize_tag(t) for t in existing_tags + added]
    return {
        **state["metadata"],
        "tags": [_normalize_tag(t) for t in existing_tags + added],
    }


def node_save(state: NoteState) -> NoteState:
    """노드 3: 저장"""
    print("💾 저장 중...")
    saved_paths = {}
    # Obsidian 저장 (항상)
    obsidian = ObsidianStorage()
    obsidian_path = obsidian.save(
        state["enhanced_content"], state["metadata"], state["related_notes"]
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
        note_id=str(Path(state["file_path"]).resolve()),  # 같은 이름일 시 UPSERT
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


def should_continue(state: NoteState) -> Literal["enhance", "approved"]:
    """조건부 분기: 피드백 후 다음 단계 결정"""

    if state["user_feedback"] == "edit":
        return "enhance"  # 글 향상
    return "approved"  # 분류 + 연관노트 검색


def should_retry(state: NoteState) -> Literal["enhance", "feedback"]:
    scores = state.get("quality_scores", {})
    total = scores.get("total", 10)
    retry_count = state.get("judge_retry_count", 0)

    if total < 8 and retry_count < 2:
        console.print(
            f"[yellow]⚡ Judge 점수 {total}/10 → 자동 재시도({retry_count}/2)[/yellow]"
        )
        return "enhance"
    return "feedback"


def node_dispatch(state: NoteState) -> NoteState:
    """빈 노드로 병렬처리"""
    return state


def node_judge(state: NoteState) -> dict:
    """보완본 품질 평가 (sonnet judge)"""
    scores = judge_quality(
        original=state["original_content"],
        enhanced=state["enhanced_content"],
        tags=state["metadata"].get("tags", []),
    )
    retry_count = state.get("judge_retry_count", 0)
    phase = f"attempt_{retry_count + 1}"
    log_score(state["file_path"], scores, phase=phase)

    issues_feedback = ""
    if scores.get("total", 10) < 8 and retry_count < 2:
        issues = scores.get("issues", [])
        if issues:
            issues_feedback = "다음 문제를 개선해줘: " + ",".join(issues)
    return {
        "quality_scores": scores,
        "judge_retry_count": retry_count + 1,
        "user_feedback_text": issues_feedback,
    }


def create_workflow():
    """워크플로우 생성"""

    workflow = StateGraph(NoteState)

    # 노드 추가
    workflow.add_node("enhance", node_enhance)
    workflow.add_node("judge", node_judge)
    workflow.add_node("feedback", node_feedback)
    workflow.add_node("classify", node_classify)
    workflow.add_node("user_input", node_user_input)
    workflow.add_node("dispatch", node_dispatch)
    workflow.add_node("find_related", node_find_related)  # 여기서 태그까지.
    workflow.add_node("save", node_save)

    # 엣지 연결
    workflow.set_entry_point("enhance")
    workflow.add_edge("enhance", "judge")

    # 조건부 분기: 평가후 자동향상 로직
    workflow.add_conditional_edges("judge", should_retry)
    # 조건부 분기: feedback 후 다음 단계 결정
    workflow.add_conditional_edges(
        "feedback", should_continue, {"enhance": "enhance", "approved": "dispatch"}
    )

    workflow.add_edge("dispatch", "classify")  # 여기서 fan-out
    workflow.add_edge("dispatch", "find_related")  # 동시에 두 노드로
    workflow.add_edge("classify", "user_input")
    workflow.add_edge("find_related", "user_input")
    workflow.add_edge("user_input", "save")
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
