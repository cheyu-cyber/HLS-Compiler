// Button input: debounce
module debounce #(
    parameter integer COUNT = 1_000_000          // 10 ms at 100 MHz
) (
    input  wire clk,
    input  wire btn,
    output wire pulse
);
    reg sync0 = 0, sync1 = 0;                     // bring the button into the clock domain
    reg stable = 0, last = 0;
    reg [19:0] count = 0;

    always @(posedge clk) begin
        sync0 <= btn;
        sync1 <= sync0;
        if (sync1 == stable) count <= 0;          // no change: restart the wait
        else if (count == COUNT - 1) begin        // changed and held long enough: accept
            stable <= sync1;
            count <= 0;
        end
        else count <= count + 1;
        last <= stable;
    end

    assign pulse = stable & ~last;                // rising edge of the clean button
endmodule
