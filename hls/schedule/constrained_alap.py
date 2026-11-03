"""ALAP scheduling for HLS compiler"""
from __future__ import annotations

from hls.dag import DAG
from hls.schedule.asap import asap


def constrained_alap(dag: DAG) -> dict[str, int]:
    # Implementation for constrained ALAP scheduling
    pass
