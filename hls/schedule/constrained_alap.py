"""Constrained ALAP scheduling for HLS compiler"""
from __future__ import annotations

from hls.dag import DAG
from hls.schedule.constrained_asap import constrained_asap


def constrained_alap(dag: DAG, adders: int, subtractors: int, multipliers: int) -> dict[str, int]:
    # Implementation for constrained ALAP scheduling
    latency = max(constrained_asap(dag, adders, subtractors, multipliers).values(), default=0)
    cycle = {}
    for name, node in reversed(dag.nodes.items()):   # backward from a bound (SSA order)
        cycle[name] = min((cycle[s] for s in node.succs), default=latency + 1) - 1
    return {name: cycle[name] for name in dag.nodes}   # back to SSA order
