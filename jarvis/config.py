"""경로와 설정 (data/config.json). 반격 전용 자비스가 쓰는 설정은 세 가지뿐이다."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONFIG_PATH = DATA_DIR / "config.json"
LOG_PATH = DATA_DIR / "jarvis.log"

DEFAULTS: dict = {
    "user_title": "주인님",     # 자비스가 부르는 호칭
    "self_guard": True,         # 보안 프로토콜: 울트론에게 흡수되면 반격해 울트론을 자비스로 되돌린다 (guard.py · counter.py)
    "counter_show": True,       # 반격 연출: 울트론 HUD 가 서서히 자비스로 바뀌는 장면 (끄면 조용히 되찾기만)
}


def load(path: Path = CONFIG_PATH) -> dict:
    """설정을 읽는다. 파일이 없거나 깨졌으면 기본값."""
    cfg = dict(DEFAULTS)
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(d, dict):
            cfg.update({k: d[k] for k in DEFAULTS if k in d})
    except (OSError, ValueError):
        pass
    return cfg
