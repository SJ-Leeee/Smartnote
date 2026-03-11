# SmartNote AI - CLAUDE.md

## 프로젝트 개요
AI 에이전트가 마크다운 메모를 받아 **다듬기 → 사용자 피드백 → 저장** 자동화 CLI 도구.
포트폴리오 목적. 2주 집중 개발 (2026-02-10 ~ 2026-02-24).

## 현재 진행 상태
- **완료**: Day 1~8 (Setup → Content Enhancement → Storage → Feedback Loop → Category System → RAG Foundation → MVP 통합 & 실전 테스트 → Bulk Migration)
- **다음**: Day 9 (LangGraph 병렬화)
- **브랜치**: `feat/workflow-test`

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
- LLM 기반 카테고리 자동 분류 (방법4 하이브리드, haiku)
- Obsidian 2단계 폴더 구조 (대분류/중분류)
- Notion Category + Subcategory 2컬럼 분리
- 태그 영문 소문자 정규화
- E2E 전체 시나리오 검증 완료
- ChromaDB + sentence-transformers 기반 EmbeddingStore 구현
- `paraphrase-multilingual-MiniLM-L12-v2` 한국어 지원 임베딩 모델 적용
- 코사인 유사도 기반 연관 노트 검색 (threshold 0.5)
- Obsidian frontmatter `related:` 필드 자동 삽입 (`[[파일명|제목]]` alias 형식)
- 자기 자신 연관 노트 제외 로직 (exclude_title)
- ChromaDB upsert + file_path 기반 ID로 중복 방지
- DB 초기화/조회 스크립트 (`scripts/reset_chromadb.py`)
- `NoteState` 초기화 시 `user_feedback_text` 누락 버그 수정
- 연관 노트 코사인 유사도 threshold 0.5 활성화 (distance > 0.5 제외)
- ChromaDB 빈 상태(첫 노트 저장) 방어 코드 추가
- Notion 100 블록 제한 → 100개 단위 청크 append 처리
- `enhancer.py` max_tokens 4096 → 8096 (대용량 파일 잘림 방지)
- 큰 파일(8000 bytes 이상) 경고 메시지 추가
- 실전 테스트 10개 노트 저장 완료 (E2E 검증)
- `bulk` 커맨드 구현 - 기존 노트 일괄 분류 + ChromaDB 임베딩 (enhance 없음)
- `is_embedded()` 메서드 추가 - 중복 임베딩 방지
- `etc / Uncategorized` 카테고리 - confidence ≤ 0.8 자동 배정
- `note_id` 전략 변경: obsidian_path → 원본 소스 파일 절대 경로 (save/bulk 통일)
- 기존 809개 노트 마이그레이션 완료

## 기술 결정 사항 (변경 이력)
- **Tistory → Notion**: Tistory OpenAPI 2024년 종료로 Notion API 사용
- **Analyzer 노드 제거**: 과도한 추상화로 판단. Enhancer가 분석+보완 통합 담당
- **롤백 로직 → 부분 성공 허용**: Notion 실패 시 Obsidian 보존 (try/except 방식)
- **Workflow 단순화**: 5노드 → 3노드 (enhance/feedback/save)
- **input() → prompt_toolkit**: 한글 Wide Character 잔상 버그로 교체
- **Notion 이미지 블록 변환**: 미구현 상태로 보류, 추후 처리 예정
- **카테고리 체계 전면 개편** (Day 5): 기존 7개 단순 목록 → 5대분류/15중분류 계층 구조
- **카테고리 분류 알고리즘** (Day 5): 방법4 하이브리드 - confidence > 0.8이면 추천+확인, ≤ 0.8이면 선택지 2~3개 제시
- **카테고리 LLM 호출 타이밍** (Day 5): A(Accept) 누른 후 호출. E(Edit) 루프 중에는 비용 낭비이므로 미호출
- **태그 UX 변경** (Day 5): enhancer 생성 태그 자동 적용 + 사용자는 추가만 가능, 영문 소문자 정규화
- **Obsidian/Notion 역할 분리** (Day 5): Obsidian=파일시스템 탐색(폴더 계층), Notion=DB 검색/조회
- **Obsidian 폴더 구조** (Day 5): 2단계 폴더 (`vault/Tech & Engineering/Stack & Framework/파일명.md`)
- **Notion 카테고리 컬럼** (Day 5): `Category` select(대분류) + `Subcategory` select(중분류) 2컬럼으로 분리
- **Notion 연관 노트**: Day 6-7 RAG 구현 후 구현 예정 (지금은 미구현)
- **카테고리 설정 고도화**: 기본 카테고리를 사용자가 수정 가능한 config로 분리 → 고도화 단계 예정
- **임베딩 모델**: `paraphrase-multilingual-MiniLM-L12-v2` (한영 지원, 로컬, 무료)
- **ChromaDB note_id**: `uuid.uuid4()` → `obsidian_path` → **원본 소스 파일 절대 경로** (Day 8: save/bulk 통일, 중복 방지)
- **Obsidian related 링크**: `[[파일명|제목]]` alias 형식 (날짜 포함 파일명 + 사람이 읽기 좋은 제목)
- **bulk 마이그레이션** (Day 8): enhance 제외, classify + embed only. 원본 파일 유지, vault에 새 파일 생성. confidence ≤ 0.8 → etc 자동 배정. 809개 완료.
- **enhancer max_tokens**: 4096 → 8096 (대용량 파일 Tool Call JSON 잘림 방지)
- **Notion 블록 청킹**: API 한 번에 최대 100개 제한 → 100개 단위로 분할 append
- **연관 노트 threshold**: 0.5 활성화 (cosine distance > 0.5 제외) - 실전 테스트로 수치 검증
- **list 명령어**: 실사용 불필요 판단 → 보류

## 핵심 파일 구조
```
src/smartnote/
├── cli.py              # CLI 진입점 (Typer) - save 명령어 완성
├── core/
│   ├── workflow.py     # LangGraph StateGraph - enhance→feedback(A: classify+save, E: enhance)
│   ├── enhancer.py     # Claude API Tool Calling (haiku-4-5)
│   ├── analyzer.py     # 스텁 (미사용)
│   └── classifier.py   # 완성 - 방법4 하이브리드 분류 (haiku-4-5)
├── storage/
│   ├── obsidian.py     # 완성 - 2단계 폴더, tags frontmatter 반영
│   └── notion.py       # 완성 - Category+Subcategory 2컬럼
├── rag/
│   └── embedding_store.py  # 완성 - ChromaDB + sentence-transformers, 코사인 유사도 검색
├── recommender/        # Day 8-12 예정
└── integrations/       # Day 13 예정 (Slack)
prompts/
├── enhancer.txt        # Claude 시스템 프롬프트 ({today}, 태그 영문 소문자 규칙)
└── classifier.txt      # 카테고리 체계 전달용 프롬프트
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
- **RAG**: ChromaDB + sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`)
- **패키지 관리**: Poetry

## 카테고리 체계 (Day 5 확정)

**대분류 5개 / 중분류 15개** - `prompts/classifier.txt`에 전체 설명 포함하여 LLM에 전달

| 대분류 | 중분류 |
|---|---|
| Tech & Engineering | Stack & Framework, Infrastructure & DevOps, Database & Cache, Software Architecture |
| Computer Science | Algorithm & DS, CS Fundamentals, Security |
| Work & Project | Issue Log, Retrospective, Tech Lead & Culture |
| Growth & Career | Seminar & Conference, Book Review, Networking |
| Life | Travel & Hobby, Thoughts |

- **Obsidian 저장 경로**: `vault/Tech & Engineering/Stack & Framework/파일명.md`
- **Notion 저장**: `Category` select = "Tech & Engineering", `Subcategory` select = "Stack & Framework"
- **중분류 미해당 시**: LLM이 새 이름 자유 제안 → Obsidian(mkdir), Notion(select 자동 생성) 모두 자동 처리
- **기본 카테고리 수정 기능**: 고도화 단계에서 config.yaml로 분리 예정

## 앞으로의 Day별 계획
- **Day 7**: ✅ MVP 통합 & 실전 테스트 (10개 노트) - 완료
- **Day 8+**: Intelligent Categorization, Related Notes, CLI Enhancement, config.yaml 카테고리 수정 기능

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
