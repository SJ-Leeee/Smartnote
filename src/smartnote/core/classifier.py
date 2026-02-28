"""
카테고리 분류 모듈

Primary Category + Tags 시스템으로 노트를 분류합니다.
- Few-shot learning으로 일관성 보장
- 확신도 기반 추천
- 사용자 최종 선택
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts" / "classifier.txt"


class CategoryClassifier:
    """카테고리 분류기"""

    def __init__(self, config: Dict[str, Any] = None):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-haiku-4-5-20251001"
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def classify(
        self, content: str, title: str = "", analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        노트를 분류합니다.

        Args:
            content: 마크다운 내용
            title: 제목
            analysis: analyzer에서 받은 분석 결과

        Returns:
            {
                "primary_category": "Tools",
                "primary_confidence": 0.65,
                "suggestions": [
                    {"category": "Tools", "confidence": 0.65, "reason": "..."},
                    {"category": "Language", "confidence": 0.25, "reason": "..."}
                ],
                "recommended_tags": ["python", "cli", "typer"],
                "related_categories": ["Language", "Concepts"]
            }
        """
        tool = {
            "name": "classify_note",
            "description": "노트의 카테고리를 분류합니다.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "primary_category": {
                        "type": "string",
                        "enum": [
                            "Tech & Engineering",
                            "Computer Science",
                            "Work & Project",
                            "Growth & Career",
                            "Life",
                        ],
                    },
                    "subcategory": {
                        "type": "string",
                        "description": "중분류. 기존 목록에 없으면 새 이름제안 가능.",
                    },
                    "confidence": {"type": "number"},
                    "reason": {"type": "string", "description": "분류 근거한 줄"},
                    "suggestions": {
                        "type": "array",
                        "description": "대안 후보 (최대 2개). 확실하면 빈배열.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "primary_category": {"type": "string"},
                                "subcategory": {"type": "string"},
                                "confidence": {"type": "number"},
                                "reason": {"type": "string"},
                            },
                            "required": [
                                "primary_category",
                                "subcategory",
                                "confidence",
                                "reason",
                            ],
                        },
                    },
                },
                "required": [
                    "primary_category",
                    "subcategory",
                    "confidence",
                    "reason",
                    "suggestions",
                ],
            },
        }

        user_message = f"제목: {title}\n\n{content}" if title else content
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            system=self.system_prompt,
            tools=[tool],  # tool
            tool_choice={"type": "tool", "name": "classify_note"},
            messages=[{"role": "user", "content": user_message}],
        )

        # 임시 반환값
        return response.content[0].input  # input이 LLM이 tool을 사용한 반환값

        # def suggest_subdivision(self, category: str, notes: List[Dict]) -> Dict[str, Any]:
        # 추후 고도화 작업
        """
        서브분류 제안 (10개 이상 쌓였을 때)

        Args:
            category: 대분류 (예: "Language")
            notes: 해당 카테고리의 노트 리스트

        Returns:
            {
                "should_subdivide": True/False,
                "subdivisions": [
                    {"name": "Rust", "notes": [...], "reason": "..."}
                ]
            }
        """


def classify_category(
    content: str, title: str = "", analysis: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    편의 함수: 카테고리 분류

    Args:
        content: 마크다운 내용
        title: 제목
        analysis: 분석 결과

    Returns:
        분류 결과
    """
    classifier = CategoryClassifier()
    return classifier.classify(content, title, analysis)


# 테스트 코드
if __name__ == "__main__":
    classifier = CategoryClassifier()

    tests = [
        ("Binary Search 구현", "이진탐색은 O(logN)..."),
        ("Typer CLI 보일러플레이트", "Typer는 Python CLI 라이브러리..."),
        ("카프카 비용 절감 회고", "업무 중 카프카 요금이 급증해서..."),
    ]

    for title, content in tests:
        result = classifier.classify(content, title)
        print(f"\n📝 {title}")
        print(
            f"   → {result['primary_category']} / {result['subcategory']}({result['confidence']:.0%})"
        )
        print(f"   근거: {result['reason']}")
        if result["suggestions"]:
            for s in result["suggestions"]:
                print(
                    f"   대안: {s['primary_category']} /{s['subcategory']} ({s['confidence']:.0%})"
                )
