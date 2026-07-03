# Card 2 — Coherence

> Reference squaring, fanout, and PLL-based generation of 32 MHz (for SX1262)
> and 905 MHz (for the mixer LO). The metrological core of the project.

## Function

This card receives the external 10 MHz GPSDO sine-wave reference and turns it into
two coherent derived frequencies, both phase-locked to the GPSDO at parts-per-billion
stability:

- **CLK0 = 32 MHz**, sine-mode, fed to the SX1262 XTA pin via amplitude conditioning
  (V0.2 change, see below).
- **RFOUT_A = 905 MHz**, +5 dBm, fed to the mixer LO port on Card 3 (after −1 dB
  pad to deliver +7 dBm at the mixer, see V0.2 changes in [`docs/CHANGELOG.md`](../CHANGELOG.md)).

## Schematic (V0.2)

```text
GPSDO 10 MHz ref in (sine, 0 dBm)
        |
        v J1 SMA panel
        |
   [C1 100 nF NP0 AC coupling]
        |
        +-- [R1 50 Ω termination to GND]
        |
        v
   +-------------------------+
   | U1 ADCMP562 comparator  |
   | propagation < 600 ps    |
   | jitter < 1 ps RMS       |
   |                         |
   | +IN ◄── (signal)        |
   | −IN ◄── Vref (1.65 V    |
   |          via R2/R3 div) |
   | Q   ──► CMOS 3.3 V out  |
   +-------------------------+
        |
        v 10 MHz CMOS rail-to-rail
        |
  Fanout to two PLLs (single fanout point under U1)
        |
        +─────────────────┐
        |                 |
        v                 v
   +--------------+  +--------------+
   | U2 Si5351C-B |  | U3 ADF4351   |
   | (CLKIN input)|  |              |
   | I²C @ 0x60   |  | SPI          |
   +--------------+  +--------------+

U2 Si5351C-B  **[V0.4 CHANGE: C variant — the Si5351A has no CLKIN pin
   and cannot accept an external reference; the Adafruit breakout is
   A-variant and is NOT suitable]**
   CLKIN = 10 MHz CMOS from fanout (CLKIN accepts up to 100 MHz)
   PLL_A multiplier = 64 (a=64, b=0, c=1) → VCO_A = 640 MHz
   **[V0.4 FIX: V0.2 specified ×32 → 320 MHz, outside the 600–900 MHz
   VCO range (AN619); the PLL cannot lock there]**
   MS0 divider = 20 → CLK0 = 32 MHz (integer PLL + integer divider =
   lowest-jitter mode)

   **[V0.4 FIX] Output: CMOS 8 mA drive. The Si5351 has no sine output
   mode — the register set offers drive strength only; the V0.2 "sine
   mode" change was not implementable. Sine shaping is done by the LPF.**

   CLK0 CMOS output → 3-pole LPF fc=40 MHz (V0.2)
                       (L=470 nH, C=100 pF / 47 pF / 100 pF, π topology;
                       ~20–25 dB at H3 = 96 MHz → residual H3 ≈ −30 dBc,
                       adequate for a clock input)
                   → **[V0.4 CHANGE] resistive divider ~2:1 (1 kΩ/1 kΩ)
                       for ≈ 1.0 Vpp at XTA — the V0.2 target of 330 mVpp
                       is below the 0.6–1.2 Vpp external-drive window
                       (SX1262_CHIRP upstream guidance)**
                   → C2 1 nF NP0 coupling
                   → To Card 3 SX1262 XTA pin (xtal removed, XTB floating)

U3 ADF4351
   REF in: 10 MHz CMOS from fanout
   R-counter = 1, charge pump = 2.5 mA
   INT = 362, FRAC = 0 (integer-N; MOD field = 2, don't-care) → VCO = 3620 MHz
   Output divider = 4 → RFOUT_A = 905 MHz
   **[V0.2 CHANGE] Drive level register = +5 dBm
                    (sufficient for −1 dB pad → +7 dBm at mixer LO)
                    Was +5 dBm with −2 dB pad in V0.1, giving only +3 dBm
                    at mixer, below ADE-R3+ nominal +7 dBm requirement.**
   MUXOUT = digital lock detect → RP2040 GPIO11 for verification

RFOUT_A (905 MHz, +5 dBm)
   |
   v
   π pad −1 dB (V0.2, was −2 dB)
   R 5.6 Ω series, R 470 Ω shunts ×2
   |
   v +4 dBm (with module typical +5.5 dBm output)
   |
   To Card 3 mixer LO port via short SMA coax
```

## V0.2 changes from V0.1

| Change | Reason |
|--------|--------|
| Si5351 CLK0 → **sine output mode** | V0.1 CMOS rail-to-rail signal exceeded SX1262 XTA input rating. Sine mode + divider produces ~330 mVpp, within datasheet specs and minimizes phase noise contribution. |
| **+ 3-pole LPF on CLK0** | V0.1 lacked harmonic filtering on the 32 MHz output. Si5351 sine mode still produces some H3, H5; the LPF cleans it before XTA. |
| **+ resistive divider on CLK0** | Combined with sine mode, divider sets exact amplitude expected by SX1262 XTA. |
| LO pad reduced **−2 dB → −1 dB** | Compensates for ADF4351 module typical insertion loss and brings nominal +7 dBm at mixer LO port. |
| ADF4351 drive register raised | Net effect: +7 dBm at mixer instead of marginal +3 dBm in V0.1. |

## V0.4 changes from V0.2 (design review)

| Change | Reason |
|--------|--------|
| Si5351**A** → **Si5351C-B** | The A variant has no CLKIN and cannot lock to the external 10 MHz reference. The Adafruit breakout is A-variant. |
| PLL ×32/÷10 → **×64/÷20** | V0.2 VCO = 320 MHz is outside the 600–900 MHz VCO range; cannot lock. 640 MHz is in range, all-integer. |
| "Sine output mode" removed | No such mode exists in the Si5351 register set. CMOS 8 mA + the existing LPF achieves the intent. |
| XTA divider ~10:1 → **~2:1** | 330 mVpp is below the 0.6–1.2 Vpp external XTA drive window; target ≈ 1 Vpp. |
| ADF4351 registers regenerated | V0.2 R4 encoded RF divider /1 (output 3620 MHz, not 905) and R2 encoded R-counter = 0 (invalid). Field-verified set; integer-N mode enabled. |

## PLL configuration code (RP2040, C with pico-sdk)

```c
// Si5351C init: PLL_A locked to external 10 MHz on CLKIN, CLK0 = 32 MHz
// V0.4: ×64/÷20 (VCO 640 MHz, in the 600–900 MHz range); CMOS output,
// sine shaping done by the external LPF ("sine mode" does not exist).
void coherence_init_si5351(i2c_inst_t *i2c) {
    si5351_init(i2c);
    si5351_set_ref_source(SI5351_REF_CLKIN);      // C variant only
    si5351_set_clock_source(SI5351_CLK0, SI5351_PLL_A);

    // PLL_A: integer multiplier 64 → VCO 640 MHz from 10 MHz ref
    si5351_setup_pll(SI5351_PLL_A, 64, 0, 1);

    // MS0: integer divider 20 → 32 MHz output
    si5351_setup_multisynth(SI5351_CLK0, 20, 0, 1);

    si5351_set_drive_strength(SI5351_CLK0, SI5351_DRIVE_8MA);

    si5351_clock_enable(SI5351_CLK0, true);
}

// ADF4351 init: 905 MHz output, +5 dBm drive
void coherence_init_adf4351(spi_inst_t *spi, uint cs_le) {
    // 6-register sequence, V0.4 regenerated and field-verified.
    // PFD = 10 MHz, INT = 362, FRAC = 0 → VCO 3620 MHz, /4 → 905 MHz.
    // Integer-N mode (LDF/LDP/ABP/charge-cancel set accordingly).
    // Reg 5: LD pin = digital lock detect
    adf4351_write_reg(spi, cs_le, 0x00580005);
    // Reg 4: fundamental feedback, RF divider /4 (V0.2 value encoded /1
    //        → 3620 MHz out!), band-select 50 kHz, out enable, +5 dBm
    adf4351_write_reg(spi, cs_le, 0x00AC803C);
    // Reg 3: ABP 3 ns + charge cancelation (integer-N), clk div 150
    adf4351_write_reg(spi, cs_le, 0x006004B3);
    // Reg 2: MUXOUT = lock detect, R = 1 (V0.2 value encoded R = 0,
    //        invalid), CP 2.5 mA, LDF/LDP integer-N, PD positive
    adf4351_write_reg(spi, cs_le, 0x18004FC2);
    // Reg 1: prescaler 4/5, phase = 1, MOD = 2 (don't-care with FRAC = 0;
    //        the V0.2 doc said "MOD = 4096" — impossible in a 12-bit field)
    adf4351_write_reg(spi, cs_le, 0x00008011);
    // Reg 0: INT = 362, FRAC = 0
    adf4351_write_reg(spi, cs_le, 0x00B50000);
}
```

## Phase noise budget (V0.2 revised)

| Source | Phase noise @ 1 kHz | Contribution at 10 MHz IF |
|--------|---------------------|----------------------------|
| GPSDO 10 MHz | −125 dBc/Hz | negligible |
| Si5351 + 32 MHz lock | −110 dBc/Hz @ 32 MHz | indirect, via SX1262 PLL |
| **Si5351 sine mode (V0.2)** | improved by ~5 dB vs CMOS | net contribution lower |
| ADF4351 + 905 MHz lock | −95 dBc/Hz @ 905 MHz | dominant term |
| SX1262 PLL @ 915 MHz | −95 dBc/Hz @ 915 MHz | similar to LO |
| Mixer ADE-R3+ | negligible | added phase noise floor |
| **Total at 10 MHz IF** | ≈ **−95 dBc/Hz @ 1 kHz** | |

Result remains adequate for the 36 dB of pulse compression gain at SF12 / BW = 7.8 kHz.

## Layout notes

- **Star ground under U2 Si5351A.** All ground returns converge here. AGND and DGND
  of the Si5351 module joined by ferrite FB2 (BLM18AG121), point connection only.
- **Faraday cage on U2/U3.** Si5351 internal VCO at 320 MHz, ADF4351 internal VCO at
  3620 MHz — both can radiate. Soldered shield can with windows for connectors.
- **U1 squarer placement.** Place ADCMP562 close to J1 SMA, with 50 Ω microstrip
  trace from J1 to comparator input. Local decoupling 10 µF tant + 100 nF X7R
  within 5 mm of pin 4 Vcc.
- **Single fanout point under U1.** No stub branching; one trace to U2 input, one
  to U3 input, both ≤ 30 mm.

## Verification procedure

1. **U1 alone.** Power up Card 1, verify Vref = 1.65 V at U1 pin 3. Apply 10 MHz
   sine 0 dBm at J1, scope at TP1 (U1 Q output): clean CMOS 3.3 V square wave,
   10 MHz exact, jitter < 100 ps RMS visible.

2. **Si5351 alone.** RP2040 sends I²C config from `coherence_init_si5351()`.
   Frequency counter at TP2 (CLK0 output, sine mode) reads 32 MHz ± 0.001 Hz.
   Spectrum analyzer at TP2: clean sine, harmonics > 40 dB below fundamental
   (after LPF).

3. **ADF4351 alone.** RP2040 sends SPI config from `coherence_init_adf4351()`.
   Spectrum analyzer at TP3 (post-pad LO output): 905 MHz at +4 dBm ±0.5 dB.
   Read MUXOUT GPIO at RP2040: lock detect = high.

4. **Combined cohérence.** Both PLLs running, GPSDO disconnected briefly:
   verify both outputs drift together (proving they share the same reference)
   and recover within 5 seconds when GPSDO reconnected.

## Bill of materials (Card 2 only, V0.2)

See [`hardware/bom/card-02-coherence.csv`](../../hardware/bom/card-02-coherence.csv).
Total ~€53, up from €50 in V0.1 due to added LPF components.
