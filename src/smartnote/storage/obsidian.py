import os
import re

from datetime import date
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

import yaml

load_dotenv()  # 어디든 호출하면 같은 프로세스에 대해서 등록됨. 테스트용


class ObsidianStorage:
    def __init__(self, vault_path: Optional[str] = None):
        path = vault_path or os.getenv("OBSIDIAN_VAULT_PATH", "")
        if not path:
            raise ValueError("obsidian vault path가 설정되지 않았습니다.")
        self.vault = Path(path)

    def save(self, content: str, metadata: dict) -> str:
        title = metadata.get("title") or "untitled"  # 제목 없으면 기본값
        category = metadata.get("category") or "Uncategorized"  # Day5 전까지 기본값
        subcategory = metadata.get("subcategory") or ""  # Day5 전까지 기본값

        content = self._inject_dates(content, metadata)  # frontmatter에 날짜 보강
        filename = self._build_filename(title)  # "2026-02-26-제목.md" 생성

        directory = (
            self.vault / category / subcategory
            if subcategory
            else self.vault / category
        )  # vault/Uncategorized 경로 조합
        directory.mkdir(parents=True, exist_ok=True)  # 폴더 없으면 생성

        save_path = self._resolve_path(directory, filename)  # 중복 파일명 처리
        save_path.write_text(content, encoding="utf-8")  # 실제 파일 저장
        return str(save_path)  # 저장 경로 반환

    def _build_filename(self, title: str) -> str:
        today = date.today().isoformat()  # "2026-02-26"
        slug = re.sub(r"[^\w\s가-힣]", "", title)  # 특수문자 제거
        slug = re.sub(r"\s+", "-", slug.strip())  # 공백 → 하이픈
        slug = slug.lower()
        return f"{today}-{slug}.md"

    def _inject_dates(self, content: str, metadata: dict = None) -> str:
        """
        처리 흐름:
        1. content 앞에 "---\n...\n---\n" 패턴 찾기 (frontmatter 유무 확인)

        2-A. frontmatter 없으면 → 날짜 포함한 frontmatter 통째로 앞에 붙이기
        2-B. frontmatter 있으면 → yaml 파싱 후
            - created 없으면 오늘 날짜 추가
            - updated 는 항상 오늘로 갱신
            - 다시 조립해서 반환
        """
        today = date.today().isoformat()
        content = content.lstrip("\n\r ")  # 앞 공백제거

        match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
        if not match:
            # frontmatter 자체가 없는 경우
            tags = metadata.get("tags", []) if metadata else []
            header = f"---\ncreated: {today}\nupdated: {today}\ntags: {tags}\n---\n\n"
            return header + content

        fm_text = match.group(1)  # --- 사이의 텍스트만 추출
        fm = yaml.safe_load(fm_text) or {}  # dict로 파싱 (비어있으면 {})

        if "created" not in fm:
            fm["created"] = today
        fm["updated"] = today  # 항상 갱신
        if metadata and metadata.get("tags"):
            fm["tags"] = metadata["tags"]  # 사용자가 추가한 태그 포함하여 덮어쓰기

        new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False).strip()
        new_header = f"---\n{new_fm}\n---\n"
        body = content[match.end() :]  # frontmatter 이후 본문
        return new_header + body

    def _resolve_path(self, directory: Path, filename: str) -> Path:
        """
        중복 파일명 처리.

        처리흐름:
        2026-02-26-react.md 있으면
        → 2026-02-26-react-1.md
        → 2026-02-26-react-2.md  (1도 있으면)
        """
        path = directory / filename
        if not path.exists():
            return path  # 중복 없으면 그대로 반환

        stem = Path(filename).stem  # "2026-02-26-react"
        suffix = Path(filename).suffix  # ".md"
        counter = 1
        while path.exists():
            path = directory / f"{stem}-{counter}{suffix}"
            counter += 1
        return path


if __name__ == "__main__":
    storage = ObsidianStorage()

    test_content = """
    ---
# 텍스트
title: 제목

# 날짜
date: 2026-02-26

# 태그 (배열)
tags:
  - backend
  - nodejs

# 체크박스
published: false

# 숫자
priority: 1
---
  # 테스트 노트
  내용입니다.
  """

    test_metadata = {
        "title": "테스트 노트",
        "tags": ["python", "test"],
        "summary": "테스트용 노트입니다",
    }

    path = storage.save(test_content, test_metadata)
    print(f"저장 완료: {path}")
