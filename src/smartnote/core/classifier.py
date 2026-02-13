"""
카테고리 분류 모듈

Primary Category + Tags 시스템으로 노트를 분류합니다.
- Few-shot learning으로 일관성 보장
- 확신도 기반 추천
- 사용자 최종 선택
"""

import os
from typing import Dict, Any, List
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class CategoryClassifier:
    """카테고리 분류기"""

    def __init__(self, config: Dict[str, Any] = None):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"
        self.config = config or self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """기본 카테고리 설정"""
        return {
            "categories": [
                {
                    "name": "Algorithm",
                    "description": "순수 알고리즘 이론 및 구현",
                    "examples": ["Binary Search", "QuickSort", "Dijkstra"],
                    "keywords": ["정렬", "탐색", "그래프", "알고리즘"]
                },
                {
                    "name": "Data Structure",
                    "description": "자료구조",
                    "examples": ["Red-Black Tree", "Hash Table"],
                    "keywords": ["트리", "해시", "배열", "자료구조"]
                },
                {
                    "name": "CS",
                    "description": "컴퓨터 과학 이론",
                    "examples": ["TCP vs UDP", "Process vs Thread"],
                    "keywords": ["네트워크", "운영체제", "데이터베이스"]
                },
                {
                    "name": "Language",
                    "description": "프로그래밍 언어 문법 및 특성",
                    "examples": ["Rust Ownership", "Python GIL"],
                    "keywords": ["문법", "언어", "컴파일러"]
                },
                {
                    "name": "DevOps",
                    "description": "배포, 인프라, CI/CD",
                    "examples": ["Docker 컨테이너", "GitHub Actions"],
                    "keywords": ["docker", "배포", "인프라", "cicd"]
                },
                {
                    "name": "AI",
                    "description": "인공지능, 머신러닝",
                    "examples": ["RAG 기초", "Transformer 구조"],
                    "keywords": ["llm", "머신러닝", "딥러닝"]
                },
                {
                    "name": "Tools",
                    "description": "라이브러리, 프레임워크, 도구",
                    "examples": ["Typer CLI", "LangChain 사용법"],
                    "keywords": ["라이브러리", "프레임워크", "도구"]
                }
            ]
        }

    def classify(
        self,
        content: str,
        title: str = "",
        analysis: Dict[str, Any] = None
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
        # TODO: Few-shot learning 구현
        # TODO: 기존 카테고리 예시를 프롬프트에 포함
        # TODO: Claude API로 분류 (Temperature = 0)
        # TODO: 확신도 계산
        # TODO: RAG로 유사 노트 참고 (나중에)

        # 임시 반환값
        return {
            "primary_category": "Tools",
            "primary_confidence": 0.65,
            "suggestions": [
                {
                    "category": "Tools",
                    "confidence": 0.65,
                    "reason": "라이브러리 사용법 위주"
                },
                {
                    "category": "Language",
                    "confidence": 0.25,
                    "reason": "Python 관련 내용"
                }
            ],
            "recommended_tags": ["python", "cli", "library"],
            "related_categories": ["Language"]
        }

    def suggest_subdivision(self, category: str, notes: List[Dict]) -> Dict[str, Any]:
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
        # TODO: 노트 10개 이상 체크
        # TODO: Claude API로 서브분류 분석
        # TODO: 의미 있는 그룹 2-5개 생성

        return {
            "should_subdivide": False,
            "subdivisions": []
        }


def classify_category(
    content: str,
    title: str = "",
    analysis: Dict[str, Any] = None
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
    test_content = """
# Typer와 CLI Boilerplate

Typer는 Python CLI 애플리케이션을 쉽게 만들 수 있는 라이브러리입니다.
"""

    result = classify_category(test_content, "Typer Boilerplate")
    print("분류 결과:", result)
