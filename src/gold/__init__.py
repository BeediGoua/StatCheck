"""Gold / oracle datasets for StatCheck evaluation."""

from src.gold.micro_gold_v0 import (
    MicroGoldCase,
    load_micro_gold_v0,
    MICRO_GOLD_V0_PATH,
)

__all__ = [
    "MicroGoldCase",
    "load_micro_gold_v0",
    "MICRO_GOLD_V0_PATH",
]
