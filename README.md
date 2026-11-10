# Simple HLS compiler
## Repository Organization
## System Description
## User Instructions
## Demo Plan
1. **High-Level Input Parsing**
2. **Single Assignment Form**

    a. Run: python -m srcs.hlsc ./examples/demo_example.txt --export-ssa

    b. Show output_log/demo_example_ssa.txt
3. **Directed Acyclic Graph (DAG) & Scheduling**

    a. Run: python -m srcs.hlsc ./examples/demo_example.txt --export-dag --export-schedule --adders 2 --subtractors 2 --multipliers 2

    b. Show output_log/demo_example_dag.svg

    c. Show output_log/demo_example_schedule.txt 
4. **Datapath and Sequencer Logic Generation**

    a. Run: python -m srcs.hlsc ./examples/demo_example.txt --export-datapath --make-schedule constrained_alap --export-verilog --export-testbench --adders 2 --subtractors 2 --multipliers 2

    b. Above line creates datapath and hardware designs based on input arg to --make-schedule, default is constrained_asap

    c. Show output_log/demo_example_datapath.txt, output_log/demo_example_verilog.v, output_log/demo_example_testbench.v
5. **Verilog Functional Unit Blocks**

    a. Show project setup in Vivado, import generated verilog and testbench
6. **Composite Verilog Synthesis & RTL Integration**

    a. Show top/core/ to show required number of operator units are instantiated

    b. Walk through generated verilog module to show instantiated modules, MUX-like routing, and pipeline registers

    c. Quickly show Elaborated Design Schematic in Vivado, emphasize MUX and register design and cycle step through flow

    d. *Show testbench results and compare to manually computed example*
7. **FPGA Deployment and Verification**

    a. Deploy onto FPGA and compare results to testbench
8. **README & Demo Plan**

    a. The demo plan is outlined as above, and can be run with any set of input equations meeting the assumptions in the assignment outline (not more than 20 equations, no negative solutions, operators limited to +, -, *)
