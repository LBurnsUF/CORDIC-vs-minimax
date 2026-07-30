#ifndef FIXED_POINT_H
#define FIXED_POINT_H

#include <stdint.h>
#include <avr/pgmspace.h>

#ifndef TOTAL_BITS
#error "Define TOTAL_BITS (8, 16, or 32)"
#endif
#ifndef FRAC_BITS
#error "Define FRAC_BITS (<= TOTAL_BITS - 2)"
#endif

_Static_assert(TOTAL_BITS == 8 || TOTAL_BITS == 16 || TOTAL_BITS == 32,
               "TOTAL_BITS must be 8, 16, or 32");
_Static_assert(FRAC_BITS >= 1 && FRAC_BITS <= TOTAL_BITS - 2,
               "FRAC_BITS must be in [1, TOTAL_BITS-2]");

#if TOTAL_BITS == 8
typedef int8_t  fixed_t;
typedef int16_t wide_t;
#define PGM_READ_FIXED(addr) ((fixed_t)pgm_read_byte(addr))
#define FIXED_FMT_SPEC "d"
#elif TOTAL_BITS == 16
typedef int16_t fixed_t;
typedef int32_t wide_t;
#define PGM_READ_FIXED(addr) ((fixed_t)pgm_read_word(addr))
#define FIXED_FMT_SPEC "d"
#elif TOTAL_BITS == 32
typedef int32_t fixed_t;
typedef int64_t wide_t;
#define PGM_READ_FIXED(addr) ((fixed_t)pgm_read_dword(addr))
#define FIXED_FMT_SPEC "ld"
#endif

#define FIXED_ONE  ((fixed_t)((fixed_t)1 << FRAC_BITS))
#define FIXED_HALF ((fixed_t)((fixed_t)1 << (FRAC_BITS - 1)))
#define INT_BITS   (TOTAL_BITS - 1 - FRAC_BITS)

static inline fixed_t fixed_mul(fixed_t a, fixed_t b)
{
    return (fixed_t)(((wide_t)a * (wide_t)b) >> FRAC_BITS);
}

#endif
