"""ALAP scheduling for HLS compiler"""
from __future__ import annotations

from hls.dag import DAG
from hls.schedule.asap import asap


def alap(dag: DAG) -> dict[str, int]:
    latency = max(asap(dag).values(), default=0)
    cycle = {}
    for name, node in reversed(dag.nodes.items()):   # backward from a bound (SSA order)
        cycle[name] = min((cycle[s] for s in node.succs), default=latency + 1) - 1
    return {name: cycle[name] for name in dag.nodes}   # back to SSA order


def sequential_alap(dag: DAG) -> dict[str, int]:
    # HW3 version, 1 op per cycle
    cycle = alap(dag)
    order = sorted(dag.nodes, key=lambda name: cycle[name])
    return {name: i for i, name in enumerate(order, start=1)}
