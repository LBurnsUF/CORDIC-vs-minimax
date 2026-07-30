#include <avr/io.h>
#include <avr/interrupt.h>
#include "fixed_point.h"
#include "generated.h"
#include "cordic.h"
#include "poly.h"
#include "bench.h"
#include "uart.h"

static void clock_init_32mhz(void)
{
    OSC.CTRL |= OSC_RC32MEN_bm;
    while (!(OSC.STATUS & OSC_RC32MRDY_bm))
        ;
    CCP = CCP_IOREG_gc;
    CLK.CTRL = CLK_SCLKSEL_RC32M_gc;
}

static void emit_csv(const char *algo, uint8_t idx,
                     fixed_t s, fixed_t c,
                     fixed_t s_ref, fixed_t c_ref,
                     uint16_t ticks)
{
    uart_puts(algo);        uart_putc(',');
    uart_put_u16(TOTAL_BITS); uart_putc(',');
    uart_put_u16(FRAC_BITS);  uart_putc(',');
    uart_put_u16(idx);        uart_putc(',');
    uart_put_fixed(s);        uart_putc(',');
    uart_put_fixed(c);        uart_putc(',');
    uart_put_fixed(s_ref);    uart_putc(',');
    uart_put_fixed(c_ref);    uart_putc(',');

    fixed_t se = s - s_ref;
    fixed_t ce = c - c_ref;
    if (se < 0) se = -se;
    if (ce < 0) ce = -ce;
    uart_put_fixed(se);        uart_putc(',');
    uart_put_fixed(ce);        uart_putc(',');
    uart_put_u16(ticks);
    uart_puts("\r\n");
}

int main(void)
{
    clock_init_32mhz();
    uart_init();
    bench_init();

    uart_puts("algo,total_bits,frac_bits,angle_idx,sin,cos,"
              "sin_ref,cos_ref,sin_err,cos_err,ticks\r\n");

    for (uint8_t a = 0; a < NUM_TEST_ANGLES; a++) {
        fixed_t angle  = PGM_READ_FIXED(&test_angles[a]);
        fixed_t s_ref  = PGM_READ_FIXED(&ref_sin[a]);
        fixed_t c_ref  = PGM_READ_FIXED(&ref_cos[a]);
        fixed_t s, c;
        uint16_t ticks;

        /* --- CORDIC --- */
        bench_start();
        for (uint16_t k = 0; k < K_LOOPS; k++)
            cordic_sincos(angle, &s, &c);
        ticks = bench_stop();
        emit_csv("CORDIC", a, s, c, s_ref, c_ref, ticks);

        /* --- Taylor --- */
        bench_start();
        for (uint16_t k = 0; k < K_LOOPS; k++)
            taylor_sincos(angle, &s, &c);
        ticks = bench_stop();
        emit_csv("TAYLOR", a, s, c, s_ref, c_ref, ticks);

        /* --- Minimax --- */
        bench_start();
        for (uint16_t k = 0; k < K_LOOPS; k++)
            minimax_sincos(angle, &s, &c);
        ticks = bench_stop();
        emit_csv("MINIMAX", a, s, c, s_ref, c_ref, ticks);
    }

    uart_puts("DONE\r\n");
    for (;;)
        ;
}
