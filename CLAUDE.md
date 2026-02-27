# SmartNote AI - CLAUDE.md

## 프로젝트 개요
AI 에이전트가 마크다운 메모를 받아 **다듬기 → 사용자 피드백 → 저장** 자동화 CLI 도구.
포트폴리오 목적. 2주 집중 개발 (2026-02-10 ~ 2026-02-24).

## 현재 진행 상태
- **완료**: Day 1 (Setup), Day 2 (Content Enhancement), Day 3 (Storage Layer), Day 4 (User Feedback Loop)
- **다음**: Day 5 (Category System)
- **브랜치**: `feat/userfeedback-loop` (Day 4 완료, 머지 후 다음 브랜치 생성 필요)

### 완료된 핵심 구현
- LangGraph 3-node 워크플로우: `enhance → feedback → save`
- Claude API Tool Calling 기반 콘텐츠 다듬기 (haiku-4-5 모델)
- 사용자 피드백 루프 (A/E/Q 인터랙션)
- Rich Panel로 원본 → 보완본 순차 표시
- `prompt_toolkit` 기반 한글 입력 (Wide Character 문제 해결)
- Rich 스피너 (`console.status`) 보완 중 표시
- Edit 루프 시 원본 + 이전 보완본 + 수정요청 모두 Claude에 전달
- Obsidian 파일 저장 (YAML frontmatter 자동 생성, 날짜 주입)
- Notion API 저장 (마크다운 → Block 변환, 언어명 매핑 테이블 포함)
- `--skip-notion` 플래그 동작 확인
- E2E 전체 시나리오 검증 완료

## 기술 결정 사항 (변경 이력)
- **Tistory → Notion**: Tistory OpenAPI 2024년 종료로 Notion API 사용
- **Analyzer 노드 제거**: 과도한 추상화로 판단. Enhancer가 분석+보완 통합 담당
- **롤백 로직 → 부분 성공 허용**: Notion 실패 시 Obsidian 보존 (try/except 방식)
- **Workflow 단순화**: 5노드 → 3노드 (enhance/feedback/save)
- **input() → prompt_toolkit**: 한글 Wide Character 잔상 버그로 교체
- **Notion 이미지 블록 변환**: 미구현 상태로 보류, 추후 처리 예정

## 핵심 파일 구조
```
src/smartnote/
├── cli.py              # CLI 진입점 (Typer) - save 명령어 완성
├── core/
│   ├── workflow.py     # LangGraph StateGraph (NoteState TypedDict)
│   ├── enhancer.py     # Claude API Tool Calling (haiku-4-5)
│   ├── analyzer.py     # 스텁 - Day 5에서 구현
│   └── classifier.py   # 카테고리 구조 정의 완료, 로직 TODO
├── storage/
│   ├── obsidian.py     # 완성 - 날짜 frontmatter, 충돌 해결
│   └── notion.py       # 완성 (95%) - 마크다운→Block 변환
├── rag/                # Day 6 예정 (ChromaDB)
├── recommender/        # Day 8-12 예정
└── integrations/       # Day 13 예정 (Slack)
prompts/
└── enhancer.txt        # Claude 시스템 프롬프트 ({today} 플레이스홀더)
```

## 실행 방법
```bash
# 기본 실행 (Obsidian + Notion 저장)
poetry run smartnote save <파일경로>

# Obsidian만 저장
poetry run smartnote save <파일경로> --skip-notion

# 테스트용 파일
poetry run smartnote save tmp/react_렌더링_사이클.md
```

## 환경 설정
`.env` 파일 필요 (프로젝트 루트):
```
ANTHROPIC_API_KEY=...
OBSIDIAN_VAULT_PATH=/Users/iseungjun/Lee/SmartNote
NOTION_PRIVATE_KEY=...
NOTION_DATABASE_ID=...
```

## 기술 스택
- **LLM**: Claude API (anthropic) - `claude-haiku-4-5-20251001`
- **워크플로우**: LangGraph 1.0.8
- **CLI**: Typer + Rich
- **저장**: Obsidian (로컬 파일시스템) + Notion API
- **RAG** (예정): ChromaDB + sentence-transformers
- **패키지 관리**: Poetry

## 카테고리 체계 (classifier.py에 정의)
Algorithm, Data Structure, CS, Language, DevOps, AI, Tools
→ Day 5에서 LLM 기반 분류 로직 구현 예정

## 앞으로의 Day별 계획
- **Day 5**: Category System (하드코딩 → LLM few-shot 분류)
- **Day 6**: RAG Foundation (ChromaDB 설정, 기존 노트 임베딩)
- **Day 7**: MVP 통합 & 실전 테스트 (10개 노트)
- **Day 8+**: Intelligent Categorization, Related Notes, CLI Enhancement

## 작업 스타일
- Claude는 **가이드만 제공**, 직접 코드 수정 금지 (사용자가 명시적으로 지시할 때만 수정)
- 사용자가 가이드를 보고 판단 후 직접 구현
- Day별 오전/오후/저녁 단위로 가이드 제공
- 구현 후 다음 단계 가이드 요청 시 진행
- smartnote 프로젝트 내 모든 파일은 지시 없이도 자유롭게 읽기 가능

## 코딩 컨벤션
- Python 3.11+, 타입 힌트 필수
- 포맷터: Black, 린터: Ruff
- 비용 최소화: 분류/검색은 Haiku, 콘텐츠 보완만 Sonnet 고려
- 과도한 추상화 지양, 실용성 우선
