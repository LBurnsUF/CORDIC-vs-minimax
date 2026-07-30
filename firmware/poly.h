#ifndef POLY_H
#define POLY_H

#include "fixed_point.h"

void taylor_sincos(fixed_t angle, fixed_t *sin_out, fixed_t *cos_out);
void minimax_sincos(fixed_t angle, fixed_t *sin_out, fixed_t *cos_out);

#endif
