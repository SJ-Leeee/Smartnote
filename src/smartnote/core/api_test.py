# .env 파일 로드
from dotenv import load_dotenv
from anthropic import Anthropic
import os

load_dotenv()


def test_claude_api():
    """Claude API 기본 테스트"""

    # API 클라이언트 생성
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # 간단한 메시지 전송
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "안녕하세요! 간단한 자기소개를 해주세요."}
        ],
    )
    # 응답 출력
    print("=" * 50)
    print("Claude API 응답:")
    print("=" * 50)
    print(message.content[0].text)
    print("=" * 50)
    print(message)

    return message


def test_structured_output():
    """구조화된 출력 테스트 (JSON)"""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": """
다음 마크다운 노트를 분석해서 JSON으로 답변해주세요:                                                
                                                                                                      
# Rust의 Ownership                                                                                  
변수가 scope를 벗어나면 메모리가 자동 해제됨.                                                       
C++의 RAII랑 비슷한 것 같음.                                                                        
                                                                                                    
응답 형식:                                                                                          
{                                                                                                   
    "topic": "주제",                                                                                  
    "category": "카테고리 (예: Programming Language)",                                                
    "difficulty": "난이도 (Beginner/Intermediate/Advanced)",                                          
    "completeness": "완성도 (1-10)"                                                                   
}                                                                                                   
                """,
            }
        ],
    )

    print("\n" + "=" * 50)
    print("구조화된 출력 테스트:")
    print("=" * 50)
    print(message.content[0].text)
    print("=" * 50)

    return message


if __name__ == "__main__":
    print("🚀 Claude API 테스트 시작\n")

    # 기본 테스트
    print("1️⃣ 기본 대화 테스트")
    test_claude_api()

    # 구조화된 출력 테스트
    print("\n2️⃣ 구조화된 출력 테스트")
    test_structured_output()

    print("\n✅ 모든 테스트 완료!")
