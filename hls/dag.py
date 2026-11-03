"""DAG for HLS compiler"""
from __future__ import annotations

from dataclasses import dataclass, field

from hls.parser import Equation


@dataclass
class Node:
    eq: Equation                                     # e.g. Z_0 = X_0 - B
    preds: list[str] = field(default_factory=list)   # nodes it waits on
    succs: list[str] = field(default_factory=list)   # nodes that use its result


@dataclass
class DAG:
    nodes: dict[str, Node]    # SSA name -> node, in SSA order
    inputs: list[str]         # read but never computed (A, B)
    outputs: list[str]        # results nobody else uses


def build_dag(ssa: list[Equation]) -> DAG:
    nodes, inputs = {}, []
    for eq in ssa:
        node = Node(eq)
        for operand in (eq.lhs, eq.rhs):
            if operand in nodes:
                node.preds.append(operand)
                nodes[operand].succs.append(eq.dest)
            elif operand not in inputs:
                inputs.append(operand)
        nodes[eq.dest] = node
    outputs = [name for name, node in nodes.items() if not node.succs]
    return DAG(nodes, inputs, outputs)
