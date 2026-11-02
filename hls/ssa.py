"""SSA for HLS compiler"""
from __future__ import annotations

from hls.parser import Equation


def to_ssa(equations: list[Equation]) -> list[Equation]:
    assign_count = {}                    # var name -> times assigned so far
    ssa = []

    def latest(name):                    # X assigned twice so far -> X_1
        if name in assign_count:
            return f"{name}_{assign_count[name] - 1}"
        return name                      # never assigned -> primary input
    
    for eq in equations:

        lhs = latest(eq.lhs)
        rhs = latest(eq.rhs)
    
        assign_count[eq.dest] = assign_count.get(eq.dest, 0) + 1   # first assignment -> 1
        dest = latest(eq.dest)
    
        ssa.append(Equation(dest, eq.op, lhs, rhs))
    
    return ssa
    #
    # example:
    #     X = A + B    ->    X_0 = A + B
    #     X = X + A    ->    X_1 = X_0 + A
    #     Y = X * B    ->    Y_0 = X_1 * B

