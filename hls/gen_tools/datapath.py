"""Build a resource and register plan for a scheduled DAG."""
from __future__ import annotations

from dataclasses import dataclass

from hls.dag import DAG

OPERATORS = ("+", "-", "*")
_OPERATOR_NAMES = {"+": "add", "-": "sub", "*": "mul"}


@dataclass(frozen=True)
class FunctionalUnit:
    """One reusable hardware unit of a particular operation type."""

    operator: str
    index: int

    @property
    def name(self) -> str:
        return f"{_OPERATOR_NAMES[self.operator]}_{self.index}"


@dataclass(frozen=True)
class DatapathPlan:
    """Allocation metadata shared by datapath and controller generation."""

    width: int
    schedule: dict[str, int]
    operations_by_cycle: dict[int, tuple[str, ...]]
    operation_counts: dict[int, dict[str, int]]
    units_by_operator: dict[str, tuple[FunctionalUnit, ...]]
    node_to_unit: dict[str, FunctionalUnit]
    operation_inputs: dict[str, tuple[str, str]]
    registers: dict[str, str]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]


def _validate_schedule(dag: DAG, schedule: dict[str, int]) -> None:
    missing = dag.nodes.keys() - schedule.keys()
    extra = schedule.keys() - dag.nodes.keys()
    if missing or extra:
        raise ValueError(
            f"Schedule must contain exactly the DAG nodes "
            f"(missing: {sorted(missing)}, extra: {sorted(extra)})"
        )

    for name, cycle in schedule.items():
        if type(cycle) is not int or cycle < 1:
            raise ValueError(f"Cycle for node {name!r} must be a positive integer")


def operation_counts_by_cycle(
    dag: DAG, schedule: dict[str, int]
) -> dict[int, dict[str, int]]:
    """Count scheduled operations by cycle and operator.
    counts is a dictionary like:
    {1: {"+": 2, "-": 1, "*": 0}, 2: {"+": 0, "-": 1, "*": 1}}"""
    _validate_schedule(dag, schedule)
    counts: dict[int, dict[str, int]] = {}
    for name, node in dag.nodes.items():
        if node.eq.op not in OPERATORS:
            raise ValueError(f"Unsupported operation {node.eq.op!r} at node {name!r}")
        cycle_counts = counts.setdefault(schedule[name], {op: 0 for op in OPERATORS})
        cycle_counts[node.eq.op] += 1
    return counts


def build_datapath_plan(
    dag: DAG, schedule: dict[str, int], width: int = 6
) -> DatapathPlan:
    """Bind scheduled operations to the minimum reusable units for that schedule.

    Unit indices are assigned in DAG order within each cycle. Values currently
    receive one register each; liveness-based register sharing can be added later.
    Inputs are 3 bits wide, and the internal datapath width may range from 3 to 6.
    """
    if not 3 <= width <= 6:
        raise ValueError("Datapath width must be between 3 and 6 bits")

    counts = operation_counts_by_cycle(dag, schedule)
    latency = max(schedule.values(), default=0)
    operations_by_cycle = {
        cycle: tuple(name for name in dag.nodes if schedule[name] == cycle)  # all node names scheduled for this cycle
        for cycle in range(1, latency + 1)
    }  # something like: operations_by_cycle = {1: ("a",), 2: ("b", "c"), 3: (), 4: ("d",)}

    # create a hardware inventory
    units_by_operator: dict[str, tuple[FunctionalUnit, ...]] = {}
    for operator in OPERATORS:
        unit_count = max(
            (cycle_counts[operator] for cycle_counts in counts.values()), default=0
        )  # count maximum number of units needed for this operator across all cycles
        units_by_operator[operator] = tuple(
            FunctionalUnit(operator, index) for index in range(unit_count)
        )  # create the units for this operator

    # build out the mapping of nodes to units and their inputs
    node_to_unit: dict[str, FunctionalUnit] = {}
    operation_inputs: dict[str, tuple[str, str]] = {}
    for names in operations_by_cycle.values():
        assigned: dict[str, int] = {operator: 0 for operator in OPERATORS}
        for name in names:
            node = dag.nodes[name]
            operator = node.eq.op
            node_to_unit[name] = units_by_operator[operator][assigned[operator]]
            assigned[operator] += 1
            operation_inputs[name] = (node.eq.lhs, node.eq.rhs)

    # populate the register mapping for all nodes, inputs, and outputs
    registers = {name: f"reg_{index}" for index, name in enumerate(dag.nodes)}

    return DatapathPlan(
        width=width,
        schedule=dict(schedule),
        operations_by_cycle=operations_by_cycle,
        operation_counts=counts,
        units_by_operator=units_by_operator,
        node_to_unit=node_to_unit,  # ex: {"Z_0": FunctionalUnit(operator="-", index=0)}
        operation_inputs=operation_inputs,
        registers=registers,
        inputs=tuple(dag.inputs),
        outputs=tuple(dag.outputs),
    )
