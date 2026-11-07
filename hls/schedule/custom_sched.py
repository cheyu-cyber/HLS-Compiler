"""Custom schedule: DAG -> {node name: cycle}"""
from __future__ import annotations

from hls.dag import DAG
from hls.schedule.asap import asap
from hls.schedule.alap import alap


def custom(dag: DAG, adders: int, subtractors: int, multipliers: int) -> dict[str, int]:
    limits = {"+": adders, "-": subtractors, "*": multipliers}
    early, late = asap(dag), alap(dag)
    diff = {name: late[name] - early[name] for name in dag.nodes}   # 0 = on the critical path

    cycle, c = {}, 0
    while len(cycle) < len(dag.nodes):
        c += 1
        ready = [name for name, node in dag.nodes.items()
                 if name not in cycle and all(cycle.get(p, c) < c for p in node.preds)]
        used = {op: 0 for op in limits}
        for name in sorted(ready, key=lambda name: diff[name]):     # most urgent first
            op = dag.nodes[name].eq.op
            if used[op] < limits[op]:
                cycle[name] = c
                used[op] += 1
    return {name: cycle[name] for name in dag.nodes}   # back to SSA order
