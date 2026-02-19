"""
내용 보완 모듈

사용자의 raw text / 마크다운 메모를 완성도 높은 학습 노트로 변환합니다.
- 구조 추가 (글 성격에 맞는 섹션 자동 선택)
- 부족한 설명 보완
- YAML frontmatter 생성
"""

import os
from datetime import date
from pathlib import Path
from typing import Dict, Any

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "enhancer.txt"


class ContentEnhancer:
    """내용 보완기"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-haiku-4-5-20251001"
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        today = date.today().isoformat()
        template = PROMPT_PATH.read_text(encoding="utf-8")
        return template.replace("{today}", today)

    def enhance(self, original_content: str, title: str = "") -> Dict[str, Any]:
        """
        내용을 보완합니다.

        Args:
            original_content: raw text or 마크다운
            title: 파일명에서 추출한 제목 힌트 (선택)

        Returns:
            {
                "enhanced_content": "YAML frontmatter + 보완된 마크다운",
                "metadata": {
                    "title": "...",
                    "tags": [...],
                    "summary": "..."
                }
            }
        """
        user_message = original_content
        if title:
            user_message = f"파일 제목 힌트: {title}\n\n{original_content}"

        tool = {
            "name": "enhance_note",
            "description": "보완된 학습 노트를 저장합니다.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "보완/수정된 제목"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "태그 목록",
                    },
                    "summary": {"type": "string", "description": "한 줄 요약"},
                    "enhanced_content": {
                        "type": "string",
                        "description": "YAML frontmatter + 보완된 마크다운 전체",
                    },
                },
                "required": ["title", "tags", "summary", "enhanced_content"],
            },
        }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0,
            system=self.system_prompt,
            tools=[tool],
            tool_choice={"type": "tool", "name": "enhance_note"},
            messages=[{"role": "user", "content": user_message}],
        )

        data = response.content[0].input

        return {
            "enhanced_content": data["enhanced_content"],
            "metadata": {
                "title": data["title"],
                "tags": data["tags"],
                "summary": data["summary"],
            },
        }

    def add_related_links(self, content: str, similar_notes: list) -> str:
        """
        연관 노트 링크를 추가합니다. (Day 6 RAG 구현 후 활성화)
        """
        # TODO: RAG 결과를 바탕으로 [[note-name]] 링크 추가
        return content


def enhance_content(original_content: str, title: str = "") -> Dict[str, Any]:
    """
    편의 함수: 내용 보완

    Args:
        original_content: raw text or 마크다운
        title: 제목 힌트

    Returns:
        보완 결과
    """
    enhancer = ContentEnhancer()
    return enhancer.enhance(original_content, title)


# 테스트 코드
if __name__ == "__main__":
    test_content = """
                    # 스택이란?

                    대표적인 LIFO 알고리즘. 
                    """

    result = enhance_content(test_content, "Stack")
    print("=== 메타데이터 ===")
    print(f"제목: {result['metadata']['title']}")
    print(f"태그: {result['metadata']['tags']}")
    print(f"요약: {result['metadata']['summary']}")
    print("\n=== 보완된 내용 ===")
    print(result["enhanced_content"])
