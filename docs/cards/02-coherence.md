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
   | U2 Si5351A   |  | U3 ADF4351   |
   | I²C @ 0x60   |  | SPI          |
   +--------------+  +--------------+

U2 Si5351A
   PLL_A locked to 10 MHz reference
   PLL_A multiplier = 32 (a=32, b=0, c=1) → VCO_A = 320 MHz
   MS0 divider = 10 → CLK0 = 32 MHz

   **[V0.2 CHANGE] Output mode: sine wave (was CMOS rail-to-rail)**
   Drive register CLK0_DRV = 010 (4 mA, sine-shaped output)
   Spread spectrum disabled

   CLK0 sine output → **[V0.2 ADDED] 3-pole LPF fc=40MHz**
                       (L=470 nH, C=100 pF / 47 pF / 100 pF, π topology)
                   → **[V0.2 ADDED] resistive divider 1k/100Ω**
                       (attenuation ~20 dB to ~330 mVpp)
                   → C2 1 nF NP0 coupling
                   → To Card 3 SX1262 XTA pin

U3 ADF4351
   REF in: 10 MHz CMOS from fanout
   R-counter = 1, charge pump = 2.5 mA
   INT = 362, FRAC = 0, MOD = 4096 → VCO = 3620 MHz
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

## PLL configuration code (RP2040, C with pico-sdk)

```c
// Si5351 init: PLL_A locked to external 10 MHz, CLK0 sine 32 MHz
void coherence_init_si5351(i2c_inst_t *i2c) {
    si5351_init(i2c);
    si5351_set_clock_source(SI5351_CLK0, SI5351_PLL_A);

    // PLL_A: integer multiplier 32 → VCO 320 MHz from 10 MHz ref
    si5351_setup_pll(SI5351_PLL_A, 32, 0, 1);

    // MS0: integer divider 10 → 32 MHz output
    si5351_setup_multisynth(SI5351_CLK0, 10, 0, 1);

    // V0.2: sine output mode, 4 mA drive
    si5351_set_drive_strength(SI5351_CLK0, SI5351_DRIVE_4MA);
    si5351_set_output_waveform(SI5351_CLK0, SI5351_WAVE_SINE);

    si5351_clock_enable(SI5351_CLK0, true);
}

// ADF4351 init: 905 MHz output, +5 dBm drive
void coherence_init_adf4351(spi_inst_t *spi, uint cs_le) {
    // Standard 6-register initialization sequence
    // Reg 5: digital lock detect
    adf4351_write_reg(spi, cs_le, 0x00580005);
    // Reg 4: VCO div = 4, output enable, +5 dBm power
    adf4351_write_reg(spi, cs_le, 0x008C803C);
    // Reg 3: clock divider, default
    adf4351_write_reg(spi, cs_le, 0x000004B3);
    // Reg 2: R-counter = 1, charge pump 2.5 mA, low noise mode
    adf4351_write_reg(spi, cs_le, 0x18000FC2);
    // Reg 1: phase value, MOD = 4096
    adf4351_write_reg(spi, cs_le, 0x08008011);
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
