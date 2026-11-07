// Top level for the Nexys 4 DDR: switches -> hls_design -> 7-segment display.
//   SW[11:0]   four 3-bit inputs (in0 = SW[2:0] ... in3 = SW[11:9])
//   SW[15:12]  view select: which functional unit or value is shown
//   BTNC       step: advance the design one cycle per press
//   CPU_RESETN reset (active low)
//   display    [view select] [blank] [state, 2 digits] [value, 4 hex digits]
//   LED[4:0]   state, LED[15] done
module top (
    input  wire        CLK100MHZ,
    input  wire        CPU_RESETN,
    input  wire        BTNC,
    input  wire [15:0] SW,
    output wire [15:0] LED,
    output wire        CA, CB, CC, CD, CE, CF, CG, DP,
    output wire [7:0]  AN
);
    wire step;
    wire [15:0] view;
    wire [4:0] state;
    wire done;

    debounce step_btn (.clk(CLK100MHZ), .btn(BTNC), .pulse(step));

    hls_design core (
        .clk(CLK100MHZ), .reset(~CPU_RESETN), .en(step),
        .in0(SW[2:0]), .in1(SW[5:3]), .in2(SW[8:6]), .in3(SW[11:9]),
        .sel(SW[15:12]), .view(view), .state(state), .done(done)
    );

    seven_seg display (
        .clk(CLK100MHZ),
        .value({SW[15:12], 4'h0, 3'b000, state, view}),
        .blank(8'b0100_0000),
        .seg({CG, CF, CE, CD, CC, CB, CA}),
        .enable(AN)
    );

    assign DP = 1'b1;                              // decimal point off
    assign LED = {done, 10'b0, state};
endmodule
