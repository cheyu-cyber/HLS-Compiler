"""Constrained ALAP scheduling for HLS compiler"""
from __future__ import annotations

from hls.dag import DAG
from hls.schedule.constrained_asap import constrained_asap


def constrained_alap(dag: DAG, adders: int, subtractors: int, multipliers: int) -> dict[str, int]:
    cycle = constrained_asap(dag, adders, subtractors, multipliers)
    latency = max(cycle.values(), default=0)
    constraints = {"+": adders, "-": subtractors, "*": multipliers}
    usage = {operation: {} for operation in constraints}

    for name, scheduled_cycle in cycle.items():  # get usage of each operation from ASAP schedule
        operation = dag.nodes[name].eq.op
        if operation in usage:
            usage[operation][scheduled_cycle] = usage[operation].get(scheduled_cycle, 0) + 1

    for name, node in reversed(dag.nodes.items()):  # reverse SSA order
        operation = node.eq.op
        limit = constraints.get(operation)
        current = cycle[name]
        latest = min((cycle[s] for s in node.succs), default=latency + 1) - 1
        latest = min(latest, latency)

        if limit is not None:
            """decrement latest until it matches current cycle or if cycle is at limit, 
            finds a cycle that isn't full and proceeds, or gives up at current cycle"""
            while latest > current and usage[operation].get(latest, 0) >= limit:
                latest -= 1

        if latest > current:  # update usage count if operation moves later
            if limit is not None:
                usage[operation][current] -= 1
                usage[operation][latest] = usage[operation].get(latest, 0) + 1
            cycle[name] = latest

    return cycle
