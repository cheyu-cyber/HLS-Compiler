"""Build per-state control metadata for a scheduled datapath."""
from __future__ import annotations

from dataclasses import dataclass

from hls.gen_tools.datapath import DatapathPlan


@dataclass(frozen=True)
class FSMPlan:
    """State and control assignments needed to emit an FSM."""

    idle_state: str
    cycle_states: dict[int, str]
    done_state: str
    latency: int
    unit_selections_by_cycle: dict[int, dict[str, str]]
    register_writes_by_cycle: dict[int, tuple[str, ...]]


def build_fsm_plan(datapath: DatapathPlan) -> FSMPlan:
    """Translate a datapath allocation into per-cycle controller actions.

    ``unit_selections_by_cycle`` maps each active functional unit to the DAG
    node whose operands it should select. ``register_writes_by_cycle`` lists
    the destination registers to enable at the end of each cycle.
    """
    latency = max(datapath.schedule.values(), default=0)
    cycle_states = {cycle: f"CYCLE_{cycle}" for cycle in range(1, latency + 1)}
    unit_selections_by_cycle: dict[int, dict[str, str]] = {}
    register_writes_by_cycle: dict[int, tuple[str, ...]] = {}

    for cycle, nodes in datapath.operations_by_cycle.items():
        unit_selections: dict[str, str] = {}
        writes: list[str] = []
        for node in nodes:
            unit = datapath.node_to_unit[node]
            unit_selections[unit.name] = node
            writes.append(datapath.registers[node])
        unit_selections_by_cycle[cycle] = unit_selections
        register_writes_by_cycle[cycle] = tuple(writes)

    return FSMPlan(
        idle_state="IDLE",
        cycle_states=cycle_states,
        done_state="DONE",
        latency=latency,
        unit_selections_by_cycle=unit_selections_by_cycle,
        register_writes_by_cycle=register_writes_by_cycle,
    )
