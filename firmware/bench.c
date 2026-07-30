#include "bench.h"
#include <avr/io.h>

void bench_init(void)
{
    TCC0.CTRLA = TC_CLKSEL_OFF_gc;
    TCC0.CTRLB = 0;
    TCC0.CNT   = 0;
}

void bench_start(void)
{
    TCC0.CNT   = 0;
    TCC0.CTRLA = BENCH_CLKSEL;
}

uint16_t bench_stop(void)
{
    uint16_t ticks = TCC0.CNT;
    TCC0.CTRLA = TC_CLKSEL_OFF_gc;
    return ticks;
}
