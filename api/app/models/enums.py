from __future__ import annotations

from enum import Enum
from typing import Literal

Puissance = Literal[3, 6, 9, 12, 15, 18, 24, 30, 36]


class TariffOption(str, Enum):
    BASE = "BASE"
    HPHC = "HPHC"
    TEMPO = "TEMPO"


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    VERIFYING = "verifying"
    STALE = "stale"
    BROKEN = "broken"
