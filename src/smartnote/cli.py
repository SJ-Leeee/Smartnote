"""SmartNote CLI - 메인 진입점"""

import os
import re
import time
from prompt_toolkit.shortcuts.progress_bar import Progress
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from pathlib import Path
from dotenv import load_dotenv

from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)
import yaml

# Core modules
from smartnote.core.classifier import CategoryClassifier
from smartnote.core.workflow import create_workflow, NoteState
from smartnote.rag.embedding_store import EmbeddingStore
from smartnote.storage.obsidian import ObsidianStorage


app = typer.Typer(
    name="smartnote", help=f"📈 글을 가공하여 알맞는 카테고리에 자동으로 저장하는 도구"
)

console = Console()
load_dotenv()


# 만약 데코레이터가 없다면 수동으로 if else 문으로 해야한다.
@app.command()
def save(
    file_path: str = typer.Argument(..., help="저장할 마크다운 경로"),
    skip_notion: bool = typer.Option(False, "--skip-notion", help="노션 저장 건너뛰기"),
):
    """
    🗃️ 마크다운 노트를 분석하고 저장합니다.

    Example:
        상대경로, 절대경로 OK
        smartnote save note.md
        smartnote save note.md --skip-notion
    """
    console.print(
        Panel.fit(  # 박스형
            f"📝 파일 처리 중: [cyan]{file_path}[/cyan]",
            title="SmartNote",
            border_style="blue",
        )
    )

    # 파일 존재확인
    path = Path(file_path)

    if not path.exists():
        console.print(f"[red]🚫 파일을 찾을 수 없습니다: {file_path}[/red]")
        raise typer.Exit(code=1)

    # 파일 내용 읽기
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    console.print(f"[green]✅ 파일 읽기 완료 ({len(content)} Bytes)[/green]")
    # TODO: 청킹고려
    if len(content) > 8000:
        console.print(
            f"[yellow]⚠️  파일이 큽니다 ({len(content)} bytes). 향상 품질이 저하될 수 있습니다.[/yellow]"
        )
    # 제목 추출 (첫 # 라인)
    lines = content.split("\n")
    title = next(
        (line.strip("# ").strip() for line in lines if line.startswith("#")), path.stem
    )

    # 미리보기
    console.print("\n[yellow]📄 파일 내용 미리보기:[/yellow]")
    preview = content[:300] + "..." if len(content) > 300 else content
    md = Markdown(preview)
    console.print(md)

    # 워크플로우 실행
    console.print("\n[yellow]🔄 AI 워크플로우 시작...[/yellow]\n")

    # 워크플로우 객체
    initial_state: NoteState = {
        "original_content": content,
        "title": title,
        "file_path": str(path),
        "skip_notion": skip_notion,
        "enhanced_content": "",
        "metadata": {},
        "user_approved": False,
        "user_feedback": "",
        "user_feedback_text": "",
        "saved_paths": {},
        "related_notes": [],
        "classify_result": {},
        "judge_retry_count": 0,
    }

    try:
        workflow = create_workflow()
        result = workflow.invoke(initial_state)

        # 결과 표시
        console.print("\n[green]✨ 완료![/green]\n")

        # 저장 결과 출력 (node_save가 saved_paths에 결과를 넣어줌)
        if result["saved_paths"].get("obsidian"):
            console.print(
                f"[cyan]📂 Obsidian: {result['saved_paths']['obsidian']}[/cyan]"
            )

        if result["saved_paths"].get("notion"):
            console.print(f"[cyan]🌐 Notion: {result['saved_paths']['notion']}[/cyan]")

    except Exception as e:
        console.print(f"\n[red]❌ 오류 발생: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def bulk(
    directory: str = typer.Argument(..., help="스캔할 디렉토리 경로"),
):
    """
    디렉토리 내 .md 파일을 일괄 분류 + 임베딩합니다. (enhance/Notion 저장 없음)

    Example:
        smartnote bulk /Users/iseungjun/Lee/SmartNote
        smartnote bulk tmp/
    """

    dir_path = Path(directory)
    if not dir_path.exists():
        console.print(f"[red]🚫 디렉토리를 찾을 수 없습니다: {directory}[/red]")
        raise typer.Exit(code=1)

    md_files = list(dir_path.rglob("*.md"))
    console.print(
        Panel.fit(
            f"📂 {directory}\n총 [cyan]{len(md_files)}[/cyan]개 파일 발견",
            title="SmartNote Bulk",
            border_style="blue",
        )
    )

    classifier = CategoryClassifier()
    obsidian = ObsidianStorage()
    store = EmbeddingStore()

    success, skipped, failed = 0, 0, 0
    failed_files = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("처리 중...", total=len(md_files))

        for file_path in md_files:
            progress.update(task, description=f"[cyan]{file_path.name[:40]}[/cyan]")

            try:
                note_id = str(file_path.resolve())

                # 이미 임베딩된 파일 스킵
                if store.is_embedded(note_id):
                    skipped += 1
                    progress.advance(task)
                    continue

                content = file_path.read_text(encoding="utf-8")
                if not content.strip():
                    skipped += 1
                    progress.advance(task)
                    continue

                # 기존 frontmatter에서 태그 추출
                match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
                existing_tags = []
                if match:
                    fm = yaml.safe_load(match.group(1)) or {}
                    existing_tags = fm.get("tags", []) or []

                # 제목 추출 (frontmatter title → 첫 # 헤딩 → 파일명 순)
                title = file_path.stem
                if match:
                    fm_title = (yaml.safe_load(match.group(1)) or {}).get("title")
                    if fm_title:
                        title = fm_title
                if title == file_path.stem:
                    lines = content.split("\n")
                    heading = next(
                        (l.strip("# ").strip() for l in lines if l.startswith("# ")),
                        None,
                    )
                    if heading:
                        title = heading

                # 분류 (confidence ≤ 0.8 이면 etc)
                result = classifier.classify(content[:3000], title)
                if result["confidence"] > 0.8 and result["primary_category"] != "etc":
                    category = result["primary_category"]
                    subcategory = result["subcategory"]
                else:
                    category = "etc"
                    subcategory = "Uncategorized"

                # vault에 새 파일 생성 (원본 건드리지 않음)
                metadata = {
                    "title": title,
                    "category": category,
                    "subcategory": subcategory,
                    "tags": existing_tags,
                }
                obsidian_path = obsidian.save(content, metadata)

                # ChromaDB 임베딩
                store.add_note(
                    note_id=note_id,
                    content=content[:3000],
                    metadata={
                        "title": title,
                        "category": category,
                        "subcategory": subcategory,
                        "tags": ", ".join(str(t) for t in existing_tags),
                        "file_path": str(obsidian_path),
                    },
                )

                success += 1
                time.sleep(0.3)

            except Exception as e:
                failed += 1
                failed_files.append(f"{file_path}: {e}")

            progress.advance(task)

    # 결과 요약
    console.print(
        f"\n[green]✅ 성공: {success}[/green]  "
        f"[yellow]스킵: {skipped}[/yellow]  "
        f"[red]실패: {failed}[/red]"
    )

    if failed_files:
        log_path = Path("failed_migrations.log")
        log_path.write_text("\n".join(failed_files), encoding="utf-8")
        console.print(f"[red]실패 목록: {log_path}[/red]")


@app.command()
def stats():
    """
    학습 통계를 보여줍니다.
    """
    console.print(Panel.fit("📊 학습 통계", border_style="yellow"))

    # TODO: 통계 표시
    console.print(
        """
[yellow]카테고리별 노트:[/yellow]
• Language: 8개
• AI: 5개
• Tools: 3개

[yellow]최근 7일:[/yellow]
• 총 5개 노트 작성
• 평균 0.7개/일

[dim](TODO: 실제 통계 구현)[/dim]
    """
    )


@app.command()
def init():
    """
    SmartNote 초기 설정을 진행합니다.
    """
    console.print(Panel.fit("🎉 SmartNote 초기화", border_style="blue"))
    # TODO: Init 작업
    console.print(
        """                                                                               
[yellow]다음 작업을 진행합니다:[/yellow]                                                            
1. config.yaml 생성                                                                                 
2. Obsidian vault 경로 설정                                                                         
3. ChromaDB 초기화                                                                                  
4. API 키 확인                                                                                      
                                                                                                    
[dim](TODO: 구현 예정)[/dim]                                                                        
    """
    )


@app.callback()
def main():
    """
    SmartNote AI - 지능형 학습 노트 자동화 에이전트
    """
    pass


if __name__ == "__main__":
    app()
