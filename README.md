# Simple HLS compiler
## Repository Organization

The compiler entry point and end-to-end pipeline are in `srcs/`: `hlsc.py` parses command-line options, while `pipeline.py` runs the synthesis flow. The `hls/` package contains the input parser, SSA and DAG construction, scheduling algorithms, and Verilog/datapath/testbench generators. Example input programs are in `examples/`, and generated exports are written to `output_log/` by default. The `rtl/` directory contains the supporting Verilog modules and constraints used for FPGA integration.

## System Description

This project is a command-line high-level synthesis compiler that converts arithmetic equations into a scheduled hardware datapath. It parses the input, transforms equations into SSA form and a DAG, schedules operations under configurable functional-unit limits, then generates datapath/control descriptions and optional Verilog and testbench files.

## User Instructions

- Your input equations can live in a directory of your choosing, but for ease of use it is recommended to copy them to `examples/` as shown in the below steps
- To run all of the steps in the demo plan with one command for a single example: `python -m srcs.hlsc ./examples/demo_example.txt --export-all --adders 2 --subtractors 2 --multipliers 2`
- You can optionally specify another schedule (other than the default constrained_asap) with `--make-schedule {schedule}`
## Demo Plan

1. **High-Level Input Parsing**

    a. Demonstrated in the same steps as #2
2. **Single Assignment Form**

    a. Run: `python -m srcs.hlsc ./examples/demo_example.txt --export-ssa`

    b. Show `output_log/demo_example_ssa.txt`
3. **Directed Acyclic Graph (DAG) & Scheduling**

    a. Run: `python -m srcs.hlsc ./examples/demo_example.txt --export-dag --export-schedule --adders 2 --subtractors 2 --multipliers 2`

    b. Show `output_log/demo_example_dag.svg`

    c. Show `output_log/demo_example_schedule.txt`
4. **Datapath and Sequencer Logic Generation**

    a. Run: `python -m srcs.hlsc ./examples/demo_example.txt --export-datapath --make-schedule constrained_alap --export-verilog --export-testbench --adders 2 --subtractors 2 --multipliers 2`

    b. Above line creates datapath and hardware designs based on input arg to `--make-schedule, default is constrained_asap`

    c. Show `output_log/demo_example_datapath.txt`, `output_log/demo_example_verilog.v`, `output_log/demo_example_testbench.v`
5. **Verilog Functional Unit Blocks**

    a. Show project setup in Vivado, import generated verilog and testbench
6. **Composite Verilog Synthesis & RTL Integration**

    a. Show `top/core/` to show required number of operator units are instantiated

    b. Walk through generated verilog module to show instantiated modules, MUX-like routing, and pipeline registers

    c. Quickly show Elaborated Design Schematic in Vivado, emphasize MUX and register design and cycle step through flow

    d. Show testbench results and compare to manually computed example
7. **FPGA Deployment and Verification**

    a. Deploy onto FPGA and compare results to testbench
8. **README & Demo Plan**

    a. The demo plan is outlined as above, and can be run with any set of input equations meeting the assumptions in the assignment outline (not more than 20 equations, no negative solutions, operators limited to +, -, *)
