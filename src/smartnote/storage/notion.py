import os
import re

from datetime import date
import textwrap


from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

"""
- notion_client.Client — 공식 Python SDK. client.pages.create(), client.blocks.children.append() 등
메서드 제공
- save는 단계가 많아서 먼저 주석으로 흐름 잡고 채워나갈 것
- _build_properties: Notion properties 딕셔너리 포맷 맞추는 게 핵심 (형식이 독특함)
- _markdown_to_blocks: 마크다운 → Notion block 배열 변환
"""

LANGUAGE_MAP = {
    "jsx": "javascript",
    "tsx": "typescript",
    "py": "python",
    "sh": "shell",
    "zsh": "shell",
    "bash": "bash",
    "js": "javascript",
    "ts": "typescript",
    "yml": "yaml",
    "md": "markdown",
    "tf": "plain text",
    "cpp": "c++",
}


def _make_heading(level: int, text: str) -> dict:
    heading_type = f"heading_{level}"
    return {
        "type": heading_type,
        heading_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


class NotionStorage:
    def __init__(self):
        token = os.getenv("NOTION_PRIVATE_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")

        if not token or not self.database_id:
            raise ValueError("Notion key 또는 Database id 오류")

        self.client = Client(auth=token)

    def save(self, content: str, metadata: dict) -> str:
        # 모든 줄의 공통 들여쓰기를 제외해준다. 실제로는 들여쓰기가 올일은 없음. 방어적코드.
        content = textwrap.dedent(content).strip()
        # 1. frontmatter 제거한 순수 본문 추출
        body = self._strip_frontmatter(content)

        # 2. properties 빌드
        properties = self._build_properties(metadata)

        # 3. Database에 빈 페이지 생성
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
        )
        """
        # response 객체
        {
            "id": "1a2b3c4d-...",           # 페이지 고유 ID
            "url": "https://notion.so/...", # 페이지 URL
            "created_time": "2026-02-26T...",
            "last_edited_time": "2026-02-26T...",
            "parent": {
                "type": "database_id",
                "database_id": "..."        # 어느 DB에 속하는지
            },
            "properties": {                 # 우리가 넣은 properties 그대로
                "Name": {...},
                "Category": {...},
                ...
            },
            "object": "page"
        }
        """

        page_id = response["id"]

        # 4. 본문 블록 추가
        blocks = self._markdown_to_blocks(body)
        CHUNK_SIZE = 100  # notion은 최대 100개 블록 제한이 있다.
        for i in range(0, len(blocks), CHUNK_SIZE):
            chunk = blocks[i : i + CHUNK_SIZE]
            self.client.blocks.children.append(block_id=page_id, children=chunk)

        # 5. 페이지 URL 반환
        return response["url"]

    def _strip_frontmatter(self, content: str) -> str:
        lines = [line.strip() for line in content.split("\n")]

        if not lines or lines[0] != "---":
            return content

        for i in range(1, len(lines)):
            if lines[i] == "---":
                return "\n".join(lines[i + 1 :]).lstrip("\n")

        return content

    def _build_properties(self, metadata: dict) -> dict:
        today = date.today().isoformat()  # "2026-02-26"

        title = metadata.get("title") or "untitled"
        category = metadata.get("category") or "Uncategorized"
        subcategory = metadata.get("subcategory") or ""
        tags = metadata.get("tags") or []  # ["python", "oop"]
        summary = metadata.get("summary") or ""

        # 전부다 API docs에 있음.
        properties = {
            # title 타입: 반드시 배열 → 텍스트 오브젝트 구조
            "Name": {"title": [{"text": {"content": title}}]},
            # select 타입: name 키에 문자열 하나
            "Category": {"select": {"name": category}},
            # multi_select 타입: {"name": "태그"} 딕셔너리의 배열
            # ["python", "oop"] → [{"name": "python"}, {"name": "oop"}]
            "Tags": {"multi_select": [{"name": tag} for tag in tags]},
            # rich_text 타입: title과 구조 동일하지만 키가 "rich_text"
            "Summary": {"rich_text": [{"text": {"content": summary}}]},
            # date 타입: start에 ISO 날짜 문자열
            "Created": {"date": {"start": today}},
        }
        if subcategory:  # 서브 카테고리 추가
            properties["Subcategory"] = {"select": {"name": subcategory}}  #

        return properties

    def _markdown_to_blocks(self, content: str) -> list[dict]:
        """
        마크다운을 block 화 시키는 메서드
        Notion Block 타입 목록은 docs Reference에 있으니까 필요할 때 찾아서 추가하면 된다.

        TODO:
        - 번호 마크다운추가
        - 인용문 마크다운 추가
        - 표 마크다운 추가
        - 굵게 마크다운 추가
        - #### 추가.. 없나?
        - #태그 처리
        """

        # YAML frontmatter 제거 (--- 로 감싼 부분)
        content = re.sub(r"^---\r?\n.*?\r?\n---\r?\n", "", content, flags=re.DOTALL)

        blocks = []
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            # TODO: tap 마크다운은 제외해야한다.
            line = lines[i].strip()  # 공백있으면 제거

            # 코드블록: ``` 시작 ~ ``` 끝까지 한 블록으로 묶음
            if line.startswith("```"):
                raw_lang = line[3:].strip().lower()
                language = LANGUAGE_MAP.get(raw_lang, raw_lang) or "plain text"
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])  # 코드내부는 공백제거 안함
                    i += 1
                blocks.append(
                    {
                        "type": "code",
                        "code": {
                            "language": language,
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "\n".join(code_lines)},
                                }
                            ],
                        },
                    }
                )

            elif line.startswith("### "):
                blocks.append(_make_heading(3, line[4:]))
            elif line.startswith("## "):
                blocks.append(_make_heading(2, line[3:]))
            elif line.startswith("# "):
                blocks.append(_make_heading(1, line[2:]))

            elif line.startswith("- "):
                blocks.append(
                    {
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {"type": "text", "text": {"content": line[2:]}}
                            ]
                        },
                    }
                )

            elif line.strip() == "":
                pass  # 빈 줄 무시

            else:
                blocks.append(
                    {
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": line}}]
                        },
                    }
                )

            i += 1

        return blocks


if __name__ == "__main__":
    storage = NotionStorage()

    test_content = """---
    title: "재밌는 노트"
    tags:
    - python
    - test
    summary: "테스트용 노트입니다"
    ---

    # 테스트 노트

    ## 개요

    내용입니다.

    - 항목 1
    - 항목 2

    ```python
    print("hello")
    ```

    - 바이요
    """

    test_metadata = {
        "title": "재밌는 노트",
        "tags": ["python", "test"],
        "summary": "테스트용 노트입니다",
    }

    url = storage.save(test_content, test_metadata)
    print(f"저장 완료: {url}")
