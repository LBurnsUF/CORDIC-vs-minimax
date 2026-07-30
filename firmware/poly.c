#include "poly.h"
#include "generated.h"

static fixed_t horner_odd(const fixed_t *coeffs, uint8_t n, fixed_t x)
{
    fixed_t u = fixed_mul(x, x);
    fixed_t r = PGM_READ_FIXED(&coeffs[n - 1]);
    for (int8_t i = n - 2; i >= 0; i--)
        r = PGM_READ_FIXED(&coeffs[i]) + fixed_mul(u, r);
    return fixed_mul(x, r);
}

static fixed_t horner_even(const fixed_t *coeffs, uint8_t n, fixed_t x)
{
    fixed_t u = fixed_mul(x, x);
    fixed_t r = PGM_READ_FIXED(&coeffs[n - 1]);
    for (int8_t i = n - 2; i >= 0; i--)
        r = PGM_READ_FIXED(&coeffs[i]) + fixed_mul(u, r);
    return r;
}

void taylor_sincos(fixed_t angle, fixed_t *sin_out, fixed_t *cos_out)
{
    fixed_t x = angle;
    uint8_t swapped = 0;

    if (angle > FIXED_PI_QUARTER) {
        x = FIXED_PI_HALF - angle;
        swapped = 1;
    }

    fixed_t s = horner_odd(taylor_sin, NUM_TAYLOR_SIN_TERMS, x);
    fixed_t c = horner_even(taylor_cos, NUM_TAYLOR_COS_TERMS, x);

    if (swapped) {
        *sin_out = c;
        *cos_out = s;
    } else {
        *sin_out = s;
        *cos_out = c;
    }
}

void minimax_sincos(fixed_t angle, fixed_t *sin_out, fixed_t *cos_out)
{
    fixed_t x = angle;
    uint8_t swapped = 0;

    if (angle > FIXED_PI_QUARTER) {
        x = FIXED_PI_HALF - angle;
        swapped = 1;
    }

    fixed_t s = horner_odd(minimax_sin, NUM_MINIMAX_SIN_TERMS, x);
    fixed_t c = horner_even(minimax_cos, NUM_MINIMAX_COS_TERMS, x);

    if (swapped) {
        *sin_out = c;
        *cos_out = s;
    } else {
        *sin_out = s;
        *cos_out = c;
    }
}
