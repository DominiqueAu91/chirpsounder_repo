# BPF 30m — 5-pole Chebyshev synthesis

## Specification

| Parameter | Value |
|-----------|-------|
| Topology | Capacitively-coupled parallel resonators |
| Order | 5 poles |
| Type | Chebyshev |
| Ripple | 0.1 dB |
| Center frequency | 10.120 MHz |
| Bandwidth -3 dB | 500 kHz |
| Source/load impedance | 50 Ω |
| Insertion loss target | < 2 dB |
| Stop-band attenuation @ ±2 MHz | > 40 dB |

## Synthesis values (theoretical)

From standard Chebyshev tables (Zverev, Matthaei-Young-Jones), the
g-coefficients for a 5-pole 0.1 dB ripple filter are:

```
g0 = 1.0000
g1 = 1.1468
g2 = 1.3712
g3 = 1.9750
g4 = 1.3712
g5 = 1.1468
g6 = 1.0000
```

For capacitively-coupled parallel-resonator topology with Q_loaded ≈ 150
on T50-6 toroids:

| Component | Value | Realization |
|-----------|-------|-------------|
| L1..L5 | 2.2 µH | T50-6 yellow, 24 turns 0.5 mm enameled |
| C1..C5 | 100 pF NP0 + 5–30 pF trimmer | 1206 SMD + Sprague-Goodman |
| Cc_io (input/output) | 22 pF NP0 1206 ±2% | |
| Cc_12, Cc_45 | 4.7 pF NP0 1206 ±0.25 pF | |
| Cc_23, Cc_34 | 3.3 pF NP0 1206 ±0.25 pF | |

## Validation needed

These values are **theoretical** from synthesis. Bench measurement is required
because:

- T50-6 actual µ_i can vary ±10% from nominal
- Wire winding inductance has ±5% variance
- NP0 caps have ±2% tolerance
- Stray capacitance from PCB layout adds 1-3 pF

Plan: use NanoVNA to characterize one-cell prototypes, adjust trimmers, then
build full filter with measured starting values.

## Tools recommended

- **Elsie** (Tonne Software, free) for initial synthesis
- **AADE Filter Design** (legacy, still works)
- **scikit-rf** Python library for in-notebook validation
- **NanoVNA-Saver** for measurement export

## Open question

Worth simulating in QUCS or Sonnet to assess sensitivity to component
tolerances? Could justify changing to wider-bandwidth design if alignment
proves too sensitive. Deferred to V0.3 if bench results show issues.
