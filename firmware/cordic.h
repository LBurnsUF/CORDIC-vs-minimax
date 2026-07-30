#ifndef CORDIC_H
#define CORDIC_H

#include "fixed_point.h"

void cordic_sincos(fixed_t angle, fixed_t *sin_out, fixed_t *cos_out);

#endif
