import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent.parent.parent / "logs/quality_scores.jsonl"


def log_score(file_path: str, scores: dict, phase: str = "before_loop") -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "file": Path(file_path).name,
        "phase": phase,
        "original_preservation": scores.get("original_preservation"),
        "tag_quality": scores.get("tag_quality"),
        "readability": scores.get("readability"),
        "total": scores.get("total"),
        "issues": scores.get("issues", []),
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
