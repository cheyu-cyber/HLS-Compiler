"""
Parser for HLS compiler: equation text -> list[Equation].
"""
from __future__ import annotations

from dataclasses import dataclass

KEYWORDS = ("=", "+", "-", "*")


@dataclass(frozen=True)
class Equation:
    dest: str
    op: str
    lhs: str
    rhs: str

    def __str__(self) -> str:
        return f"{self.dest} = {self.lhs} {self.op} {self.rhs}"


def parse_hls(text: str) -> list[Equation]:
    equations = []
    for line in text.splitlines():
        if not line.strip():
            continue
        for kw in KEYWORDS:
            line = line.replace(kw, f" {kw} ")
        dest, _, lhs, op, rhs = line.split()
        equations.append(Equation(dest, op, lhs, rhs))
    return equations
