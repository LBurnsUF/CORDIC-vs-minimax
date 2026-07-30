#include "cordic.h"
#include "generated.h"

void cordic_sincos(fixed_t angle, fixed_t *sin_out, fixed_t *cos_out)
{
    fixed_t x = CORDIC_INV_K;
    fixed_t y = 0;
    fixed_t z = angle;

    for (uint8_t i = 0; i < NUM_CORDIC_ITER; i++) {
        fixed_t dx = y >> i;
        fixed_t dy = x >> i;
        fixed_t ai = PGM_READ_FIXED(&cordic_atan[i]);

        if (z >= 0) {
            x -= dx;
            y += dy;
            z -= ai;
        } else {
            x += dx;
            y -= dy;
            z += ai;
        }
    }

    *cos_out = x;
    *sin_out = y;
}
