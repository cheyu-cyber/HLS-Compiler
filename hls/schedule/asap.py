"""ASAP scheduling for HLS compiler: DAG -> {node name: cycle}"""
from __future__ import annotations

from hls.dag import DAG


def asap(dag: DAG) -> dict[str, int]:
    cycle = {}
    for name, node in dag.nodes.items():      # SSA order: preds always come first
        cycle[name] = 1 + max((cycle[p] for p in node.preds), default=0)
    return cycle
