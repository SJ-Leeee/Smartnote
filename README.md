# SmartNote AI

> 간단한 메모를 완성도 높은 학습 노트로 자동 변환하고, Obsidian과 Notion에 저장하는 AI 에이전트

## 개요

글을 쓰려고 하면 항상 막힌다. 당연한 내용을 적어야 하나? 아는 내용을 굳이 정리해야 하나?
SmartNote AI는 이 장벽을 낮춘다.

짧은 메모를 입력하면 Claude AI가 내용을 분석하고 구조화한다. 사용자가 피드백을 반영하면 Obsidian 로컬 vault와 Notion에 자동으로 저장된다.

## 핵심 기능

- **지능형 글 다듬기**: 간단한 메모 → YAML frontmatter 포함 완성도 높은 학습 노트
- **사용자 피드백 루프**: Accept / Edit / Quit 인터랙션으로 결과물 제어
- **Obsidian 자동 저장**: 카테고리별 디렉토리 구조, 날짜 기반 파일명
- **Notion 자동 발행**: Database에 페이지 생성, 태그/요약 메타데이터 자동 설정
- **선택적 저장**: `--skip-notion` 플래그로 Obsidian만 저장 가능

## 기술 스택

| 영역 | 기술 |
|---|---|
| LLM | Claude API (Anthropic) — Tool Calling 방식 |
| 워크플로우 | LangGraph (StateGraph) |
| CLI | Typer + Rich |
| 외부 저장소 | Obsidian (파일시스템), Notion API |
| 언어 | Python 3.11+ |
| 패키지 관리 | Poetry |

## 워크플로우

```
마크다운 메모 입력
      ↓
  enhance (Claude API)
  — 내용 분석 + 보완 + YAML frontmatter 생성
      ↓
  feedback (CLI)
  — 보완 결과 미리보기
  — [A] Accept  [E] Edit  [Q] Quit
      ↓ (Edit 시 enhance로 재진입)
  save
  — Obsidian vault에 파일 저장
  — Notion Database에 페이지 발행
```

## 설치

```bash
git clone https://github.com/your-id/smartnote.git
cd smartnote
poetry install
```

`.env` 파일 생성:

```
ANTHROPIC_API_KEY=sk-ant-...
OBSIDIAN_VAULT_PATH=/path/to/your/vault
NOTION_PRIVATE_KEY=ntn_...
NOTION_DATABASE_ID=...
```

## 사용법

```bash
# 기본 사용 (Obsidian + Notion 저장)
poetry run smartnote save note.md

# Obsidian만 저장
poetry run smartnote save note.md --skip-notion

# 저장된 노트 목록
poetry run smartnote list

# 학습 통계
poetry run smartnote stats
```

## 프로젝트 구조

```
src/smartnote/
├── cli.py              # CLI 진입점 (Typer)
├── core/
│   ├── workflow.py     # LangGraph StateGraph
│   └── enhancer.py     # Claude API Tool Calling
└── storage/
    ├── obsidian.py     # Obsidian 파일 저장
    └── notion.py       # Notion API 연동
```

## 개발 배경

- LangGraph 기반 AI 워크플로우 설계 경험
- Claude API Tool Calling 활용
- 외부 API 연동 (Notion)
- 실제로 사용하는 개인 지식 관리 도구 구축
