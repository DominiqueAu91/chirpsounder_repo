# Phase noise budget — V0.4 (method corrected)

The V0.2 budget RSS-summed spot values quoted at different carrier
frequencies. That is not how phase noise combines through this chain: noise
transfers to the 10 MHz IF **scaled by the multiplication each path applies**,
and contributions derived from the **shared reference are correlated** between
the RF and LO paths and largely cancel at the difference frequency. Both
effects are first-order; the V0.2 total (−95 dBc/Hz) mixed them up.

## Transfer model

The IF phase is φ_IF = φ_RF − φ_LO with:

```text
RF path: 10 MHz ref ──×3.2──► 32 MHz (Si5351) ──×28.59──► 915 MHz (SX1262 PLL)
LO path: 10 MHz ref ──×90.5──────────────────────────────► 905 MHz (ADF4351)
```

Inside the loop bandwidths of all three PLLs:

- **Reference noise** reaches the RF side ×91.5 and the LO side ×90.5,
  correlated. At the IF difference it appears scaled by (91.5 − 90.5) = ×1:
  the GPSDO contributes at its **raw** level, not multiplied. This is the
  quantitative content of design principle 1 ("coherence by construction")
  and is worth ≈ 39 dB relative to a naive uncorrelated treatment.
- **Additive noise of each synthesizer** (its own PFD/CP/VCO/output noise,
  on top of the multiplied reference) is uncorrelated between paths and adds
  in power. Si5351 additive noise is further multiplied ×28.59 (+29.1 dB) by
  the SX1262 PLL — this is the term the V0.2 budget missed.

Caveat: reference cancellation is exact only for identical loop transfer
functions and zero differential delay; in practice expect 20–30 dB of
suppression rather than perfect cancellation below a few kHz offset —
still enough to make the reference term negligible.

## Budget at 1 kHz offset, referred to the 10 MHz IF

| Term | At its carrier | Transfer to IF | At IF |
|------|----------------|----------------|-------|
| GPSDO reference (Thunderbolt-class, −135…−140 dBc/Hz measured; V0.2 used −125 conservative) | −140 | ×1 (correlated difference) | ≈ −140 |
| Si5351 additive (≈ −112 dBc/Hz at 32 MHz after removing the ref part of the −110 measured) | −112 | +29.1 dB (×28.59 in SX1262 PLL) | **≈ −82** |
| ADF4351 additive (chip in-band floor: −220 + 10·log10(10 MHz PFD) + 20·log10(362) ≈ −99) | −99 | ×1 | ≈ −99 |
| SX1262 PLL additive at 915 MHz | ≈ −99 | ×1 | ≈ −99 |
| ADE-R3+ mixer | < −130 | ×1 | negligible |
| **Total** | | | **≈ −82 dBc/Hz** |

The dominant term is the **Si5351 → SX1262 multiplication path**, ~17 dB
above everything else. The V0.2 figure of −95 dBc/Hz was optimistic by
roughly that margin.

## Impact on pulse compression

What multiplicative phase noise costs after dechirp is the integrated
double-sideband noise around each echo. Taking L(f) ≈ −82 dBc/Hz roughly
flat over the offsets that matter (1/T_sym ≈ 2 Hz to BW/2 = 3.9 kHz):

```text
Sideband total ≈ −82 + 10·log10(3900) + 3 (DSB) ≈ −43 dBc
```

The compressed-pulse peak therefore stands at best ~43 dB above its own
phase-noise pedestal. Against the SF12 processing gain of 36 dB this is
**adequate but no longer generous** — and it caps the benefit of going to
SF13/SF14 (39/42 dB nominal gain) at essentially nothing.

Consequences:

1. SF12 / 7.8 kHz operation: phase noise is not the limiting factor —
   the V0.2 conclusion survives, with ~7 dB margin instead of ~20.
2. Higher-SF modes: gated by the Si5351 path. The single highest-leverage
   improvement is deleting it (review item **E1**: programmable GPSDO
   delivering 32 MHz directly to XTA), which removes the ×28.59 multiplied
   term and returns the budget to ≈ −99 dBc/Hz, ADF/SX-limited.
3. Offsets below 1/T_sym (≈ 2 Hz) do not blur single dwells but produce
   dwell-to-dwell phase wander — the quantity that matters for coherent
   Doppler integration (TID mode). It is dominated by the same Si5351 path
   plus reference flicker, and is best **measured, not modeled**: see
   `tests/integration-zero-baseline.md`, step 4.

## Bistatic note

With independent GPSDOs at TX and RX, the reference terms no longer share a
cancellation path — but at −135…−140 dBc/Hz raw they remain ~40 dB below
the Si5351 term, so the single-site budget carries over unchanged.

## Measurement plan

All numbers above marked "≈" are datasheet-typical placeholders. The
zero-baseline bench (dummy load, −60 dB tap, RX888) yields the real L(f) at
the IF in one session: dechirp a dwell, FFT the tone, read the sideband
skirt directly. Replace this table with measured values before V1.0
decisions (E1 vs E2) are taken.
