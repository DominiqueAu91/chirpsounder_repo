# Card 1 — Power

> Multi-rail power distribution: 12 V_PA / 12 V_clean / 5 V / 3.3 V.

## Function

Receives external 12 V supply (barrel jack) and distributes four regulated rails:

- **12 V_PA** — direct, unregulated, routed through Card 6 safety relay to PA only. Peak 1.5 A in TX.
- **12 V_clean** — linear-regulated 12 V for ADF4351 module, ERA-3SM+ driver, VSWR bridge. ~250 mA.
- **5 V** — for SX1262 module, Si5351, OLED, USB host. ~400 mA.
- **3.3 V** — for RP2040 logic and pull-ups. ~150 mA.

## Schematic

```
DC IN 12V barrel ──[F1 polyfuse 3A]──[D1 1N5822]──┬──► 12V_PA bus (to Card 6 relay)
                                                  ├── [TVS SMBJ16CA]
                                                  ├── LED red "ON" + R 1k5
                                                  │
                                                  v
                                          [LM7812 + heatsink + 10µF + 100nF]
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
budget (< 1 A idle), thermal losses are acceptable (~1 W on LM7812 with clip-on
heatsink), and the absence of switching noise (typically 100 kHz to 2 MHz on
buck switchers) is precious for a card feeding sensitive PLLs downstream.

**Three-stage input protection.** Polyfuse for resettable overcurrent, TVS
bidirectional for transient surges, Schottky for reverse-polarity (a common
homebrew accident, 0.4 V drop acceptable here).

**Star ground under LM7812.** All daughter-card grounds converge at this point
via short wires (< 5 cm) or the backplane ground plane. This eliminates ground
loops that would degrade Card 2 phase noise performance.

## Verification

1. Apply 12 V to barrel jack. LED on. Verify 12 V_clean = 12.0 V ± 0.2 V at
   no load, then with 250 mA dummy load.
2. Verify 5 V = 5.0 V ± 0.05 V at 400 mA load.
3. Verify 3.3 V = 3.3 V ± 0.05 V at 150 mA load.
4. Reverse polarity test: apply −12 V briefly. No damage. Forward voltage
   recovery within 1 second when polarity restored.
5. Thermal: full load for 30 minutes. LM7812 heatsink reaches 55 °C max in
   still air at 22 °C ambient.

## BoM

See [`hardware/bom/card-01-power.csv`](../../hardware/bom/card-01-power.csv).
~€10 total.
