# Card 4 — RF-High

> Driver, power amplifier, output filtering, VSWR sensing, and ESD protection.
> The thermally and electromagnetically demanding card.

## Function

Card 4 takes the 0 dBm chirp at 10 MHz from Card 3 and amplifies it to 10 W RMS at
the antenna connector, with bidirectional power and VSWR monitoring, low-pass output
filtering for harmonic compliance, and (V0.2 addition) coaxial ESD surge protection.

## Schematic (V0.2)

```
SMA J1 input ◄── 10 MHz, 0 dBm from Card 3
        |
        v
   +-----------------+
   | ERA-3SM+ MMIC   |
   | gain +18 dB     |
   | RFC L1 = 1 µH   |
   | R_bias = 150 Ω  |
   +-----------------+
        |
        v +18 dBm
        |
   π pad −2 dB (V0.2: was −5 dB; reduced because ADE-R3+ gives less drive)
   R 11 Ω series, R 220 Ω shunts ×2
        |
        v +12.5 dBm (PA drive optimum)
        |
   +================================================+
   |                                                |
   |  PA QRP-Labs 10W HF Linear (~€55)              |
   |                                                |
   |  Driver: BS170 push-pull (~10 dB)              |
   |  Final:  IRF510 push-pull (~17 dB)             |
   |  Transformer T3: binocular 4:1                 |
   |                                                |
   |  Vcc 12V_PA  ◄── via Card 6 safety relay       |
   |  PTT_KEY     ◄── via 4N35 opto from RP2040     |
   |                                                |
   |  **[V0.2 CHANGE] PA Vcc return path through    |
   |   ferrite bead BLM41 to isolate PA ground      |
   |   from driver/sense ground (eliminates         |
   |   ground-bounce coupling at 1.5 A pulse load)** |
   |                                                |
   |  **[V0.2 CHANGE] NTC 10 kΩ moved from radiator |
   |   surface to immediate proximity of IRF510     |
   |   case (~2 cm). Threshold lowered 70 → 65 °C.**|
   |                                                |
   +================================================+
        |
        v +40 dBm = 10 W RMS
        |
   +-----------------------------------------------+
   | Bidirectional directional coupler             |
   |                                                |
   | **[V0.2 CHANGE] BN43-7051 binocular core      |
   |  (was BN43-2402, undersized at 10 W)**         |
   | 25 W rated, no flux saturation, no harmonic    |
   | distortion of forward/reverse readings.        |
   |                                                |
   | Coupling: −20 dB                              |
   | Detectors: 1N5711 Schottky × 2                |
   | RC filter: 1 kΩ + 100 nF                      |
   |                                                |
   | V_fwd → ADC0 RP2040 (GPIO26)                   |
   | V_rev → ADC1 RP2040 (GPIO27)                   |
   +-----------------------------------------------+
        |
        v +39.5 dBm
        |
   +-----------------------------------------------+
   | LPF 30m 7-pole Chebyshev passband             |
   | fc = 12 MHz, ripple 0.1 dB                    |
   |                                                |
   | L1=L7 = 0.65 µH (T50-6, 13 turns 0.8 mm)      |
   | L2=L6 = 1.07 µH (T50-6, 17 turns 0.8 mm)      |
   | L3=L4=L5 = 1.18 µH (T50-6, 18 turns 0.8 mm)   |
   | C1=C6 = 470 pF NP0 1 kV                       |
   | C2=C5 = 1000 pF NP0 1 kV                      |
   | C3=C4 = 1200 pF NP0 1 kV                      |
   |                                                |
   | Attenuation @ 20 MHz (PA H2): > 50 dB         |
   | Attenuation @ 30 MHz (PA H3): > 70 dB         |
   +-----------------------------------------------+
        |
        v +38.5 dBm
        |
   **[V0.2 ADDED] Coaxial ESD surge protector
    PolyPhaser IS-50UX-C0 or Alpha Delta TT3G50
    Mandatory for outdoor antenna installation,
    particularly in thunderstorm-prone areas
    (Lot, Dordogne, summer storms).**
        |
        v +38.3 dBm ≈ 6.8 W radiated
        |
   SO-239 panel connector → 30m antenna feedline
```

## V0.2 changes from V0.1

| Change | Reason | Cost |
|--------|--------|------|
| Coupler core BN43-2402 → **BN43-7051** | Original core saturated at 10 W, distorting fwd/rev readings via harmonic generation in the core itself. Larger core stays linear. | +€2 |
| **+ ESD surge protector on antenna port** | Mandatory for outdoor installations. Lightning-induced transients of several kV can destroy IRF510. The €40 PolyPhaser is cheap insurance vs PA replacement. | +€40 |
| **+ ferrite BLM41 on PA Vcc return** | Isolates PA ground bounce (1.5 A peak transients) from driver and sense grounds. Eliminates parasitic coupling that would modulate driver bias. | < €1 |
| NTC repositioned + threshold lowered | NTC on radiator surface had 15 s thermal lag, allowing IRF510 die to overshoot before NTC tripped. Closer placement + lower threshold (65 °C) gives meaningful protection. | €0 |
| Driver pad −5 dB → −2 dB | Compensates for lower drive level out of ADE-R3+ mixer (V0.2 mixer change). Net PA input still +12.5 dBm optimum. | €0 |

## ERA-3SM+ driver biasing

Standard MMIC bias network:

- Vcc supply: 12 V
- Internal voltage drop: ~3.5 V across the MMIC
- Target bias current: 60 mA
- Bias resistor: R_bias = (12 − 3.5) / 0.060 = 142 Ω → 150 Ω 1% 1/4 W
- RF choke: 1 µH (to keep RF out of the bias supply)
- Decoupling: 100 nF X7R + 10 µF tantalum, close to RFC

Datasheet: [Mini-Circuits ERA-3SM+](https://www.minicircuits.com/pdfs/ERA-3SM+.pdf).

## QRP-Labs PA — operational notes

- Source: <https://shop.qrp-labs.com/linear>
- Topology: BS170 push-pull driver + IRF510 push-pull final
- Linearity: IMD3 < −30 dBc at 10 W on 14 MHz (manufacturer claim, independently
  verified by GI0GDP)
- Duty cycle: 100% rated for 1 hour continuous at 10 W with included heatsink
- Vcc range: 12 V to 13.8 V
- Peak current: 1.5 A in TX
- VSWR tolerance: handles open, short, and 20 ft of open coax without damage

The PA kit ships with all components, magnet wire, and the heatsink. Build time
typically 4-6 hours for an experienced builder, 8-10 for a beginner. **The kit
does not include an output low-pass filter**; the filter is part of our Card 4
design.

## VSWR coupler calibration

Calibration is required once at commissioning, then repeated annually due to
Schottky aging and temperature drift.

Procedure:

1. Insert a known-good 50 Ω dummy load between LPF output and antenna connector.
2. Connect a calibrated wattmeter (Bird 43 with 25H slug, or MFJ-841) inline
   between coupler output and dummy load.
3. Transmit at 1 W, record V_fwd from ADC0. Repeat at 2, 5, 10 W. Build a
   piecewise-linear table mapping V_fwd to actual power.
4. Store table in RP2040 flash via USB-CDC `cal save fwd` command.
5. For V_rev: deliberately mismatched load (calibrated VSWR stubs at 2:1, 3:1,
   5:1) and repeat. Store reverse calibration.
6. Annual verification: recheck at 5 W only, confirm reading within ±0.5 dB
   of stored table. If drift exceeds ±1 dB, recalibrate fully.

Reference: <https://www.qsl.net/wb6bld/swrtut.htm> for theoretical background
on directional coupler bridge design.

## ESD surge protector (V0.2 addition)

Two acceptable options:

- **PolyPhaser IS-50UX-C0**: gas discharge tube (GDT) based, 90 V trigger,
  designed for HF up to 6 GHz. Surface-mount enclosure with N-female on both
  sides. Replace adapters as needed. ~€40.
- **Alpha Delta TT3G50**: dual-stage, 230 V GDT + capacitor filtering. SO-239
  pass-through. ~€55.

Mounting: between SO-239 panel connector and the external antenna feedline,
ideally with the protector grounded to the equipment chassis AND to a separate
station ground rod. The dual-grounding requirement is documented in 
[`docs/operating/grounding.md`](../operating/grounding.md).

**Note on insurance:** The IS-50UX-C0 documentation explicitly states the device
will NOT survive direct lightning strikes — it protects against induced
transients only. For genuinely lightning-exposed antennas, an external mast
disconnect (manual or automatic relay) remains the only complete protection.

## Layout notes

- **Star grounding** at the PA negative return point. Driver and sense circuits
  reference this point only via the BLM41 ferrite isolation.
- **Heatsink with thermal interface material** between IRF510 and radiator
  (Bergquist Sil-Pad or equivalent, NOT just dry contact).
- **NTC placement**: solder NTC leads to PCB pads located within 2 cm of IRF510
  body, then bend NTC body to physical contact with IRF510 case via thermally
  conductive epoxy (Arctic Alumina or similar).
- **Inter-stage shielding**: vertical metal partition between driver section and
  PA section to prevent feedback oscillation. The QRP-Labs kit doesn't ship with
  this; we add a piece of brass shim soldered to ground islands.
- **High-current return**: 12 V_PA return trace at least 3 mm wide (or via grid)
  to handle 1.5 A pulses without IR drop affecting reference voltages.

## Verification procedure

1. **No-RF DC checks.** Power up with PA disabled (relay open). Verify driver
   bias current = 60 mA ± 10%. NTC reads ambient temperature.

2. **Driver chain alone.** Inject 0 dBm at J1, PA still disabled. Probe at PA
   input connector: expect +12.5 dBm ± 0.5 dB at 10 MHz, clean tone.

3. **Full TX into dummy load.** 50 Ω dummy load connected. Enable PA. Inject
   0 dBm at J1. Measure with wattmeter: 10 W ± 1 W at 10 MHz. Spectrum analyzer
   on coupler tap: H2 < −50 dBc, H3 < −60 dBc post-LPF.

4. **VSWR sense calibration.** Run procedure above.

5. **Thermal cycling.** Continuous TX into dummy load for 1 hour at 10 W.
   Monitor T_NTC via USB-CDC: should stabilize around 50-55 °C with included
   heatsink in still air. Verify thermal shutdown triggers at 65 °C by
   blocking radiator airflow.

6. **VSWR fault.** Replace dummy load with deliberately mismatched stub
   (3:1 VSWR). Verify firmware shuts down PA within 100 ms via VSWR trip.

## Bill of materials (Card 4 only, V0.2)

See [`hardware/bom/card-04-rf-high.csv`](../../hardware/bom/card-04-rf-high.csv).
Total ~€143, up from €100 in V0.1 due to BN43-7051, BLM41, and ESD protector.
