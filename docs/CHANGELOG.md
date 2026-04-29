# Changelog

All notable design changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [V0.2] — 2026-04 — Design review #1

### Major design corrections following V0.1 internal review

V0.1 was a conceptual document with several quantitative and structural flaws.
This V0.2 addresses ten identified issues. Every change below is traceable to a
specific flaw in V0.1.

#### Critical (blocking) corrections

- **Mixer substitution.** The ADE-1 specified in V0.1 is rated 0.5–500 MHz and was
  used at RF=915 MHz, well outside specs. Replaced with **ADE-R3+** (1–3000 MHz,
  Mini-Circuits, ~€12). Conversion loss now within manufacturer specifications.
  See [`docs/cards/03-rf-low.md`](cards/03-rf-low.md).

- **LO drive level.** ADE-R3+ requires +7 dBm at the LO port for nominal performance.
  V0.1 delivered +3 dBm (ADF4351 +5 dBm minus 2 dB pad). Two changes applied:
  ADF4351 drive bumped to +8 dBm via register configuration, pad reduced to −1 dB.
  Result: +7 dBm at the LO port, mixer in nominal regime.

- **IF/LO frequency separation.** V0.1 had IF=10 MHz, LO=905 MHz, ratio 1.1%, too
  close to the LO for clean separation through the mixer. **Resolution accepted as
  known limitation** in V0.2 — output BPF on IF side handles residual leakage; full
  redesign with two-stage conversion deferred to V1.0.

- **RF input pre-filter added.** V0.1 had no bandpass filter between SX1262 output
  and mixer RF port, letting harmonics into the mixer. Added a commercial 902–928 MHz
  SAW filter (TriQuint TA0902A, ~€5) at the mixer RF input. Mixer now sees only the
  fundamental.

- **SX1262 XTA driving.** V0.1 had Si5351 CMOS rail-to-rail signal directly coupling
  to the SX1262 XTA pin via a 1 nF capacitor. SX1262 expects sine-like input at a
  few hundred mVpp. **Resolution:** Si5351 CLK0 reconfigured to sine-output mode
  (register `CLKx_DRV` reduced + spread-spectrum disabled), and a resistive divider
  (1 kΩ / 100 Ω) added before the coupling capacitor for amplitude conditioning.

#### Important (performance) corrections

- **Si5351 output low-pass filtering.** Added a 3-pole Chebyshev LPF (fc = 40 MHz,
  L = 470 nH, C = 100 pF) on Si5351 CLK0 before XTA coupling, to suppress odd
  harmonics that would otherwise radiate from the trace.

- **PA ground separation.** PA Vcc return rerouted with a ferrite bead (BLM41) to
  isolate from driver and sense ground. Removes ground-bounce coupling that would
  modulate driver bias and pollute VSWR ADC readings during TX peaks (1.5 A).

- **Directional coupler core upsizing.** BN43-2402 binocular core replaced with
  **BN43-7051** (larger cross-section), keeping flux well below saturation at 10 W.
  Eliminates harmonic distortion in the coupler that would corrupt fwd/rev readings.

#### Reliability corrections

- **Thermal sensor placement.** NTC 10 kΩ moved from radiator surface (slow thermal
  response, ~15 s lag) to immediate proximity of IRF510 transistor case. Threshold
  also lowered from 70 °C to 65 °C as a further safety margin.

- **ESD protection on antenna port.** Coaxial gas discharge surge protector added
  between SO-239 panel connector and antenna feedline (PolyPhaser IS-50UX-C0 or
  Alpha Delta TT3G50, ~€40). Mandatory for outdoor installation, particularly in
  thunderstorm-prone areas (Lot region in summer).

### BoM impact

Net BoM change V0.1 → V0.2: approximately **+€55** (TA0902A SAW, ADE-R3+ delta,
LPF components, BN43-7051, BLM41 ferrite, surge protector). Total BoM revised from
€330 to **~€385** excluding GPSDO.

### Documentation impact

Card-level documents in [`docs/cards/`](cards/) updated to reflect substitutions and
new components. RF chain budget in [`docs/architecture/rf-budget.md`](architecture/rf-budget.md)
fully recomputed. Phase noise budget in [`simulations/phase-noise/`](../simulations/phase-noise/)
re-evaluated with corrected component datasheets.

---

## [V0.1] — 2026-04 — Initial design document

Initial conceptual document. Six-card architecture, BoM ~€330. PDF deliverable shared
internally for review. Contains the 10 flaws now documented and corrected in V0.2.

Archived in [`docs/archive/V0.1-design-document.pdf`](archive/) for traceability.
