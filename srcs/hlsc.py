"""
    compiler enter point           
"""
import argparse
import os
import sys
from pathlib import Path

from srcs import pipeline

def argparser(argv=None):
    parser = argparse.ArgumentParser(
        prog="hlsc", description="High-Level Synthesis Compiler")
    parser.add_argument("file", type=Path,
                        help="input equation file, one equation per line")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print the SSA form and the schedules")
    parser.add_argument("--export-ssa", action="store_true",
                        help="export the SSA form as a text file")
    parser.add_argument("--export-dag", action="store_true",
                        help="export the DAG as an SVG picture")
    parser.add_argument("--export-all", action="store_true",
                        help="export everything (same as all --export-* flags)")
    parser.add_argument("--adders", type=int, default=1, metavar="N",
                        help="max adders (constrained asap/alap, default: %(default)s)")
    parser.add_argument("--subtractors", type=int, default=1, metavar="N",
                        help="max subtractors (constrained asap/alap, default: %(default)s)")
    parser.add_argument("--multipliers", type=int, default=1, metavar="N",
                        help="max multipliers (constrained asap/alap, default: %(default)s)")
    parser.add_argument("--latency", type=int, metavar="N",
                        help="latency bound for alap (default: asap latency)")
    parser.add_argument("--width", type=int, default=3, metavar="BITS",
                        help="datapath bit-width (default: %(default)s)")
    parser.add_argument("--make-schedule", type=str, default="constrained_asap", metavar="STRING",
                        help="schedule to create datapath (default: %(default)s)")
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("output_log"),
                        help="output directory (default: %(default)s)")
    args = parser.parse_args(argv)
    if args.export_all:
        args.export_ssa = args.export_dag = True
    return args


def main(argv=None):
    args = argparser(argv)
    try:
        text = args.file.read_text(encoding="utf-8")
        results = pipeline.run(text,args)
    except OSError as exc:
        print(f"hlsc: error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
