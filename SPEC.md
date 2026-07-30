# Spec: Informational Document — Computing Fixed-Point sin/cos on the ATxmega128A1U (CORDIC vs. Multiply-Based)

**Deliverable:** a self-contained **HTML page** that serves as the visual backdrop for a **recorded video voiceover** by the author. Not graded, not an exercise — an informational resource the professor will post for curious students. The HTML itself likely won't be distributed; the *video* is the artifact students see, so the page is designed to be **narrated over**, not read silently.

**Author:** Logan (PI), writing/recording it himself. **Audience:** curious undergrads; assume some programming, light on EE specifics — explain fixed-point, FPU absence, and the algorithms from near-first-principles.

**Target part:** ATxmega128A1U (8-bit AVR, **has** hardware 8x8->16 `MUL`, **no** FPU).

---

## 0. Design constraint: everything is narration-friendly

Because the page is talked *over* in a recording:
- Animations must have **manual controls** -- play/pause, step-forward/back, scrub, and adjustable speed. The author needs to pause on a frame and explain it, or step one CORDIC iteration at a time while narrating.
- Animations should **loop cleanly** and be **re-triggerable** so a take can be redone.
- No reliance on hover-only reveals (hard to narrate and capture on video); prefer explicit buttons/sliders with visible state.
- Layout is **section-by-section, top-to-bottom**, matching a spoken walkthrough order. Each major concept is its own screen-height block so the recording can scroll-and-pause.
- On-screen text is **sparse** -- captions, labels, equations, short callouts (the voiceover carries the detail).
- Self-contained single HTML file (inline CSS/JS, no external CDN dependence that could fail mid-record). SVG/Canvas for animations; no build step to view.

---

## 1. Purpose of the document

Walk through, with animated visuals, **how a computer evaluates sin/cos with no FPU**, then show **two methods implemented on the xmega** and **how each scales with precision**. Three movements:
1. **Theory** -- the problem (no FPU, fractional outputs), fixed-point, and how each algorithm works, animated.
2. **Implementation** -- both algorithms shown as real working xmega code.
3. **Comparison** -- measured cost scaling across fixed-point widths, presented as authored results.

Through-line: **CORDIC trades the multiplier for a small angle table and many iterations; the polynomial method trades the table for multiplies the xmega can actually do in hardware.** The document characterizes how that tradeoff plays out as precision grows.

---

## 2. Theory section (animated)

### 2.1 The problem
- A calculator/MCU gets an angle, must return a fractional length. The xmega has no FPU and only add/sub/shift/`MUL`. How?
- Animated **unit-circle -> sine-wave** unrolling (rotating vector, y-projection traces the wave). Sets the geometric meaning of sin/cos.

### 2.2 Fixed-point (animated bit-format visualization)
- Why not floats: no FPU, software float is expensive. Use fixed-point.
- **Animated bit-format diagram:** an N-bit register with sign / integer / fraction fields highlighted; show a value like 0.707 represented, and `value x 2^FRAC_BITS -> integer` scaling (video's 0.60725 -> 39 in Q1.6). Slider to change FRAC_BITS and watch representable precision change live.
- Show quantization: as FRAC_BITS drops, representable points coarsen -- visually motivates the later precision-vs-width results.

### 2.3 Lookup-table method (brief, animated)
- The "usual" method: precomputed table + interpolation; index the angle, interpolate between neighbors.
- Animated: angle -> index -> neighboring entries -> interpolated output.
- Cost: memory for the table, and interpolation needs multiply+divide. Motivates the alternatives.

### 2.4 CORDIC (animated vector rotation + convergence) -- headline visual
- Core idea: rotate a vector by successively smaller angles, each chosen so `tan` is a power of two -> the rotation "multiply" becomes a **bit shift**. Direction each step from the sign of the residual angle (binary-search feel).
- **Animation, step-controllable:** a vector rotating toward the target angle, one iteration per step; show the residual angle shrinking, the +/- direction choice, the shift-based update. Author steps through iterations while narrating.
- **Convergence sub-animation:** accuracy vs. iteration count -- visually show the ~**1 bit per iteration** linear convergence.
- **The gain constant K:** animate that the per-iteration cosine factors all multiply to one fixed scalar (1/K ~ 0.6072...), independent of angle, collapsing into a single prescale of the initial x. "No per-iteration multiply, just one constant baked into the start."
- **Honest callout (on-screen + narration):** CORDIC still needs a small **atan(2^-i) angle table** -- it eliminates the *sine* table, not all tables. Table length ~ fractional bits (beyond that the atan values round to zero). Mirrors the reference video's "ironically still a lookup table, just a tiny one."

### 2.5 Polynomial method (animated term-by-term approach)
- Core idea: approximate sin/cos by a polynomial; evaluate with Horner using the xmega's hardware `MUL`. No angle table -- coefficients are inline constants.
- **Animation:** start with the linear term, add successive terms, watch the polynomial curve converge onto the true sine over the reduced interval. Step-controllable so each added term is narratable.
- Both variants the comparison uses:
  - **Taylor** -- intuitive, derived from the series; more terms for given accuracy.
  - **Minimax** -- coefficients minimize worst-case error; fewer terms for same accuracy. Animate the error curve (Taylor's error grows toward interval edges; minimax's ripples evenly -- the equioscillation picture).
- **Argument reduction:** animate folding an arbitrary angle into a small base interval via quadrant/periodicity identities, since both methods need a reduced argument.

---

## 3. Implementation section (both algorithms, real xmega code)

Author implements **both** and shows the actual code (code is displayed and explained, not blanked).

- **Fixed-point format**, parameterized by compile-time width so one codebase serves every measured point:
  - `-DTOTAL_BITS={8,16,32}` -> backing type `int8_t`/`int16_t`/`int32_t`.
  - `-DFRAC_BITS=k` -> Q(sign+integer+fraction); enforce `FRAC_BITS <= TOTAL_BITS-2` (static assert).
  - No wider than 32-bit: the limit is measurement cleanliness, not SRAM. All widths >8 are multi-limb `MUL` sequences (AVR has only 8x8->16); 16/32-bit use libgcc's tight `__mulhi3`/`__mulsi3` paths, while 64-bit's generic `__muldi3` overhead reflects routine quality, not the algorithmic tradeoff. Three native points (L = ceil(TOTAL_BITS/8) in {1,2,4}) characterize scaling.
- **Compile-time constant generation (host-side):** a small host program emits a `PROGMEM` header for the chosen width -- the **atan(2^-i) table** (length ~ FRAC_BITS, rounded to Q-format), the **1/K gain** computed over **exactly the iterations performed** (finite-iteration K, NOT asymptotic 1.64676...; the wrong one injects constant bias -- show this), and the **Taylor/minimax coefficients** scaled to Q-format. Makefile regenerates per width.
- **CORDIC arm:** rotation-mode loop, `x=1/K`, `y=0`, `z=angle`; per iteration sign(z) -> +/- shift-add update of x,y and +/- atan-table step on z. No multiply in the loop. Watch avr-gcc's arithmetic-shift-with-carry codegen on wider formats; inline asm if poor.
- **Polynomial arm:** Horner in fixed point using hardware `MUL`; Taylor (primary) + minimax (second variant). Coefficients inline. Multi-limb multiply at 16/32-bit is where `MUL` cost concentrates -- inspect `-S`/disassembly and show it (the "did the compiler use MUL / emit clean shifts?" reveal is good narration).
- **C with inline asm where gcc misses intent**; raw asm for a core loop if warranted. A generated-assembly snippet is on-theme for the audience.

---

## 4. Comparison section (authored results, animated/interactive plots)

Framed as **characterizing each algorithm's cost scaling**, not hunting a crossover -- three points (L in {1,2,4}) fit a scaling trend; any crossover is an **extrapolation**, labeled as such.

### 4.1 What's measured
Per (TOTAL_BITS, FRAC_BITS): **cycles** (CORDIC, Taylor, minimax), **accuracy** vs. host `sinf`/`cosf`, **operation count** (CORDIC iterations, polynomial terms), **limb count** L. Op-count logged separately so cost decomposes into **(operation count) x (per-operation cost)** rather than one collapsed exponent.

### 4.2 Measurement methodology (shown/narrated, not hidden)
- On-chip **TC timer in stopwatch mode**: start/stop = writing clock-select bits (~1-2 cycles, negligible, no overhead subtraction).
- **Unified protocol:** fixed **K-loop** (same K all configs) inside one timer window + **width-escalating prescaler** P (8->1, 16->2, 32->4). Measured ticks = K*C/P; recover cycles = ticks*P/K. K-loop divides quantization to **+/-P/K per run**; prescaler keeps the K-inflated count under the 16-bit counter's **65535-tick** ceiling. Select P = smallest divider with K*C_est/P < 65535; fixed K bounded by the tightest config (32-bit). Report +/-P/K per config.

### 4.3 Predictions to state then test
- **CORDIC** ~ O(L^2): iterations grow with FRAC_BITS (~linear in width) x per-iteration shift-add linear in limbs.
- **Polynomial** also trends ~quadratic in the multiply-dominated regime (schoolbook `MUL` ~O(L^2) x modestly growing term count). Both may land near degree 2 -- the interesting findings are the **constant factor** and whether exponents *actually* differ.

### 4.4 Plots (animated / interactive, narration-friendly)
1. **Cycles vs. L (log-log)** per algorithm -> fitted scaling exponent; fit with and without the L=1 point (8-bit may sit below trend -- native single `MUL`, no multi-limb plumbing). Report residuals. Headline result.
2. **Per-operation cost vs. L** -- cycles / count, isolating per-op scaling from count scaling.
3. **Operation count vs. FRAC_BITS** -- confirms the count side of the factorization.
4. **Accuracy vs. FRAC_BITS** per algorithm.
5. **CORDIC accuracy vs. iteration count** -- the ~1-bit/iteration linear-convergence plot (ties back to 2.4).
6. **Extrapolated comparison** -- project fitted curves beyond the measured range to show where (if at all) they'd cross, explicitly labeled extrapolation with three-point uncertainty.
7. Optional: **flash/code size** per algorithm per width (CORDIC table vs. polynomial coefficients).

Interactive sliders (sweep width, sweep iteration count) welcome but must have **visible state**, not hover-only, for recordability.

---

## 5. Honest framing to preserve throughout

- CORDIC is **not** LUT-less -- it needs the small atan table; only the *sine* table is removed and the gain collapses to one prescale. Say so explicitly, as the reference video does.
- The polynomial arm is genuinely data-table-free (inline coefficients).
- The "crossover" is an extrapolation from three points, not a measured event; the real result is the **scaling characterization** and **constant-factor comparison** on a part that *has* a hardware multiply.
- Finite-iteration K vs. asymptotic K: use the finite one; flag the bias.

---

## 6. Build / production notes

- Single self-contained HTML file, inline assets, SVG/Canvas animations, manual controls on every animation.
- Author records voiceover over the page; design pacing and section breaks for a spoken walkthrough.
- Companion code (xmega C/asm + host generator + Makefile sweep) shown *in* the doc as snippets and produced as a real working project the author builds first to generate the genuine numbers behind section 4.
- Production order: (1) build the real xmega project + host generator, verify constants against `sinf`, get one disassembly cycle estimate to lock K and the P table; (2) run the sweep, collect real numbers; (3) build the HTML with animations and the *real* plotted data; (4) record voiceover.

## 7. Possible additional visuals (author flagged "some others would be nice")
- Side-by-side "same angle, both algorithms" run, stepping in lockstep, each converging to the same fixed-point result.
- The deg -> fixed-point-radian conversion (the irony that prepping CORDIC's input needs a multiply) animated as a pre-step.
- A "what the LCD shows" recreation matching the reference video's output (0.718/0.687 vs true 0.707) to ground the precision discussion.
- Quadrant-extension animation (first-quadrant result reflected/swapped into the other three).
- Error-vs-true-curve overlay that updates as FRAC_BITS or iteration/term count changes.
