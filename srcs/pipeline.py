"""hls compiler module: ssa-->build dag-->schedule-->generate verilog"""
from __future__ import annotations

import argparse
import os
import sys
from hls.parser import parse_hls
from hls.ssa import to_ssa
from hls.dag import build_dag
from srcs.svg_gen import dag_to_svg
from hls.schedule.asap import asap
from hls.schedule.alap import alap, sequential_alap
# from hls.schedule import constrained_asap, constrained_alap



def run(text: str, args: argparse.Namespace):
    equations = parse_hls(text)
    ssa = to_ssa(equations)
    if args.verbose:
        print("SSA:\n" + "\n".join(f"  {eq}" for eq in ssa))
    if args.export_ssa:
        export(args, "ssa", "\n".join(map(str, ssa)))

    dag = build_dag(ssa)
    if args.export_dag:
        export(args, "dag", dag_to_svg(dag), ext="svg")

    schedules = {"asap": asap(dag),
                 "alap": alap(dag),
                 "HW3 alap": sequential_alap(dag)}
    if args.verbose:
        for name, cycles in schedules.items():
            print(f"{name.upper()} schedule:\n{format_schedule(dag, cycles)}")
    # report()
    return None


def export(args: argparse.Namespace, name: str, content: str, ext: str = "txt"):
    path = args.out_dir / f"{args.file.stem}_{name}.{ext}"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n", encoding="utf-8")
    print(f"{name.upper()} written to: {path}")


def format_schedule(dag, cycles: dict[str, int]) -> str:
    lines = []
    for c in range(1, max(cycles.values(), default=0) + 1):
        ops = [str(dag.nodes[name].eq) for name, cyc in cycles.items() if cyc == c]
        lines.append(f"  cycle {c}: " + ", ".join(ops))
    return "\n".join(lines)
