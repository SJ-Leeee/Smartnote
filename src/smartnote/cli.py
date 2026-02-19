"""SmartNote CLI - 메인 진입점"""

import os
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from pathlib import Path
from dotenv import load_dotenv

# Core modules
from smartnote.core.workflow import create_workflow, NoteState


app = typer.Typer(name="smartnote", help=f"🤖 지식노트 분석가공저장 서비스 With AI")

console = Console()
load_dotenv()


# 만약 데코레이터가 없다면 수동으로 if else 문으로 해야한다.
@app.command()
def save(
    file_path: str = typer.Argument(..., help="저장할 마크다운 경로"),
    skip_tistory: bool = typer.Option(
        False, "--skip-tistory", help="티스토리 저장 건너뛰기f"
    ),
):
    """
    🗃️ 마크다운 노트를 분석하고 저장합니다.

    Example:
        smartnote save note.md
        smartnote save note.md --skip-tistory
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
        "skip_tistory": skip_tistory,
        "enhanced_content": "",
        "metadata": {},
        "user_approved": False,
        "user_feedback": "",
        "saved_paths": {},
    }

    try:
        workflow = create_workflow()
        result = workflow(initial_state)

        # 결과 표시
        console.print("\n[green]✨ 완료![/green]\n")

        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "").strip()
        if vault_path:
            category = result.get("classification", {}).get(
                "primary_category", "Uncategorized"
            )
            note_title = (
                result.get("metadata", {}).get("title")
                or result.get("title")
                or title
                or path.stem
            )
            safe_title = "".join(
                ch for ch in note_title if ch not in '<>:"/\\|?*'
            ).strip() or path.stem

            obsidian_dir = Path(vault_path) / category
            obsidian_dir.mkdir(parents=True, exist_ok=True)
            obsidian_path = obsidian_dir / f"{safe_title}.md"
            obsidian_content = result.get("enhanced_content") or content
            obsidian_path.write_text(obsidian_content, encoding="utf-8")

            result.setdefault("saved_paths", {})
            result["saved_paths"]["obsidian"] = str(obsidian_path)
        else:
            console.print(
                "[yellow]⚠️ OBSIDIAN_VAULT_PATH가 설정되지 않아 Obsidian 저장을 건너뜁니다.[/yellow]"
            )

        if result["saved_paths"].get("obsidian"):
            console.print(
                f"[cyan]📂 Obsidian: {result['saved_paths']['obsidian']}[/cyan]"
            )
        # TODO: tistory에 저장하기
        if result["saved_paths"].get("tistory"):
            console.print(
                f"[cyan]🌐 Tistory: {result['saved_paths']['tistory']}[/cyan]"
            )

    except Exception as e:
        console.print(f"\n[red]❌ 오류 발생: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def list(
    category: str = typer.Option(None, "--category", "-c", help="카테고리 필터"),
    limit: int = typer.Option(20, "--limit", "-l", help="표시 개수"),
):
    """
    저장된 노트 목록을 보여줍니다.

    Example:
        smartnote list
        smartnote list --category "Language"
    """
    console.print(Panel.fit("📚 저장된 노트 목록", border_style="green"))

    # TODO: 실제 노트 목록 가져오기
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("날짜", style="dim")
    table.add_column("제목")
    table.add_column("카테고리", style="cyan")
    table.add_column("태그", style="yellow")

    # 예시 데이터
    table.add_row("2026-02-13", "Rust Ownership", "Language/Rust", "ownership, memory")
    table.add_row("2026-02-12", "RAG 기초", "AI/LLM", "rag, vector-db")

    console.print(table)
    console.print(f"\n[dim](TODO: 실제 데이터 표시, 필터 적용)[/dim]")


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
