# Architecture overview

This document gives a guided tour of the chirpsounder transmitter architecture,
intended as the entry point for anyone reviewing the design.

## Design principles

Three principles drive the architecture:

1. **Coherence by construction.** A single external 10 MHz GPSDO reference enters
   the chain at one point and disciplines all derived frequencies (32 MHz for
   SX1262, 905 MHz for the mixer LO) via Si5351 and ADF4351 PLLs locked to that
   reference. Long-term stability is inherited from GPS at parts-per-billion level.

2. **Heterogeneous safety redundancy.** The PA receives 12 V only when four
   independent conditions hold simultaneously: software enable, manual kill switch,
   hardware watchdog timer, thermal comparator. Wired in series on the relay coil,
   they form a hardwired AND that no single common-cause failure can defeat.

3. **Modularity for testability.** Six functional cards, each individually testable
   with bench instruments before integration. Failures localize cleanly. Replacement
   modules (Si5351 breakout, ADF4351 module, QRP-Labs PA) are socketed for easy
   debug and substitution.

## Six-card partitioning

| Card | Function | Key components |
|------|----------|----------------|
| 1 — Power | 12 V / 12 V_clean / 5 V / 3.3 V distribution | LM7812, LM7805, AMS1117 |
| 2 — Coherence | 32 MHz + 905 MHz generation, GPSDO-locked | ADCMP562, Si5351, ADF4351 |
| 3 — RF-Low | Chirp generation, downconversion, IF filtering | SX1262, **ADE-R3+ (V0.2)**, BPF 30m |
| 4 — RF-High | Driver, PA, output filter, VSWR sense | ERA-3SM+, QRP-Labs 10W PA, LPF 30m |
| 5 — Control | RP2040 + OLED + encoder + USB host | Raspberry Pi Pico, SSD1306, CH376S |
| 6 — Safety | Hardwired AND chain protecting the PA | NE555, LM393, opto 4N35, DPDT relay |

Detailed card-level documents in [`docs/cards/`](../cards/).

## Block diagram

```
External GPSDO (10 MHz + PPS)
        |
        v
 +--------------------+
 |  Card 2 — Coherence|
 |  Squarer + PLLs    |
 |  → 32 MHz CMOS     |---32 MHz (sine mode, see V0.2 fix)
 |  → 905 MHz LO      |---905 MHz +5 dBm
 +--------------------+
                              |       |
                              v       v
                       +-----------------+
                       | Card 3 — RF-Low |
                       | SX1262 chirp    |
                       |   ↓             |
                       | TA0902A SAW (V0.2 added)
                       |   ↓             |
                       | ADE-R3+ mixer (V0.2 substitution)
                       |   ↓             |
                       | BPF 30m 5-pole  |
                       +-----------------+
                              |
                              v 10 MHz, 0 dBm
                       +-----------------+
                       | Card 4 — RF-High|
                       | ERA-3SM+ driver |
                       |   ↓ pad         |
                       | QRP-Labs 10W PA |
                       |   ↓             |
                       | Coupler (BN43-7051, V0.2 upsized)
                       |   ↓             |
                       | LPF 30m 7-pole  |
                       |   ↓             |
                       | ESD surge prot. (V0.2 added)
                       +-----------------+
                              |
                              v
                          Antenna 30m

 +-----------+     +-----------+     +----------------+
 | Card 5    |<--->| Card 6    |---->| 12V_PA relay   |
 | Control   | EN+ | Safety    |     | 4-input AND    |
 | RP2040    | WD  | 555+LM393 |     | wired chain    |
 +-----------+     +-----------+     +----------------+
```

## RF chain budget (V0.2 revised)

| Stage | Input | Gain/Loss | Output | Notes |
|-------|-------|-----------|--------|-------|
| SX1262 | — | — | +14 dBm | Set via SetTxParams |
| Pad −6 dB | +14 | −6 | +8 | π-pad |
| **TA0902A SAW (V0.2)** | +8 | −2 | +6 | New BPF on RF input |
| **ADE-R3+ mixer (V0.2)** | +6 | −7 | −1 | In-band conversion loss |
| BPF 30m IF | −1 | −2 | −3 | 5-pole Chebyshev |
| Inter-card link | −3 | −0.5 | −3.5 | SMA + coax |
| ERA-3SM+ driver | −3.5 | +18 | +14.5 | P1dB = +21 dBm, margin OK |
| Adjustable pad | +14.5 | −2 | +12.5 | Trim to PA optimum |
| **PA QRP-Labs** | +12.5 | +27.5 | **+40** | 10 W RMS |
| Coupler (V0.2 upsized) | +40 | −0.5 | +39.5 | BN43-7051 |
| LPF 30m | +39.5 | −1 | +38.5 | 7-pole Chebyshev |
| ESD surge prot. (V0.2) | +38.5 | −0.2 | +38.3 | PolyPhaser |
| Antenna feed | +38.3 | — | **+38.3 ≈ 6.8 W** | SO-239 |

Phase noise budget in [`simulations/phase-noise/`](../../simulations/phase-noise/),
filter synthesis in [`simulations/filters/`](../../simulations/filters/).

## What changed between V0.1 and V0.2

See [`docs/CHANGELOG.md`](../CHANGELOG.md) for the complete list of design
corrections following internal review. The major substitutions are:

1. ADE-1 → **ADE-R3+** (mixer in-band)
2. New **TA0902A** SAW on RF input
3. Si5351 CLK0 → **sine-output mode** (was CMOS rail-to-rail)
4. New 3-pole LPF on Si5351 output
5. Coupler core upsized to **BN43-7051**
6. New ESD coaxial surge protection
7. Thermal sensor moved closer to IRF510 die
8. PA ground isolation by ferrite bead
9. ADF4351 LO drive bumped to +8 dBm
10. RF chain budget fully recomputed

## Receiver architecture (V0.3)

This document covers the **transmitter**. Since V0.3 the receive side runs on
the wsprdaemon reference hardware (GPSDO + RX888 MkII + Beelink miniPC) with
ka9q-radio's `radiod` as channelizer; the sounder RX coexists with WSPR
decoding on the same box. Design principle 1 (coherence by construction)
extends to RX through the GPSDO-disciplined RX888 sample clock. Full details:
[`rx-ka9q.md`](rx-ka9q.md).

## Open questions

- **Two-stage conversion?** The IF/LO ratio of 1.1% with single-stage conversion
  remains marginal even with the SAW pre-filter. A two-stage scheme (915 MHz →
  70 MHz → 10 MHz) would relax this constraint at the cost of one more mixer and
  filter. Deferred to V1.0 pending bench data on V0.2.

- **PA upgrade path?** QRP-Labs 10W kit is well proven but limits us to that
  power class. For higher-power experiments (legal up to 150 W on 30m in France),
  an external linear amp (Hardrock-50, MX-P50M) could be inserted between the
  current PA and the LPF. Out of scope for V0.2 baseline.

- **TCXO fallback?** The whole architecture assumes an external GPSDO. For
  portable or backup operation, a TCXO + occasional GPSDO sync would suffice for
  short sessions. To investigate.
