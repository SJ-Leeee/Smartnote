# Typer와 CLI Boilerplate

Typer는 Python에서 CLI 애플리케이션을 쉽게 만들 수 있는 라이브러리입니다.

## 주요 특징
- 타입 힌트 기반 자동 CLI 생성
- Rich와 통합으로 예쁜 출력
- 자동 도움말 생성

## 예제
```python
import typer

app = typer.Typer()

@app.command()
def hello(name: str):
    print(f"Hello {name}")

if __name__ == "__main__":
    app()
```

## 정리
Boilerplate 코드를 최소화하면서 강력한 CLI를 만들 수 있습니다.
