# Card 3 — RF-Low

> SX1262 chirp source, frequency conversion to 30m, IF bandpass filtering.
> Most modified card between V0.1 and V0.2.

## Function

The card produces a coherent LFM chirp at the SX1262 native frequency (~915 MHz),
then converts it down to 10 MHz on the 30m amateur band by mixing with a coherent
905 MHz LO from Card 2. An IF bandpass filter rejects mixing products and leakage.

## Schematic (V0.2)

```
32 MHz sine (Card 2, sine-mode Si5351)
    |
   [resistive divider 1k/100Ω, V0.2 added]
    |
   [C 1nF NP0 coupling]
    |
    o XTA pin SX1262 module (E22-900M30S)
      XTB floating
      DIO3 not used (no internal TCXO)

+5 V → SX1262 module Vcc, decoupling 10 µF tant + 100 nF X7R

RP2040 SPI:
  MOSI ────────────► SX1262 MOSI
  MISO ◄──────────── SX1262 MISO
  SCK  ────────────► SX1262 SCK
  NSS  ────────────► SX1262 NSS
  BUSY ◄──────────── SX1262 BUSY
  NRST ────────────► SX1262 NRST
  DIO1 ◄──────────── SX1262 DIO1 (IRQ)

SX1262 ANT pin:
  +14 dBm @ ~915 MHz, continuous LFM chirp (SetTxContinuousPreamble, opcode 0xD2)
    |
    v
  π pad −6 dB (R 18 Ω series, R 150 Ω shunts ×2)
    |
    v +8 dBm @ 915 MHz
    |
**[V0.2 ADDED] TriQuint TA0902A SAW filter, 902–928 MHz, IL ~2 dB**
    |
    v +6 dBm
    |
+----------------+
| ADE-R3+ mixer  |   **[V0.2 SUBSTITUTED, was ADE-1]**
| 1–3000 MHz     |   Mini-Circuits, level 7 mixer
|                |
| pin 1 RF in ◄──── +6 dBm @ 915 MHz (post-SAW)
|                |
| pin 8 LO in ◄──── +7 dBm @ 905 MHz (from Card 2, V0.2 raised drive level)
|                |
| pin 3,4 IF out ─► 10 MHz @ −1 dBm (and 1820 MHz sum, suppressed by IF BPF)
+----------------+
    |
    v
+--------------------------------------------+
| BPF 30m 5-pole Chebyshev 0.1 dB ripple    |
| fc = 10.120 MHz, BW −3 dB = 500 kHz       |
|                                            |
| Topology: shunt-LC resonators              |
| capacitively coupled                       |
|                                            |
| L1..L5 = 2.2 µH, T50-6 yellow, 24 turns    |
| C1..C5 = 100 pF NP0 + 5–30 pF trimmer      |
| Cc_io = 22 pF, Cc_inner = 4.7 / 3.3 pF    |
+--------------------------------------------+
    |
    v 0 dBm @ 10 MHz, 500 kHz usable BW, IL = 2 dB
    |
    o J3 SMA panel → coax → Card 4
```

## V0.2 changes from V0.1

| Change | Reason | Cost impact |
|--------|--------|-------------|
| ADE-1 → **ADE-R3+** | ADE-1 was used at 915 MHz, outside its 500 MHz spec. Conversion loss exceeded 10 dB and isolation collapsed. ADE-R3+ rated 1–3000 MHz, in-band performance restored. | +€4 |
| **+ TA0902A SAW BPF on RF input** | V0.1 routed unfiltered SX1262 output to mixer. SX1262 harmonics polluted mixer ports. SAW filter eliminates everything outside 902–928 MHz. | +€5 |
| **+ resistive divider on XTA input** | V0.1 directly coupled CMOS rail-to-rail signal to XTA. Combined with sine-mode Si5351 (Card 2), the divider brings amplitude down to ~330 mVpp, within SX1262 datasheet specs. | < €0.10 |
| LO drive raised to +7 dBm | ADE-R3+ wants +7 dBm on LO for nominal performance. ADF4351 register reconfigured + reduced pad. | €0 |

## SX1262 register configuration

Initial sequence at boot, sent over SPI by RP2040:

```c
// Standby
sx1262_cmd(0x80, {0x00});  // SetStandby(STDBY_RC)

// Packet type
sx1262_cmd(0x8A, {0x01});  // SetPacketType(LORA)

// Frequency
// f = 915 MHz, regs = floor(f * 2^32 / 32e6) = 0xE4400000
sx1262_cmd(0x86, {0xE4, 0x40, 0x00, 0x00});  // SetRfFrequency

// Image calibration
sx1262_cmd(0x98, {0xE1, 0xE9});  // CalibrateImage 902-928 MHz

// Modulation: SF12, BW = 7.8125 kHz, CR = 1, LDRO on
sx1262_cmd(0x8B, {0x0C, 0x00, 0x01, 0x01});

// Output power: target +14 dBm at chip output
// power = -3 (registered), ramp = 200 µs
sx1262_cmd(0x8E, {0xFD, 0x04});  // SetTxParams

// Start coherent chirp
sx1262_cmd(0xD2, {});  // SetTxContinuousPreamble
```

To stop: `sx1262_cmd(0x80, {0x00})` returns to standby.

## ADE-R3+ details

- Frequency range: 1–3000 MHz (vs 0.5–500 MHz for ADE-1)
- Conversion loss in band: 7.5 dB typical at 1 GHz
- LO-RF isolation: 35 dB typical
- LO-IF isolation: 25 dB typical
- IP3 input: +21 dBm
- Package: surface-mount QFN, 6×4 mm
- Datasheet: [Mini-Circuits ADE-R3+](https://www.minicircuits.com/pdfs/ADE-R3+.pdf)

## TA0902A SAW filter

- Center: 915 MHz
- Bandwidth: 26 MHz (902–928 MHz)
- Insertion loss: 2.4 dB typ
- Out-of-band rejection: > 35 dB at fc ± 50 MHz
- Package: SMD ceramic, 5×5 mm
- Note: alternative filters acceptable (TA0989A, B3741, B3744) — any 902–928 MHz
  amateur ISM SAW with IL < 3 dB will work.

## BPF 30m design

The 5-pole Chebyshev bandpass filter is unchanged from V0.1. Component values from
the original Cohn synthesis (capacitively-coupled parallel resonators):

| Component | Value | Realization |
|-----------|-------|-------------|
| L1..L5 | 2.2 µH | T50-6 yellow toroid, 24 turns 0.5 mm enameled wire |
| C1..C5 | 100 pF NP0 + 5–30 pF trimmer | 1206 SMD + Sprague-Goodman trimmer |
| Cc_io (input/output) | 22 pF NP0 1206 | tolerance ±2% |
| Cc_12, Cc_45 | 4.7 pF NP0 1206 | tolerance ±0.25 pF |
| Cc_23, Cc_34 | 3.3 pF NP0 1206 | tolerance ±0.25 pF |

**Note:** these values are theoretical from synthesis. Bench measurement on the
prototype will likely require adjustment. The trimmers on the resonators allow
±10% trimming of each resonance frequency for VNA-guided alignment.

Detailed synthesis and SPICE simulation in
[`simulations/filters/bpf-30m-5pole.md`](../../simulations/filters/bpf-30m-5pole.md).

## Layout notes

- ADE-R3+ pin 8 (LO) is sensitive to ground-loop noise. Keep LO trace short
  (< 30 mm) and direct from Card 2 inter-card connector.
- TA0902A SAW filter requires good 50 Ω matching on input and output ports.
  Recommend microstrip width calculator (KiCad's "Track Width" tool) for 1.6 mm
  FR4: trace width 2.8 mm.
- BPF toroids spaced ≥ 2× their diameter, axes perpendicular between neighbors,
  to suppress parasitic magnetic coupling that would skew the response.
- Test points: TP4 at SX1262 ANT pin (before pad), TP5 at BPF output (before
  inter-card cable). Both as SMA edge-mount on PCB for easy spectrum analyzer
  hookup during bench validation.

## Verification procedure

After assembly, verify in this order:

1. **DC checks.** 5 V rail clean, no excessive current draw, SX1262 module
   responsive on SPI (check version register).

2. **Standalone SX1262 chirp.** With LO disabled (CE pin of ADF4351 low) and PA
   inhibited (PA_ENABLE GPIO low), command SX1262 to start chirping. Probe TP4
   on spectrum analyzer: expect clean chirp around 915 MHz, +14 dBm ±1 dB,
   linear sweep over BW = 7.8 kHz at SF12.

3. **LO injection.** Enable ADF4351, verify LO at +7 dBm at mixer LO port (use
   SMA tee with 50 Ω terminator if needed for non-disruptive measurement).

4. **Mixed output before BPF.** Probe at mixer IF output: expect 10 MHz tone
   plus 1820 MHz tone (sum), and possible LO/RF leakage. Power level around
   −1 dBm at 10 MHz.

5. **Final IF output after BPF.** Probe at TP5: expect clean 10 MHz chirp at
   0 dBm, ±1 dB, with 500 kHz usable bandwidth, all out-of-band products
   below −40 dBc.

6. **VNA alignment of BPF.** With NanoVNA, sweep S21 over 8–12 MHz, trim
   each resonator's trimmer to flatten passband to < 0.5 dB ripple, verify
   stop-band attenuation > 40 dB at 9.0 and 11.0 MHz.

If steps 1–5 pass and step 6 produces a clean response, the card is ready for
integration. Total bench time, first build: 4–6 hours typical.

## Bill of materials (Card 3 only, V0.2)

See [`hardware/bom/card-03-rf-low.csv`](../../hardware/bom/card-03-rf-low.csv).
Total ~€55, up from €46 in V0.1 due to mixer substitution and SAW filter addition.
