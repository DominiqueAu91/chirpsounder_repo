# TX & applicative review — input for V0.4

Scope: transmitter cards 1–6, firmware skeleton, LFM theory, phase-noise and
filter simulations, regulatory doc. Receiver (V0.3 ka9q backend) out of scope.
Every quantitative claim below was recomputed independently; datasheet-level
claims are referenced to the source.

Severity classes: **B** = blocker (does not work as documented),
**M** = major (works degraded, unsafe, or claim/hardware mismatch),
**E** = enhancement.

---

## Card 2 — Coherence: four blockers

### B1. Si5351A has no reference input

The BoM specifies the Adafruit Si5351 breakout, which carries the Si5351**A**.
The A variant has **no CLKIN pin** — it accepts only a 25/27 MHz crystal.
"PLL_A locked to 10 MHz reference" is not possible with this part. Options:

1. **Si5351C-B** (CLKIN up to 100 MHz) — the drop-in-intent part; needs a
   custom footprint or a C-variant breakout (rarer but they exist).
2. Overdrive the XA pin with the 10 MHz squared reference through a coupling
   cap — works in practice, out of datasheet spec; acceptable for a prototype
   if documented as such.
3. Delete the Si5351 entirely — see E1 (direct 32 MHz GPSDO).

### B2. PLL configuration outside VCO range

`si5351_setup_pll(PLL_A, 32, 0, 1)` → VCO = 10 × 32 = **320 MHz**. The
Si5351 VCO range is **600–900 MHz** (AN619). The documented configuration
cannot lock. Correct integer-only configuration:

```text
PLL_A = 10 MHz × 64 = 640 MHz   (in range, integer)
MS0   = 640 / 20    = 32 MHz    (integer divider — lowest jitter mode)
```

### B3. "Sine output mode" does not exist

The Si5351 output stage is CMOS only; the register set offers drive strength
(2/4/6/8 mA), not waveform selection. `SI5351_WAVE_SINE` corresponds to no
register. The V0.2 change as written is not implementable. The *intent*
survives with: CMOS out (8 mA) → the existing 3-pole LPF (which then does the
sine-shaping, not just harmonic cleanup) → attenuator. Note the 3-pole
π at fc = 40 MHz gives roughly 20–25 dB at H3 (96 MHz); with the square
wave's H3 at −9.5 dBc the result is ≈ −30 dBc — adequate for a clock input,
but re-state the spec honestly.

### B4. XTA drive amplitude too low

The design targets ~330 mVpp at XTA. The upstream SX1262_CHIRP project (which
this TX derives from) specifies **0.6–1.2 Vpp** for external XTA drive, xtal
removed, XTB floating, DC-blocked. Resize the divider for ≈ 1 Vpp
(e.g. ~2:1 from the filtered CMOS level instead of the current ~10:1).

---

## Card 3 — RF-Low: one blocker, one major

### B5. E22-900M30S is the wrong module — and it breaks the coherence claim

The Ebyte E22-900M30S contains SX1262 **plus a +30 dBm PA, LNA, RF switch
(TXEN/RXEN pins), and an onboard TCXO**. Consequences:

- **XTA is not accessible** on the potted module: the external 32 MHz cannot
  be injected. Without injection, the internal reference free-runs at
  ±2–10 ppm → **±1.8–9.2 kHz at 915 MHz, comparable to or larger than the
  entire 7.8 kHz chirp bandwidth**, and orders of magnitude away from the
  ~1×10⁻⁹ fractional stability a coherent SF12 dwell requires
  (1/(2·0.524 s) ≈ 1 Hz at 915 MHz). Design principle 1 collapses.
- Output is +30 dBm class, not the +14 dBm the RF budget assumes, and the
  module PA's linearity/harmonics enter the chain uncharacterized.
- TXEN/RXEN control appears nowhere in the GPIO map.

Fix: a **bare-SX1262 module that exposes the crystal** (Waveshare Core1262,
NiceRF SX1262, Ebyte E22-900M22S) with the xtal/TCXO removed and the 32 MHz
injected per B4 — exactly the upstream SX1262_CHIRP procedure — or the bare
chip on Card 3 (V1.0). BoM delta ≈ €0.

### M2. Mixer level plan violates level-7 operation

RF port drive is +6 dBm against a +7 dBm LO — essentially LO-level drive on a
level-7 mixer, deep in compression (guideline: RF ≤ LO − 10 dB). Two honest
observations before the fix: the chirp is constant-envelope, so two-tone IMD
regrowth does not apply; and the m = n spur family for 915/905 MHz lands at
n × 10 MHz, which the IF BPF and output LPF remove. So the design "works" —
but conversion loss becomes drive-dependent and out of datasheet conditions.
Recommended: pad the SX1262 down to ≈ −3…0 dBm at the RF port and recover
the ~6 dB with a cheap 10 MHz gain stage after the BPF (second ERA/GALI or a
BJT feedback amp, ~€2) — which also buffers the filter from the inter-card
load. The budget table then needs one new row and two edits.

---

## Card 1 — Power: one blocker

### B8. LM7812 cannot regulate from a 12 V input

12 V barrel − 0.4 V Schottky = 11.6 V at the LM7812 input; the 7812 needs
≈ 14 V (2–2.5 V dropout). "12V_clean" as designed is an unregulated ~9.5 V
rail tracking the supply. Downstream: the ERA-3SM+ bias, computed for 12 V
((12 − 3.5)/150 Ω = 57 mA), falls to ~40 mA — gain and P1dB degrade.

Fix, minimal and synergistic: specify the external supply as **13.8 V
nominal** (the standard shack PSU) and substitute a low-dropout regulator
(LM2940-12 or MIC29302, dropout < 0.5 V at 1 A). Side benefit: the IRF510 PA
at 13.8 V runs with more comfortable headroom than at 12 V for the 10 W
target. Also verify the ADF4351 Chinese module's input: most accept 5 V
(onboard LDOs) — the "12V_clean for ADF4351" assignment may be moot.

---

## Card 6 — Safety: one blocker, one major

### B9. The AND chain cannot carry the relay coil

As drawn, the coil current path runs through the 4N35 output transistor
(50 mA absolute max, CTR-limited) and the LM393 open collector (≈ 20 mA
sink). A 12 V DPDT relay with 5 A contacts draws 30–80 mA coil current —
neither device can hold it reliably. Keep the series-AND *logic* but let it
gate a logic-level N-MOSFET (2N7000 for < 200 mA, IRLZ series if larger)
that switches the coil; flyback diode stays. One transistor, philosophy
intact.

### M1. The "hardwired 10-minute limit" does not exist

`docs/operating/regulatory.md` claims a wired, non-configurable 10-minute
maximum continuous emission. Card 6 contains no such circuit — the 555 is a
1.7 s retriggerable firmware-liveness watchdog; firmware in `DWELL_TX` keeps
kicking it indefinitely. Either implement it (a CD4060 counting a slow clock,
gated by PTT, reset on PTT release — a genuinely hardwired TX-time limiter
for ~€1) or amend the regulatory doc. A compliance claim must match the
hardware; this one currently doesn't.

### M7. VSWR protection is software-only — free hardware fix available

Antenna-fault protection currently rests on a 50 ms firmware loop plus the
(slow) thermal backstop. The LM393 is a **dual** comparator with one half
unused: V_rev against a threshold into the AND chain = a fast, hardwired
VSWR trip for the cost of three resistors.

---

## Firmware — one blocker, several majors

### B6/B7. SX1262 init sequence: two hard errors

- `SetRfFrequency` value **0xE4400000 is wrong**. With Frf = reg × F_XTAL/2²⁵,
  915 MHz → **0x39300000**. (The comment's formula uses 2³², which matches no
  SX126x convention; as written the chip would be commanded far out of band —
  in practice BUSY/parameter-error, not 915 MHz.)
- **`SetPaConfig` (0x95) is missing entirely**, and `SetTxParams` power byte
  0xFD (−3 dBm) contradicts the +14 dBm target. Per the datasheet's optimal
  settings table, +14 dBm on an SX1262 is `SetPaConfig(0x02, 0x02, 0x00,
  0x01)` + `SetTxParams(power = 0x16)` — yes, the power byte says +22; the
  PA config scales it. Semtech's quirk, worth a comment in the code.

### M4. State machine defects (main.c)

1. `fault_acknowledged` is never set anywhere → the FAULT state is
   unrecoverable without a power cycle.
2. `CW_ID → DWELL_TX` transitions after one 50 ms tick — Core 1 sees the
   CW_ID state for one loop iteration; the callsign never completes. A
   completion flag from Core 1 (or a minimum-dwell timer) is required.
   Same for `CW_ID_FINAL`.
3. The every-10-minutes re-identification required by the regulatory doc has
   no implementation: `PAUSE → DWELL_TX` bypasses CW_ID entirely.
4. On FAULT entry the code path shown never drops `PA_ENABLE` (GP15) —
   the relay opens via the hardware chain, but software should
   belt-and-braces it.
5. Cross-core state sharing via `volatile` enum is fragile on M0+; a
   single-producer flag pair or the pico-sdk FIFO is the clean pattern.

### M5. ADF4351 register set contradicts its own intent

R4 = 0x008C803C encodes RF divider select bits [22:20] = 000 = **÷1** →
output 3620 MHz, not 905 MHz (÷4 = 010). And "MOD = 4096" is impossible —
the MOD field is 12 bits, max 4095; with FRAC = 0 set MOD = 2 and enable
integer-N mode (LDF/LDP) for lower spurs. Regenerate the full register set
with ADIsimPLL or the `adf435x` Python tool and verify lock via MUXOUT.

### M6. ADC inputs one fault away from absolute maximum

At 10 W forward, −20 dB coupling delivers +20 dBm → 3.16 Vpk at the
detector; the DC output sits at RP2040 ADC full scale with zero margin. Any
overshoot (PA transient, mismatch reflection) exceeds VDDIO + 0.3 V absolute
max. Add a 2:1 divider plus BAT54S clamp to 3V3 on ADC0/1; rescale in the
calibration table.

---

## Analysis documents

### M3. Phase-noise budget: method errors (conclusion survives, barely)

Three corrections to `simulations/phase-noise/budget.md`:

1. **Multiplication is ignored.** The Si5351's −110 dBc/Hz at 32 MHz is
   multiplied by N = 915/32 = 28.6 inside the SX1262 PLL bandwidth:
   +29.1 dB → **≈ −81 dBc/Hz at 915 MHz**. This — not the ADF4351's
   −95 dBc/Hz — is the dominant term. The budget's −95 dBc/Hz total is
   ~14 dB optimistic.
2. **Common-reference correlation is ignored** — ironically, the
   architecture's own selling point. RF (×91.5) and LO (×90.5) derive from
   the same 10 MHz; at the 10 MHz *difference*, reference noise inside both
   loop bandwidths contributes scaled by (91.5 − 90.5) = ×1, i.e. at the raw
   −125 dBc/Hz, not multiplied. Only the uncorrelated VCO contributions add
   RSS. Coherence by construction is worth ~+39 dB here and the budget
   doesn't claim it.
3. Integrating the 1 kHz spot value flat across 7.8 kHz is a coarse bound;
   what actually matters for the dechirped product is the multiplicative
   sideband floor after compression.

Net: total ≈ −80…−85 dBc/Hz at 1 kHz, dominated by the 32 MHz path. The
SF12 conclusion ("not phase-noise-limited") still holds with margin — but
the identified dominant term points directly at the highest-leverage
improvement (see E1).

### E-lfm. Conventions note for `lfm-theory.md`

The table uses monostatic radar conventions (Δr = c/2BW, R_ua = cT/2) while
the primary application is one-way oblique sounding (delay resolution 1/BW,
one-way range c/BW). Both are fine; state which convention each row uses.

---

## Enhancements (V0.4 / V1.0 candidates)

### E1. Simplify the 32 MHz path — biggest phase-noise lever

Given M3, the Si5351 is the noise bottleneck *and* (B1–B3) the most
error-prone card. Upstream SX1262_CHIRP's approach: a programmable GPSDO
(Leo Bodnar mini, two outputs) delivering **32 MHz directly to XTA and
10 MHz to the ADF4351** deletes the Si5351, the squarer's second load, the
LPF and the divider — removing three blockers and ~25 dB of multiplied noise
in one move. Cost: ~€150 vs ~€15, and the "any 10 MHz GPSDO" input spec
becomes "Bodnar-class programmable GPSDO". Worth pricing both variants in
the BoM as options.

### E2. DDS alternative (V1.0 question, replacing "two-stage conversion?")

The open question in `overview.md` asks whether to add a second conversion
stage. Answer: no — with the SAW doing image duty and the m = n spur family
landing on filterable IF harmonics, single conversion is sound. The *real*
V1.0 architecture question is different: an AD9834/AD9851 DDS clocked from
the GPSDO generates the LFM **directly at 10 MHz** — no mixer, no SAW, no
ADF4351, no 905/915 MHz synthesis at all, and the phase-noise problem
retreats by 20·log(915/10) ≈ 39 dB structurally. Cost: −€40 BoM. Price paid:
the SF/BW LoRa semantics and SX1262_CHIRP lineage/interop are lost, and the
RP2040 must generate the sweep (trivial: FTW ramp via SPI/DMA). Recommend
keeping the SX1262 baseline for ecosystem compatibility and documenting the
DDS variant as the V1.0 decision point.

### E3. Zero-baseline validation milestone

Before any on-air test: TX into dummy load, −60 dB tap into the RX888, full
chain through `dechirp_basic.py` / the ka9q Mode A channel. This single
bench setup validates end-to-end coherence, measures the actual phase noise
(M3), and answers a question no datasheet does: **whether
`SetTxContinuousPreamble` chirps are phase-continuous pulse-to-pulse at the
wrap instant** — which the TID/Doppler mode silently assumes for coherent
integration across pulses. Upstream claims it; one evening with the RX888
proves it. Suggest adding `tests/integration-zero-baseline.md`.

### E4. Logging: microSD over SPI instead of CH376S

The CH376S (9600 baud UART, thin documentation, FAT16/32 quirks) is the
weakest sourcing item on Card 5. A microSD on SPI1 with FatFs is cheaper,
20× faster, better documented, and frees the USB story: keep USB-CDC as
console only.

### E5. Repo hygiene

- Committed at repo root by accident: `rx-ka9q.md`, `CHANGELOG.md`
  (duplicates of the `docs/` versions) and `v0.2-to-v0.3.diff`. Delete all
  three.
- `docs/cards/04-rf-high.md` references `docs/operating/grounding.md`,
  which does not exist — dead link; either write it (the dual-grounding
  requirement deserves it) or drop the reference.

---

## What is right and should not change

For balance, the review also confirms: the heterogeneous-redundancy safety
philosophy is sound and unusually well argued for a hobby project; every
V0.2 RF correction (ADE-R3+ in-band, SAW as image filter, coupler core
upsizing, NTC relocation) is technically correct; `CalibrateImage
{0xE1, 0xE9}` matches the 902–928 MHz datasheet values; the
`SetTxContinuousPreamble` continuous-chirp approach is validated by the
upstream project; the regulatory discipline (duty cycle, coordination,
response procedure) is exemplary; and the BPF resonator values check out
(100 pF + 5–30 pF trimmer tunes 9.4–10.5 MHz around L = 2.2 µH). The
six-card partition with per-card bench procedures is exactly how this
should be built.

## Suggested sequencing for V0.4

1. Paper fixes first (zero cost): B2, B3, B4, B6, B7, M1-doc-or-hardware
   decision, M5 register regeneration, M3 budget rewrite, E-lfm, E5.
2. BoM swaps: B1 (Si5351C or E1), B5 (bare-SX1262 module), B8 (13.8 V + LDO).
3. Schematic deltas: B9 (MOSFET coil driver), M6 (ADC clamps), M7 (second
   LM393 half), M2 (pad + 10 MHz gain stage).
4. Firmware: M4 items in the skeleton before any flesh grows on it.
5. Bench: E3 zero-baseline before first antenna connection.
