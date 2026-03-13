import json
from anthropic import Anthropic
from pathlib import Path

client = Anthropic()
JUDGE_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "prompts/judge.txt"


def judge_quality(original: str, enhanced: str, tags: list[str]) -> dict:
    """보완본 품질을 sonnet으로 평가하여 점수 반환"""

    user_message = f"""
## 원본 노트 
{original}

## 보완된 노트
{enhanced}

## 생성된 태그
{', '.join(tags)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=JUDGE_PROMPT_PATH.read_text(encoding="utf-8"),
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    # JSON 파싱 (마크다운 코드블록 감싸진 경우 대비)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())
