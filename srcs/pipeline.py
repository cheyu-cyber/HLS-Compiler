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
from hls.schedule.constrained_asap import constrained_asap
from hls.schedule.constrained_alap import constrained_alap
from hls.gen_tools.datapath import build_datapath_plan
from hls.gen_tools.fsm_ctrl import build_fsm_plan
from hls.gen_tools.verilog_gen import generate_verilog


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

    limits = (args.adders, args.subtractors, args.multipliers)
    if any(limit is not None and limit < 0 for limit in limits):
        raise ValueError("Resource limits must be non-negative")

    schedules = {"asap": asap(dag),
                 "alap": alap(dag),
                 "HW3_alap": sequential_alap(dag),
                 "constrained_asap": constrained_asap(dag, limits[0], limits[1], limits[2]),
                 "constrained_alap": constrained_alap(dag, limits[0], limits[1], limits[2])}

    if args.verbose:
        for name, cycles in schedules.items():
            print(f"{name.upper()} schedule:\n{format_schedule(dag, cycles)}")
    # report()

    datapath_plan = build_datapath_plan(dag, schedules[args.make_schedule], args.width)
    export(args, "datapath", str(datapath_plan))
    fsm_plan = build_fsm_plan(datapath_plan)
    export(args, "fsm", str(fsm_plan))
    verilog = generate_verilog(datapath_plan, fsm_plan)
    export(args, "verilog", verilog, ext="v")

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
