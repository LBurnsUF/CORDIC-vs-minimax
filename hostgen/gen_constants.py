#!/usr/bin/env python3
"""
Host-side constant generator for CORDIC-vs-minimax project.

Generates a C header (generated.h) with:
  - CORDIC atan lookup table and finite-iteration 1/K
  - Taylor polynomial coefficients for sin/cos
  - Minimax polynomial coefficients via Remez exchange
  - Test angle vectors with reference sin/cos values

Usage: python gen_constants.py TOTAL_BITS FRAC_BITS > generated.h
"""

import sys
import math


# ---------------------------------------------------------------------------
# Linear algebra (no numpy dependency)
# ---------------------------------------------------------------------------

def gauss_solve(A, b):
    """Solve Ax=b via Gaussian elimination with partial pivoting."""
    n = len(b)
    M = [row[:] + [bi] for row, bi in zip(A, b)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[pivot] = M[pivot], M[col]
        if abs(M[col][col]) < 1e-30:
            raise ValueError("Singular matrix at column %d" % col)
        for row in range(col + 1, n):
            f = M[row][col] / M[col][col]
            for j in range(col, n + 1):
                M[row][j] -= f * M[col][j]

    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


# ---------------------------------------------------------------------------
# Remez exchange
# ---------------------------------------------------------------------------

def remez(target, degree, a, b, max_iter=80, n_samples=20000):
    """
    Minimax polynomial approximation of *target* on [a, b].

    Returns (coeffs, max_error) where
        p(x) = coeffs[0] + coeffs[1]*x + ... + coeffs[degree]*x^degree
    minimises  max |target(x) - p(x)|  over [a, b].
    """
    n_coeffs = degree + 1
    n_refs   = degree + 2

    # Chebyshev nodes as initial reference
    refs = sorted(
        (a + b) / 2 - (b - a) / 2 * math.cos(math.pi * k / (n_refs - 1))
        for k in range(n_refs)
    )

    def poly_eval(coeffs, x):
        r = 0.0
        for c in reversed(coeffs):
            r = r * x + c
        return r

    prev_E = None
    coeffs = None
    for _it in range(max_iter):
        # Leveled interpolation system
        A   = [[u ** j for j in range(n_coeffs)] + [(-1.0) ** i]
               for i, u in enumerate(refs)]
        rhs = [target(u) for u in refs]
        sol = gauss_solve(A, rhs)
        coeffs = sol[:n_coeffs]
        E = abs(sol[n_coeffs])

        if prev_E is not None and abs(E - prev_E) < 1e-15 * max(E, 1e-30):
            break
        prev_E = E

        # Dense error sampling
        errs = []
        for i in range(n_samples + 1):
            x = a + (b - a) * i / n_samples
            errs.append((x, target(x) - poly_eval(coeffs, x)))

        # Local extrema (including endpoints)
        extrema = [errs[0]]
        for i in range(1, len(errs) - 1):
            _, ep = errs[i - 1]
            _, ec = errs[i]
            _, en = errs[i + 1]
            if (ec >= ep and ec >= en) or (ec <= ep and ec <= en):
                extrema.append(errs[i])
        extrema.append(errs[-1])

        # Merge adjacent same-sign extrema (keep larger |e|)
        merged = [extrema[0]]
        for ext in extrema[1:]:
            if (ext[1] > 0) == (merged[-1][1] > 0):
                if abs(ext[1]) > abs(merged[-1][1]):
                    merged[-1] = ext
            else:
                merged.append(ext)

        # Trim to n_refs points while preserving alternation
        while len(merged) > n_refs:
            if (len(merged) - n_refs) % 2 == 1:
                if abs(merged[0][1]) < abs(merged[-1][1]):
                    merged.pop(0)
                else:
                    merged.pop()
            else:
                worst_idx = min(
                    range(len(merged) - 1),
                    key=lambda i: min(abs(merged[i][1]), abs(merged[i + 1][1]))
                )
                del merged[worst_idx:worst_idx + 2]

        if len(merged) < n_refs:
            break

        refs = [m[0] for m in merged]

    return coeffs, E


# ---------------------------------------------------------------------------
# Coefficient helpers
# ---------------------------------------------------------------------------

def taylor_sin_coeffs(max_terms):
    """Coefficients of P(u) where sin(x) = x * P(x^2)."""
    coeffs = []
    for k in range(max_terms):
        n = 2 * k + 1
        fact = math.factorial(n)
        coeffs.append((-1) ** k / fact)
    return coeffs


def taylor_cos_coeffs(max_terms):
    """Coefficients of Q(u) where cos(x) = Q(x^2)."""
    coeffs = []
    for k in range(max_terms):
        n = 2 * k
        fact = math.factorial(n) if n else 1
        coeffs.append((-1) ** k / fact)
    return coeffs


def count_nonzero(float_coeffs, scale):
    """Number of leading coefficients that round to non-zero in Q format."""
    n = 0
    for c in float_coeffs:
        if round(c * scale) != 0:
            n += 1
        else:
            break
    # Must keep at least the constant term
    return max(n, 1)


def minimax_sin_coeffs(degree, interval_hi=math.pi / 4):
    """
    Minimax coefficients for P(u) where sin(x) ~ x * P(x^2) on [0, interval_hi].
    u_max = interval_hi^2.
    """
    u_max = interval_hi ** 2

    def target(u):
        if u < 1e-30:
            return 1.0
        x = math.sqrt(u)
        return math.sin(x) / x

    coeffs, _err = remez(target, degree, 0.0, u_max)
    return coeffs


def minimax_cos_coeffs(degree, interval_hi=math.pi / 4):
    """
    Minimax coefficients for Q(u) where cos(x) ~ Q(x^2) on [0, interval_hi].
    """
    u_max = interval_hi ** 2

    def target(u):
        return math.cos(math.sqrt(u))

    coeffs, _err = remez(target, degree, 0.0, u_max)
    return coeffs


def pick_poly_degree(target_func, half_lsb, a, b, max_deg=12):
    """
    Find minimum polynomial degree for Remez error < half_lsb on [a, b].
    """
    for deg in range(1, max_deg + 1):
        _coeffs, err = remez(target_func, deg, a, b)
        if err < half_lsb:
            return deg
    return max_deg


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def q(val, scale):
    """Quantize a float to fixed-point integer."""
    return int(round(val * scale))


def c_type(total_bits):
    return {8: "int8_t", 16: "int16_t", 32: "int32_t"}[total_bits]


def emit_header(total_bits, frac_bits):
    scale = 2 ** frac_bits
    half_lsb = 0.5 / scale
    pi_half = math.pi / 2
    pi_quarter = math.pi / 4
    u_max = pi_quarter ** 2
    num_iter = frac_bits

    lines = []
    def out(s=""):
        lines.append(s)

    out("/* Auto-generated for Q%d.%d  (TOTAL_BITS=%d, FRAC_BITS=%d) */" %
        (total_bits - 1 - frac_bits, frac_bits, total_bits, frac_bits))
    out("#ifndef GENERATED_H")
    out("#define GENERATED_H")
    out()
    out('#include <avr/pgmspace.h>')
    out('#include "fixed_point.h"')
    out()

    # ---- fixed-point constants ----
    out("#define FIXED_PI_HALF    ((fixed_t)%d)" % q(pi_half, scale))
    out("#define FIXED_PI_QUARTER ((fixed_t)%d)" % q(pi_quarter, scale))
    out()

    # ---- CORDIC atan table ----
    out("#define NUM_CORDIC_ITER %d" % num_iter)
    out()
    out("static const fixed_t cordic_atan[NUM_CORDIC_ITER] PROGMEM = {")
    for i in range(num_iter):
        a_val = math.atan(2.0 ** (-i))
        out("    %d%s  /* atan(2^-%d) = %.12f */" %
            (q(a_val, scale), "," if i < num_iter - 1 else "", i, a_val))
    out("};")
    out()

    # ---- CORDIC 1/K (finite iteration count) ----
    K = 1.0
    for i in range(num_iter):
        K *= math.sqrt(1.0 + 2.0 ** (-2 * i))
    inv_K = 1.0 / K
    out("/* 1/K for %d iterations  (K=%.15f, 1/K=%.15f) */" % (num_iter, K, inv_K))
    out("/* Finite-iteration value, NOT the asymptotic 0.6072529... */")
    out("#define CORDIC_INV_K ((fixed_t)%d)" % q(inv_K, scale))
    out()

    # ---- Taylor coefficients ----
    max_terms = min(frac_bits // 3 + 2, 10)
    t_sin = taylor_sin_coeffs(max_terms)
    t_cos = taylor_cos_coeffs(max_terms)
    n_sin = count_nonzero(t_sin, scale)
    n_cos = count_nonzero(t_cos, scale)

    out("/* Taylor sin: sin(x) = x * (c[0] + x^2*(c[1] + ...)) */")
    out("#define NUM_TAYLOR_SIN_TERMS %d" % n_sin)
    out("static const fixed_t taylor_sin[NUM_TAYLOR_SIN_TERMS] PROGMEM = {")
    for k in range(n_sin):
        out("    %d%s  /* %+.15f */" %
            (q(t_sin[k], scale), "," if k < n_sin - 1 else "", t_sin[k]))
    out("};")
    out()

    out("/* Taylor cos: cos(x) = c[0] + x^2*(c[1] + ...) */")
    out("#define NUM_TAYLOR_COS_TERMS %d" % n_cos)
    out("static const fixed_t taylor_cos[NUM_TAYLOR_COS_TERMS] PROGMEM = {")
    for k in range(n_cos):
        out("    %d%s  /* %+.15f */" %
            (q(t_cos[k], scale), "," if k < n_cos - 1 else "", t_cos[k]))
    out("};")
    out()

    # ---- Minimax coefficients (Remez exchange) ----
    def sin_target(u):
        if u < 1e-30:
            return 1.0
        return math.sin(math.sqrt(u)) / math.sqrt(u)

    def cos_target(u):
        return math.cos(math.sqrt(u))

    mm_sin_deg = pick_poly_degree(sin_target, half_lsb, 0.0, u_max)
    mm_cos_deg = pick_poly_degree(cos_target, half_lsb, 0.0, u_max)
    mm_sin, mm_sin_err = remez(sin_target, mm_sin_deg, 0.0, u_max)
    mm_cos, mm_cos_err = remez(cos_target, mm_cos_deg, 0.0, u_max)

    n_mm_sin = len(mm_sin)
    n_mm_cos = len(mm_cos)

    out("/* Minimax sin (Remez, degree %d in u=x^2, max err %.2e) */" %
        (mm_sin_deg, mm_sin_err))
    out("#define NUM_MINIMAX_SIN_TERMS %d" % n_mm_sin)
    out("static const fixed_t minimax_sin[NUM_MINIMAX_SIN_TERMS] PROGMEM = {")
    for k in range(n_mm_sin):
        out("    %d%s  /* %+.15f */" %
            (q(mm_sin[k], scale), "," if k < n_mm_sin - 1 else "", mm_sin[k]))
    out("};")
    out()

    out("/* Minimax cos (Remez, degree %d in u=x^2, max err %.2e) */" %
        (mm_cos_deg, mm_cos_err))
    out("#define NUM_MINIMAX_COS_TERMS %d" % n_mm_cos)
    out("static const fixed_t minimax_cos[NUM_MINIMAX_COS_TERMS] PROGMEM = {")
    for k in range(n_mm_cos):
        out("    %d%s  /* %+.15f */" %
            (q(mm_cos[k], scale), "," if k < n_mm_cos - 1 else "", mm_cos[k]))
    out("};")
    out()

    # ---- Test angles and reference values ----
    test_degs = [0, 15, 30, 45, 60, 75, 90]
    out("#define NUM_TEST_ANGLES %d" % len(test_degs))
    out()

    out("static const fixed_t test_angles[NUM_TEST_ANGLES] PROGMEM = {")
    for i, d in enumerate(test_degs):
        rad = math.radians(d)
        out("    %d%s  /* %d deg = %.12f rad */" %
            (q(rad, scale), "," if i < len(test_degs) - 1 else "", d, rad))
    out("};")
    out()

    out("static const fixed_t ref_sin[NUM_TEST_ANGLES] PROGMEM = {")
    for i, d in enumerate(test_degs):
        s = math.sin(math.radians(d))
        out("    %d%s  /* sin(%d) = %.15f */" %
            (q(s, scale), "," if i < len(test_degs) - 1 else "", d, s))
    out("};")
    out()

    out("static const fixed_t ref_cos[NUM_TEST_ANGLES] PROGMEM = {")
    for i, d in enumerate(test_degs):
        c = math.cos(math.radians(d))
        out("    %d%s  /* cos(%d) = %.15f */" %
            (q(c, scale), "," if i < len(test_degs) - 1 else "", d, c))
    out("};")
    out()

    out("#endif /* GENERATED_H */")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 3:
        print("Usage: %s TOTAL_BITS FRAC_BITS" % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    total_bits = int(sys.argv[1])
    frac_bits  = int(sys.argv[2])

    if total_bits not in (8, 16, 32):
        print("TOTAL_BITS must be 8, 16, or 32", file=sys.stderr)
        sys.exit(1)
    if not (1 <= frac_bits <= total_bits - 2):
        print("FRAC_BITS must be in [1, %d]" % (total_bits - 2), file=sys.stderr)
        sys.exit(1)

    print(emit_header(total_bits, frac_bits))


if __name__ == "__main__":
    main()
