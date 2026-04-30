from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.core.config import settings


def run() -> None:
    golden_path = settings.data_dir / "eval" / "golden.jsonl"
    runs_dir = settings.data_dir / "eval" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    if not golden_path.exists():
        print("No se encontró data/eval/golden.jsonl")
        return
    rows = []
    for line in golden_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_questions": len(rows),
        "keyword_recall": 0.0,
        "source_recall": 0.0,
        "latency_avg_ms": 0.0,
        "note": "Baseline evaluator scaffold. Integrar pipeline real en siguiente iteración.",
    }
    out = runs_dir / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
