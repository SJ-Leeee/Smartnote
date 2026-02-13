"""
내용 분석 모듈

Claude API를 사용하여 마크다운 노트의 내용을 분석합니다.
- 주제 추출
- 난이도 판단
- 완성도 평가
"""

import os
from typing import Dict, Any
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class ContentAnalyzer:
    """노트 내용 분석기"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"

    def analyze(self, content: str, title: str = "") -> Dict[str, Any]:
        """
        노트 내용을 분석합니다.

        Args:
            content: 마크다운 내용
            title: 노트 제목 (선택)

        Returns:
            {
                "topic": "주제",
                "difficulty": "Beginner/Intermediate/Advanced",
                "completeness": 1-10,
                "key_concepts": ["개념1", "개념2"],
                "summary": "한 줄 요약"
            }
        """
        # TODO: Claude API로 실제 분석 구현
        # TODO: Structured output (JSON mode) 사용
        # TODO: Temperature = 0 for consistency

        # 임시 반환값
        return {
            "topic": title or "Unknown",
            "difficulty": "Intermediate",
            "completeness": 6,
            "key_concepts": ["concept1", "concept2"],
            "summary": "내용 분석 필요 (TODO)"
        }

    def extract_keywords(self, content: str) -> list[str]:
        """
        내용에서 키워드를 추출합니다.

        Args:
            content: 마크다운 내용

        Returns:
            키워드 리스트
        """
        # TODO: Claude API로 키워드 추출
        # TODO: 카테고리 분류에 활용할 수 있는 키워드 추출

        return ["keyword1", "keyword2", "keyword3"]


def analyze_content(content: str, title: str = "") -> Dict[str, Any]:
    """
    편의 함수: 내용 분석

    Args:
        content: 마크다운 내용
        title: 노트 제목

    Returns:
        분석 결과
    """
    analyzer = ContentAnalyzer()
    return analyzer.analyze(content, title)


# 테스트 코드
if __name__ == "__main__":
    test_content = """
# Rust의 Ownership

변수가 scope를 벗어나면 메모리가 자동 해제됨.
C++의 RAII랑 비슷한 것 같음.
"""

    result = analyze_content(test_content, "Rust Ownership")
    print("분석 결과:", result)
