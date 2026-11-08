"""Generate synthesizable Verilog from datapath and FSM plans."""
from __future__ import annotations

import re

from hls.gen_tools.datapath import DatapathPlan, OPERATORS
from hls.gen_tools.fsm_ctrl import FSMPlan

_VERILOG_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*\Z")
_OPERATOR_MODULES = {"+": "adder", "-": "subtractor", "*": "multiplier"}
_INPUT_WIDTH = 3
_SWITCH_GROUPS = 4      # in0..in3 come from SW[11:0]; extra inputs are hardcoded
_HARDCODED_VALUE = 1
_VIEW_SLOTS = 16        # sel (SW[15:12]) picks one of these for the display


# check if a module name or signal name is valid in Verilog
def _validate_identifier(name: str, description: str) -> None:
    if not _VERILOG_IDENTIFIER.fullmatch(name):
        raise ValueError(f"{description} {name!r} is not a valid Verilog identifier")


# what sel 0, 1, 2... shows: each functional unit's result, then each register
# (shared with testbench_gen so both use the same slot numbers)
def view_slots(datapath: DatapathPlan) -> list[tuple[str, str]]:
    units = [unit for operator in OPERATORS for unit in datapath.units_by_operator.get(operator, ())]
    views = [(f"{unit.name}_result", unit.name) for unit in units]
    views += [(register, node) for node, register in datapath.registers.items()]
    return views[:_VIEW_SLOTS]


def generate_verilog(
    datapath: DatapathPlan,
    fsm: FSMPlan,
    module_name: str = "hls_design",
) -> str:
    """Return a Verilog module implementing the supplied datapath and FSM.

    The module has fixed ports so ``rtl/top.v`` never changes: 3-bit switch
    inputs ``in0``..``in3`` (inputs in alphabetical order), ``en`` to advance
    one cycle per button press, and ``sel`` choosing which functional unit or
    register drives ``view``. ``WIDTH`` is a top-level parameter defaulting to
    the datapath plan's internal width, which must be between 3 and 16.
    Each allocated functional unit instantiates the matching module from
    ``rtl/lib``.
    """
    _validate_identifier(module_name, "Module name")
    if not _INPUT_WIDTH <= datapath.width <= 16:
        raise ValueError("Datapath width must be between 3 and 16 bits")

    for name in (*datapath.inputs, *datapath.outputs):
        _validate_identifier(name, "DAG signal")
    for state_name in (fsm.idle_state, fsm.done_state, *fsm.cycle_states.values()):
        _validate_identifier(state_name, "FSM state")

    units = [
        unit
        for operator in OPERATORS
        for unit in datapath.units_by_operator.get(operator, ())
    ]
    unit_names = {unit.name for unit in units}
    if len(unit_names) != len(units):
        raise ValueError("Functional unit names must be unique")

    nodes_by_register = {register: node for node, register in datapath.registers.items()}
    if len(nodes_by_register) != len(datapath.registers):
        raise ValueError("Register names must be unique")

    cycle_count = fsm.latency
    expected_cycles = set(range(1, cycle_count + 1))
    if set(fsm.cycle_states) != expected_cycles:
        raise ValueError("FSM cycle states must cover every scheduled cycle")

    port_lines = [
        "input wire clk",
        "input wire reset",
        "input wire en",
        f"input wire [{_INPUT_WIDTH - 1}:0] in0",
        f"input wire [{_INPUT_WIDTH - 1}:0] in1",
        f"input wire [{_INPUT_WIDTH - 1}:0] in2",
        f"input wire [{_INPUT_WIDTH - 1}:0] in3",
        "input wire [3:0] sel",
        "output reg [15:0] view",
        "output reg [4:0] state",
        "output wire done",
    ]
    switch_inputs = sorted(datapath.inputs)
    lines = [
        "// switches: " + ", ".join(
            f"in{index} = {name}" for index, name in enumerate(switch_inputs[:_SWITCH_GROUPS])
        ),
        f"module {module_name} #(",
        f"    parameter integer WIDTH = {datapath.width}",
        ") (",
    ]
    lines.extend(
        f"    {line}" + ("," if index < len(port_lines) - 1 else "")
        for index, line in enumerate(port_lines)
    )
    lines.append(");")

    state_names = [fsm.idle_state]
    state_names.extend(fsm.cycle_states[cycle] for cycle in sorted(expected_cycles))
    state_names.append(fsm.done_state)
    if len(set(state_names)) != len(state_names):
        raise ValueError("FSM state names must be unique")
    state_width = 5  # state is a 5-bit output port (shown on the display)
    for index, state_name in enumerate(state_names):
        lines.append(
            f"localparam [{state_width - 1}:0] {state_name} = "
            f"{state_width}'d{index};"
        )

    for register in datapath.registers.values():
        _validate_identifier(register, "Register name")
        lines.append(f"reg [WIDTH-1:0] {register};")

    for index, name in enumerate(switch_inputs):
        source = f"in{index}" if index < _SWITCH_GROUPS else str(_HARDCODED_VALUE)
        lines.extend(
            (
                f"wire [WIDTH-1:0] extended_{name};",
                f"assign extended_{name} = {source};",
            )
        )

    for unit in units:
        lines.extend(
            (
                f"reg [WIDTH-1:0] {unit.name}_lhs;",
                f"reg [WIDTH-1:0] {unit.name}_rhs;",
                f"wire [WIDTH-1:0] {unit.name}_result;",
            )
        )
        operator = unit.operator
        if operator not in OPERATORS:
            raise ValueError(f"Unsupported functional unit operator {operator!r}")
        lines.append(
            f"{_OPERATOR_MODULES[operator]} #(.WIDTH(WIDTH)) {unit.name} ("
            f".a({unit.name}_lhs), .b({unit.name}_rhs), "
            f".result({unit.name}_result));"
        )

    # observability: sel shows a functional unit's result, then each register
    lines.extend(("always @* begin", "    case (sel)"))
    for index, (signal, label) in enumerate(view_slots(datapath)):
        lines.append(f"        4'd{index}: view = {signal};  // {label}")
    lines.extend(("        default: view = 16'd0;", "    endcase", "end"))
    lines.append("assign done = (state == " + fsm.done_state + ");")

    if units:
        lines.append("always @* begin")
        for unit in units:
            lines.append(f"    {unit.name}_lhs = {{WIDTH{{1'b0}}}};")
            lines.append(f"    {unit.name}_rhs = {{WIDTH{{1'b0}}}};")
        lines.append("    case (state)")
        for cycle in sorted(expected_cycles):
            selections = fsm.unit_selections_by_cycle.get(cycle, {})
            if not selections:
                continue
            lines.append(f"        {fsm.cycle_states[cycle]}: begin")
            for unit_name, node in selections.items():
                if unit_name not in unit_names:
                    raise ValueError(
                        f"FSM selects unknown functional unit {unit_name!r}"
                    )
                if node not in datapath.operation_inputs:
                    raise ValueError(f"FSM selects unknown operation node {node!r}")
                lhs, rhs = datapath.operation_inputs[node]
                for operand, side in ((lhs, "lhs"), (rhs, "rhs")):
                    if operand in datapath.registers:
                        signal = datapath.registers[operand]
                    elif operand in datapath.inputs:
                        signal = f"extended_{operand}"
                    else:
                        raise ValueError(
                            f"Operand {operand!r} for node {node!r} "
                            "is not a register or module input"
                        )
                    lines.append(f"            {unit_name}_{side} = {signal};")
            lines.append("        end")
        lines.extend(("        default: begin end", "    endcase", "end"))

    lines.extend(
        (
            "always @(posedge clk or posedge reset) begin",
            "    if (reset) begin",
            f"        state <= {fsm.idle_state};",
        )
    )
    for register in datapath.registers.values():
        lines.append(f"        {register} <= {{WIDTH{{1'b0}}}};")
    lines.extend(("    end else if (en) begin  // one step per button press", "        case (state)"))
    if cycle_count == 0:
        lines.extend(
            (
                f"            {fsm.idle_state}: state <= {fsm.done_state};",
            )
        )
    else:
        first_state = fsm.cycle_states[1]
        lines.extend(
            (
                f"            {fsm.idle_state}: state <= {first_state};",
            )
        )
        for cycle in sorted(expected_cycles):
            state_name = fsm.cycle_states[cycle]
            writes = fsm.register_writes_by_cycle.get(cycle, ())
            lines.append(f"            {state_name}: begin")
            for register in writes:
                if register not in nodes_by_register:
                    raise ValueError(
                        f"FSM writes unknown register {register!r}"
                    )
                node = nodes_by_register[register]
                unit = datapath.node_to_unit.get(node)
                if unit is None or unit.name not in unit_names:
                    raise ValueError(
                        f"Operation node {node!r} has no allocated functional unit"
                    )
                if fsm.unit_selections_by_cycle.get(cycle, {}).get(unit.name) != node:
                    raise ValueError(
                        f"FSM does not select the unit for node {node!r} "
                        f"in cycle {cycle}"
                    )
                lines.append(f"                {register} <= {unit.name}_result;")
            next_state = (
                fsm.cycle_states[cycle + 1]
                if cycle < cycle_count
                else fsm.done_state
            )
            lines.append(f"                state <= {next_state};")
            lines.append("            end")
    lines.extend(
        (
            f"            {fsm.done_state}: state <= {fsm.idle_state};",
            f"            default: state <= {fsm.idle_state};",
            "        endcase",
            "    end",
            "end",
            "endmodule",
            "",
        )
    )
    return "\n".join(lines)
