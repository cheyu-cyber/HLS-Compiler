// Parameterized unsigned subtractor; the default datapath width is 6 bits.
module subtractor #(
    parameter integer WIDTH = 6
) (
    input wire [WIDTH-1:0] a,
    input wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] result
);
    assign result = a - b;
endmodule