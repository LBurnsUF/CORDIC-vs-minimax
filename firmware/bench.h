#ifndef BENCH_H
#define BENCH_H

#include <stdint.h>
#include "fixed_point.h"

#if TOTAL_BITS == 8
#define PRESCALER    1
#define BENCH_CLKSEL TC_CLKSEL_DIV1_gc
#elif TOTAL_BITS == 16
#define PRESCALER    8
#define BENCH_CLKSEL TC_CLKSEL_DIV8_gc
#elif TOTAL_BITS == 32
#define PRESCALER    64
#define BENCH_CLKSEL TC_CLKSEL_DIV64_gc
#endif

#define K_LOOPS 100

void     bench_init(void);
void     bench_start(void);
uint16_t bench_stop(void);

#endif
