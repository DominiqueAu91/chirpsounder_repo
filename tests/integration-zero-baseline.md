# Integration test — zero baseline (TX → RX888, no antenna)

The single most informative bench session in the project: the complete TX
chain into a dummy load, a −60 dB sample into the station RX888, the complete
RX pipeline (`radiod` Mode A channel → `dechirp_basic.py`). One evening
answers, with measurements instead of datasheets:

1. end-to-end coherence of the whole architecture,
2. the real phase-noise density at the IF (replaces the placeholder table in
   `simulations/phase-noise/budget.md`),
3. **pulse-to-pulse phase continuity of `SetTxContinuousPreamble`** at the
   chirp wrap — the assumption the TID/Doppler mode rests on, which no
   datasheet states,
4. absolute frequency accuracy of the full multiplication chain,
5. spectral purity at the antenna port (regulatory pre-check).

Run this before the first antenna connection, and re-run after any Card 2/3
modification.

## Setup

```text
TX (full chain) ──► coupler ──► LPF ──► 30 dB / 25 W attenuator ──► dummy load
                      │
                      └── −20 dB tap (+20 dBm at 10 W)
                            │
                            ▼
                        30 dB pad ──► 10 dB pad ──► RX888 input  (≈ −20 dBm)
```

- Total tap-to-RX attenuation −60 dB: 10 W → −20 dBm at the RX888, safely
  below A/D full scale at moderate gain; trim the radiod `gain` so the tone
  peaks 20–30 dB below clipping.
- Both instruments on the **same GPSDO** for steps 1–4 (single-reference
  test); repeat step 4 with the RX on its own GPSDO to characterize the
  bistatic case.
- Host clock disciplined (gpsd + chrony) as per the RX documentation.

Create the RX channel (Mode A, fixed — no tracking needed):

```sh
tune --radio hf.local --ssrc 5001 --mode iq --samprate 96k \
     --encoding f32le --low -46k --high +46k \
     --destination chirp-iq.local --frequency 10m120
```

## Procedure and pass criteria

### 1. Spectral sanity

TX one dwell (SF12, BW 7.8125 kHz). Observe the channel with a waterfall or
`pcmrecord` + offline FFT.

- Chirp centered at 10.120 MHz ± the expected programmed offset.
- H2/H3 at the coupler tap: < −50 / −60 dBc post-LPF (spectrum analyzer if
  available; otherwise retune a second radiod channel to 20.24 / 30.36 MHz
  and compare levels — the RX888 sees the whole band, use it).

### 2. Compression gain

Record ≥ 60 s (≥ 114 symbols at SF12). Run `dechirp_basic.py`.

- Single dominant range bin at the cable/pipeline delay (≈ 0, constant).
- Peak-to-background ≥ 30 dB single-symbol (theory 36 dB minus implementation
  loss; > 6 dB shortfall means a coherence or level problem, not noise).

### 3. IF phase-noise measurement

Dechirp one symbol stream; the result is a near-DC tone. FFT with ≥ 10 s of
data (0.1 Hz resolution); read the single-sideband skirt L(f) at 10, 100,
1000 Hz offsets, normalized to the tone power.

- Compare against `simulations/phase-noise/budget.md`; expected ballpark
  −80…−85 dBc/Hz at 1 kHz with the V0.4 Si5351 path, −95…−100 after E1.
- **Update the budget table with the measured values.**

### 4. Pulse-to-pulse phase continuity (the TID-mode gate)

Extract the dechirped phase of each symbol (argument of the per-symbol
correlation peak). Plot phase vs symbol index over ≥ 60 s.

- Pass for coherent Doppler integration over N symbols: phase increments
  consistent with a constant offset, residual step at each wrap
  σ_Δφ < 0.1 rad. A deterministic per-symbol phase slip is acceptable
  (it calibrates out); a **random** wrap phase is not — it would cap
  coherent integration at one symbol and demote the TID mode to
  incoherent averaging. This is the measurement that decides.

### 5. Absolute frequency accuracy

With both ends on one GPSDO, the dechirped tone offset measures the chain's
synthesis error only.

- |offset| < 0.1 Hz (limited by INT-N exactness: 905 and 915 MHz are both
  exact multiples of the 10 MHz PFD; any residual indicates a programming
  error, not drift).
- Repeat with independent GPSDOs: |offset| < 1 Hz and Allan-stable over
  10 min — the bistatic readiness figure.

### 6. Thermal soak

1 h continuous duty-cycle pattern (30 s ON / 30 s OFF accelerated). Log
V_fwd, T_PA, dechirped amplitude and phase.

- Amplitude drift < 1 dB, no thermal trip below 60 °C, phase drift smooth
  (no jumps — jumps indicate a connector or the Card 2 shield resonating,
  not physics).

## Recording the results

Append a dated results section to this file per session (instrument, serial
numbers, radiod gain, raw files kept under `/dev/shm` are ephemeral — copy
the processed CSV/PNG into `tests/results/zero-baseline-YYYYMMDD/`). The
step-3 and step-4 numbers gate the V1.0 architecture decision (review items
E1/E2).
