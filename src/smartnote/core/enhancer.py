"""
내용 보완 모듈

사용자의 간단한 메모를 완성도 높은 학습 노트로 변환합니다.
- 구조 추가 (기승전결)
- 부족한 설명 보완
- 예제 코드 생성
- 연관 노트 링크 추가
"""

import os
from typing import Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class ContentEnhancer:
    """내용 보완기"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"

    def enhance(
        self,
        original_content: str,
        analysis: Dict[str, Any],
        classification: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        내용을 보완합니다.

        Args:
            original_content: raw text or markdown
            analysis: 내용 분석 결과
            classification: 카테고리 분류 결과

        Returns:
            {
                "enhanced_content": "보완된 마크다운",
                "changes": ["추가된 섹션1", "보완된 부분2"],
                "metadata": {
                    "title": "...",
                    "category": "...",
                    "tags": [...],
                    "related": [...]
                }
            }
        """
        # TODO: Claude API로 내용 보완
        # TODO: 구조 추가 (## 개념, ## 예시, ## 정리)
        # TODO: 부족한 설명 보완
        # TODO: 코드 예제 생성
        # TODO: 연관 노트 링크 [[...]] 추가
        # TODO: YAML frontmatter 생성

        # 임시 반환값
        enhanced = f"""---
title: "{analysis.get('topic', 'Untitled')}"
category: {classification.get('primary_category', 'Uncategorized')}
tags: {classification.get('recommended_tags', [])}
created: 2026-02-13
updated: 2026-02-13
related: []
---

{original_content}

## TODO
- 내용 보완 필요
- 예제 추가 필요
"""

        return {
            "enhanced_content": enhanced,
            "changes": ["YAML frontmatter 추가 (TODO)", "구조 정리 필요 (TODO)"],
            "metadata": {
                "title": analysis.get("topic", "Untitled"),
                "category": classification.get("primary_category", "Uncategorized"),
                "tags": classification.get("recommended_tags", []),
                "related": [],
            },
        }

    def add_related_links(self, content: str, similar_notes: list) -> str:
        """
        연관 노트 링크를 추가합니다.

        Args:
            content: 마크다운 내용
            similar_notes: RAG로 찾은 유사 노트들

        Returns:
            링크가 추가된 마크다운
        """
        # TODO: RAG 결과를 바탕으로 [[note-name]] 링크 추가
        # TODO: 적절한 위치에 자연스럽게 삽입

        return content


def enhance_content(
    original_content: str, analysis: Dict[str, Any], classification: Dict[str, Any]
) -> Dict[str, Any]:
    """
    편의 함수: 내용 보완

    Args:
        original_content: 원본
        analysis: 분석 결과
        classification: 분류 결과

    Returns:
        보완 결과
    """
    enhancer = ContentEnhancer()
    return enhancer.enhance(original_content, analysis, classification)


# 테스트 코드
if __name__ == "__main__":
    test_content = "# Rust Ownership\n메모리 자동 해제"
    test_analysis = {"topic": "Rust Ownership", "difficulty": "Intermediate"}
    test_classification = {
        "primary_category": "Language",
        "recommended_tags": ["rust", "memory"],
    }

    result = enhance_content(test_content, test_analysis, test_classification)
    print("보완 결과:")
    print(result["enhanced_content"])
