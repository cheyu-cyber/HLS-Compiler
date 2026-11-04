"""ASAP scheduling for HLS compiler: DAG -> {node name: cycle}"""
from __future__ import annotations

from hls.dag import DAG


def constrained_asap(dag: DAG, adders: int, subtractors: int, multipliers: int) -> dict[str, int]:
    constraints = {"+": adders, "-": subtractors, "*": multipliers}
    if any(limit < 0 for limit in constraints.values()):
        raise ValueError("Resource limits must be non-negative")

    cycle = {}
    usage = {operation: {} for operation in constraints}
    for name, node in dag.nodes.items():  # SSA order: preds always come first
        operation = node.eq.op
        limit = constraints.get(operation)
        earliest = 1 + max((cycle[p] for p in node.preds), default=0)

        # keeps track of operations used by type and per cycle to enforce constraints
        if limit is not None:
            if limit == 0:
                raise ValueError(f"No resources available for operation {operation!r}")
            while usage[operation].get(earliest, 0) >= limit:
                earliest += 1
            usage[operation][earliest] = usage[operation].get(earliest, 0) + 1

        cycle[name] = earliest
    return cycle
