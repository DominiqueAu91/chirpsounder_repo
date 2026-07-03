# Card 1 — Power

> Multi-rail power distribution: 12 V_PA / 12 V_clean / 5 V / 3.3 V.

## Function

Receives the external supply (barrel jack, **13.8 V nominal — V0.4 change,
see below**) and distributes four rails:

- **12 V_PA** — direct, unregulated, routed through Card 6 safety relay to PA only. Peak 1.5 A in TX.
- **12 V_clean** — linear-regulated 12 V for ADF4351 module, ERA-3SM+ driver, VSWR bridge. ~250 mA.
- **5 V** — for SX1262 module, Si5351, OLED, USB host. ~400 mA.
- **3.3 V** — for RP2040 logic and pull-ups. ~150 mA.

## Schematic

```text
DC IN 13.8V barrel ─[F1 polyfuse 3A]──[D1 1N5822]──┬──► 12V_PA bus (13.4 V, to Card 6 relay)
                                                  ├── [TVS SMBJ16CA]
                                                  ├── LED red "ON" + R 1k5
                                                  │
                                                  v
                                          [LM2940-12 LDO + heatsink + 22µF + 100nF]
                                          **[V0.4: was LM7812 — see below]**
                                                  │
                                                  ├──► 12V_clean (ADF4351, ERA-3SM+, sense)
                                                  v
                                          [LM7805 + heatsink + 10µF + 100nF]
                                                  │
                                                  ├──► 5V (SX1262, Si5351, OLED, USB host)
                                                  v
                                          [AMS1117-3.3 + 4.7µF + 100nF]
                                                  │
                                                  └──► 3.3V (RP2040 backup, I/O pull-ups)
```

## Design choices

**Linear regulation cascade.** No switching converters — for a modest current
budget (< 1 A idle), thermal losses are acceptable (~0.5 W on the LM2940 with
clip-on heatsink at 13.8 V in), and the absence of switching noise (typically
100 kHz to 2 MHz on buck switchers) is precious for a card feeding sensitive
PLLs downstream.

**[V0.4 FIX] Input voltage and 12 V regulator.** The V0.2 design fed an LM7812
from a 12 V input: after the 0.4 V Schottky drop, 11.6 V reaches a regulator
that needs ≈ 14 V (2–2.5 V dropout). "12V_clean" was in reality an unregulated
~9.5 V rail tracking the supply — silently degrading the ERA-3SM+ bias
((12 − 3.5)/150 Ω = 57 mA design → ~40 mA actual, with gain and P1dB loss).
Two coordinated changes fix it:

1. **External supply specified as 13.8 V nominal** — the standard shack PSU.
   Side benefit: the IRF510 PA runs with healthier headroom at 13.4 V than
   at 11.6 V for the 10 W target.
2. **LM7812 → LM2940-12** (low-dropout, < 0.5 V at 1 A): 13.4 V in, true
   12.0 V out with margin. The ERA-3SM+ bias network is then correct as
   designed (150 Ω → 57 mA). LDO stability note: the LM2940 requires
   ≥ 22 µF output capacitance with ESR in the 0.1–1 Ω window — a tantalum
   or aluminum electrolytic, NOT a low-ESR ceramic alone.

Verify also the ADF4351 module's supply input: most Chinese modules carry
onboard 3.3 V regulators and accept 5 V — if so, move it to the 5 V rail and
the 12V_clean load drops to the ERA-3SM+ and sense bridge only.

**Three-stage input protection.** Polyfuse for resettable overcurrent, TVS
bidirectional for transient surges, Schottky for reverse-polarity (a common
homebrew accident, 0.4 V drop acceptable here).

**Star ground under LM7812.** All daughter-card grounds converge at this point
via short wires (< 5 cm) or the backplane ground plane. This eliminates ground
loops that would degrade Card 2 phase noise performance.

## Verification

1. Apply 13.8 V to barrel jack. LED on. Verify 12 V_clean = 12.0 V ± 0.2 V at
   no load, then with 250 mA dummy load. Then lower the supply to 13.0 V and
   verify regulation holds (LDO margin check — the V0.2 design failed here).
2. Verify 5 V = 5.0 V ± 0.05 V at 400 mA load.
3. Verify 3.3 V = 3.3 V ± 0.05 V at 150 mA load.
4. Reverse polarity test: apply −12 V briefly. No damage. Forward voltage
   recovery within 1 second when polarity restored.
5. Thermal: full load for 30 minutes. LM7812 heatsink reaches 55 °C max in
   still air at 22 °C ambient.

## BoM

See [`hardware/bom/card-01-power.csv`](../../hardware/bom/card-01-power.csv).
~€10 total.
