// 7 seg with flickering
module seven_seg #(
    parameter integer DIGIT_TIME = 400_000         // clocks per digit: 4 ms at 100 MHz
) (
    input  wire        clk,
    input  wire [31:0] value,     // 8 hex digits, digit 7 on the left
    input  wire [7:0]  blank,     // 1 = digit off
    output reg  [6:0]  seg,       // {g, f, e, d, c, b, a}
    output wire [7:0]  enable
);
    reg [21:0] count = 0;
    reg [2:0]  digit = 0;
    always @(posedge clk)
        if (count == DIGIT_TIME - 1) begin        // time's up: move to the next digit
            count <= 0;
            digit <= digit + 1;
        end
        else count <= count + 1;

    wire [3:0] hex = value[digit * 4 +: 4];
    assign enable = blank[digit] ? 8'hFF : ~(8'b1 << digit);

    always @* case (hex)
        4'h0: seg = 7'b1000000;
        4'h1: seg = 7'b1111001;
        4'h2: seg = 7'b0100100;
        4'h3: seg = 7'b0110000;
        4'h4: seg = 7'b0011001;
        4'h5: seg = 7'b0010010;
        4'h6: seg = 7'b0000010;
        4'h7: seg = 7'b1111000;
        4'h8: seg = 7'b0000000;
        4'h9: seg = 7'b0010000;
        4'hA: seg = 7'b0001000;
        4'hB: seg = 7'b0000011;
        4'hC: seg = 7'b1000110;
        4'hD: seg = 7'b0100001;
        4'hE: seg = 7'b0000110;
        default: seg = 7'b0001110;               // F
    endcase
endmodule
