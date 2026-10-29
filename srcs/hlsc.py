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
    parser.add_argument("--export-ssa", action="store_true",
                        help="export the SSA form as a text file")
    parser.add_argument("-s", "--schedule", default="asap",
                        choices=["asap", "casap", "alap", "calap", "custom"],
                        help="scheduling mode: asap, constrained asap, alap, "
                             "constrained alap, custom (default: %(default)s)")
    parser.add_argument("--adders", type=int, metavar="N",
                        help="max adders (casap/calap)")
    parser.add_argument("--subtractors", type=int, metavar="N",
                        help="max subtractors (casap/calap)")
    parser.add_argument("--multipliers", type=int, metavar="N",
                        help="max multipliers (casap/calap)")
    parser.add_argument("--latency", type=int, metavar="N",
                        help="latency bound for alap/calap (default: asap latency)")
    parser.add_argument("--width", type=int, default=8, metavar="BITS",
                        help="datapath bit-width (default: %(default)s)")
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("output_log"),
                        help="output directory (default: %(default)s)")
    return parser.parse_args(argv)


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
