# CORDIC vs. Minimax: Fixed-Point sin/cos on an 8-bit AVR

How do you compute sin/cos on a microcontroller with no FPU? This project implements and
measures two answers on an ATxmega128A1U (8-bit AVR: add/sub/shift and a hardware 8×8→16
`MUL`, nothing else):

- **CORDIC** — rotate a vector by successively smaller angles chosen so each rotation is a
  bit shift; ~1 bit of precision per iteration, needs only a tiny atan(2⁻ⁱ) table.
- **Polynomial (Taylor and minimax)** — evaluate a degree-N polynomial with Horner's rule
  on the hardware multiplier; no angle table, coefficients inline.

The tradeoff is measured, not argued: real firmware sweeps both algorithms across three
fixed-point widths (Q8.6, Q16.14, Q32.30) and reports per-call cycle counts and error
against a double-precision reference.

## Results

Measured on the ATxmega128A1U at 32 MHz, averaged across 7 test angles
(timer-captured over 100-call loops; raw counter data in `data/*.csv`):

| Format | CORDIC (cycles) | Taylor | Minimax | CORDIC max err (LSB) | Taylor | Minimax |
|---|---|---|---|---|---|---|
| Q8.6   | 410   | 282   | 202   | 4 | 1 | 1 |
| Q16.14 | 1,488 | 1,537 | 1,215 | 4 | 1 | 1 |
| Q32.30 | 9,419 | 5,345 | 4,218 | 5 | 1 | 1 |

The story in two lines: CORDIC's shift-add iterations are cheap per step (~101 cycles at
8-bit) but iteration count grows one-per-bit, and each iteration's shifts get more
expensive as the word spans more limbs. The polynomial only adds ~2 terms per doubling of
precision, so the hardware multiplier wins increasingly hard at wider formats — and
equal-degree minimax beats Taylor on both cycles and worst-case error.

## Layout

```
firmware/   AVR C implementation: cordic.c, poly.c, fixed_point.h, UART bench harness, Makefile
hostgen/    Python host-side generator (coefficient/table generation, reference values)
data/       measured results per Q format: algo, angle, outputs, error, cycle ticks
page/       self-contained animated HTML explainer (single file, no dependencies)
manim/      animation scenes used for the recorded walkthrough
SPEC.md     full design document
```

## The interesting parts

- `firmware/fixed_point.h` — width-generic fixed-point layer; the same algorithm sources
  compile for all three Q formats.
- `firmware/cordic.c` — shift-add rotation loop with the gain constant 1/K prescaled into
  the initial vector, so there is no per-iteration multiply.
- `firmware/poly.c` — Horner evaluation built on the 8-bit hardware multiplier; Taylor
  and minimax coefficient sets are swappable to show why equal-degree minimax wins on
  worst-case error.
- `data/*.csv` — the measurements: per-angle sin/cos outputs, error vs. reference, and
  cycle counts for every algorithm × width combination.
- `page/index.html` — an animated, narration-friendly explainer of the whole story
  (fixed-point representation, CORDIC convergence, polynomial term-by-term fit), written
  to accompany a recorded walkthrough for students.

## Building

Firmware: `make` in `firmware/` (avr-gcc). Bench results stream over UART.
Explainer: open `page/index.html` in a browser — fully self-contained.
