"""Generate synthesizable Verilog from datapath and FSM plans."""
from __future__ import annotations

import re

from hls.gen_tools.datapath import DatapathPlan, OPERATORS
from hls.gen_tools.fsm_ctrl import FSMPlan

_VERILOG_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*\Z")
_RESERVED_PORTS = {"clk", "reset", "start", "done"}
_OPERATOR_MODULES = {"+": "adder", "-": "subtractor", "*": "multiplier"}
_INPUT_WIDTH = 3


# check if a module name or signal name is valid in Verilog
def _validate_identifier(name: str, description: str) -> None:
    if not _VERILOG_IDENTIFIER.fullmatch(name):
        raise ValueError(f"{description} {name!r} is not a valid Verilog identifier")


def generate_verilog(
    datapath: DatapathPlan,
    fsm: FSMPlan,
    module_name: str = "hls_design",
) -> str:
    """Return a Verilog module implementing the supplied datapath and FSM.

    The module exposes 3-bit inputs as ``in_<name>`` and results as
    ``out_<name>``. ``WIDTH`` is a top-level parameter defaulting to the
    datapath plan's internal width, which must be between 3 and 6.
    Each allocated functional unit instantiates the matching module from
    ``rtl/lib``.
    """
    _validate_identifier(module_name, "Module name")
    if not _INPUT_WIDTH <= datapath.width <= 6:
        raise ValueError("Datapath width must be between 3 and 6 bits")

    for name in (*datapath.inputs, *datapath.outputs):
        _validate_identifier(name, "DAG signal")
    for state_name in (fsm.idle_state, fsm.done_state, *fsm.cycle_states.values()):
        _validate_identifier(state_name, "FSM state")

    all_ports = {
        f"in_{name}" for name in datapath.inputs
    } | {f"out_{name}" for name in datapath.outputs} | _RESERVED_PORTS
    if len(all_ports) != len(datapath.inputs) + len(datapath.outputs) + len(_RESERVED_PORTS):
        raise ValueError("Generated Verilog port names are not unique")

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
        "input wire start",
        "output wire done",
    ] + [
        f"input wire [{_INPUT_WIDTH - 1}:0] in_{name}"
        for name in datapath.inputs
    ] + [
        f"output wire [WIDTH-1:0] out_{name}"
        for name in datapath.outputs
    ]
    lines = [
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
    state_width = max(1, (len(state_names) - 1).bit_length())
    lines.append(f"reg [{state_width - 1}:0] state;")
    for index, state_name in enumerate(state_names):
        lines.append(
            f"localparam [{state_width - 1}:0] {state_name} = "
            f"{state_width}'d{index};"
        )

    for register in datapath.registers.values():
        _validate_identifier(register, "Register name")
        lines.append(f"reg [WIDTH-1:0] {register};")

    for name in datapath.inputs:
        lines.extend(
            (
                f"wire [WIDTH-1:0] extended_{name};",
                f"assign extended_{name} = in_{name};",
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

    for output in datapath.outputs:
        if output not in datapath.registers:
            raise ValueError(f"Output node {output!r} has no result register")
        lines.append(f"assign out_{output} = {datapath.registers[output]};")
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
    lines.extend(("    end else begin", "        case (state)"))
    if cycle_count == 0:
        lines.extend(
            (
                f"            {fsm.idle_state}: state <= start ? "
                f"{fsm.done_state} : {fsm.idle_state};",
            )
        )
    else:
        first_state = fsm.cycle_states[1]
        lines.extend(
            (
                f"            {fsm.idle_state}: state <= start ? "
                f"{first_state} : {fsm.idle_state};",
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
