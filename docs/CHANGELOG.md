# Changelog

All notable design changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [V0.4 — unreleased] — TX design review fixes

Receiver-side V0.3 review extended to the transmitter and applicative parts.
Full findings with severity ranking: [`docs/reviews/tx-review-v0.4-input.md`](reviews/tx-review-v0.4-input.md).

### Blockers fixed (design did not work as documented)

- **Card 2**: Si5351A → Si5351C-B (A variant has no CLKIN, cannot lock to
  the GPSDO); PLL ×32/÷10 → ×64/÷20 (V0.2 VCO at 320 MHz was outside the
  600–900 MHz range); nonexistent "sine output mode" removed (CMOS + LPF
  achieves the intent); XTA drive raised to ≈ 1 Vpp (0.6–1.2 Vpp window).
- **Card 3**: E22-900M30S → Waveshare Core1262 with xtal removed — the M30S
  hides XTA (coherence injection impossible) and embeds a +30 dBm PA/TCXO;
  SX1262 init corrected (`SetRfFrequency` = 0x39300000; `SetPaConfig` added;
  power byte +22 with scaled PA for +14 dBm).
- **Card 1**: input specified 13.8 V nominal; LM7812 → LM2940-12 LDO (the
  7812 cannot regulate from a 12 V input; "12V_clean" was ~9.5 V unregulated).
- **Card 6**: AND chain now gates a 2N7000 driving the relay coil (V0.2
  routed coil current through a 4N35 and an LM393 OC, beyond both ratings).
- **ADF4351**: register set regenerated and field-verified (V0.2 R4 encoded
  RF divider ÷1 → 3620 MHz out; R2 encoded R-counter = 0, invalid).
- **Firmware**: FAULT state made recoverable; CW identification completes
  before dwell (completion handshake); 10-minute re-identification
  implemented; PA_ENABLE dropped in software on fault.

### Majors

- Mixer level plan: RF pad −6 → −15 dB (RF port at LO − 10 dB); new 10 MHz
  post-BPF gain stage restores 0 dBm at the card output.
- ADC front-end: 2:1 divider + BAT54S clamps on V_fwd/V_rev (detector DC
  sat at RP2040 full scale with zero margin).
- Card 6: + hardware VSWR trip (spare LM393 half); + CD4060 TX-time limiter
  (~10.4 min backstop) making the regulatory "hardwired limit" claim true;
  `regulatory.md` corrected accordingly.
- Phase-noise budget rewritten with correct multiplication/correlation
  treatment: total ≈ −82 dBc/Hz at 1 kHz dominated by the Si5351→SX1262
  path (V0.2's −95 was optimistic); SF12 conclusion survives with reduced
  margin; the shared-reference cancellation (worth ≈ 39 dB) is now claimed.

### Additions

- `tests/integration-zero-baseline.md` — pre-air validation procedure:
  compression gain, measured L(f), pulse-to-pulse phase continuity (gates
  the TID mode), absolute frequency accuracy, thermal soak.
- `docs/reviews/tx-review-v0.4-input.md` — the full review, including open
  V1.0 forks (direct-GPSDO 32 MHz vs DDS architecture) deliberately left
  as design decisions.

### Housekeeping

- Root-level debris removed (`rx-ka9q.md`, `CHANGELOG.md`, `v0.2-to-v0.3.diff`
  — copy-accident leftovers duplicating `docs/` content).
- `.markdownlint.yaml`: MD060 disabled (the fix from the CI session was
  never pushed; folded in here).
- BoM deltas: Card 2 +€2 (Si5351C), Card 3 −€4.50 net (Core1262 cheaper than
  M30S, + IF gain stage).

---

## [V0.3] — 2026-07 — Receiver platform migration to ka9q-radio

### Scope

V0.3 is a **receiver-side** revision only. The transmitter design (six-card
architecture, RF budget) is unchanged from V0.2. The direct-SDR receiver
options of V0.2 (ANTSDR E200, Hermes-Lite 2, RTL-SDR + upconverter) are
replaced as reference platform by the **wsprdaemon architecture**: GPSDO +
RX888 MkII + Beelink miniPC (Ubuntu Server 24.04 LTS) running
**ka9q-radio** (`radiod`).

Rationale, theory and implementation details:
[`docs/architecture/rx-ka9q.md`](architecture/rx-ka9q.md).

### Architectural changes

- **Capture model changed.** Behind `radiod` the raw 64.8 Msps stream is not
  exposed; instead of wideband capture + offline dechirp, the receiver uses a
  **stepped-LO tracking channel** (96 kHz IQ retuned by 48 kHz every 0.48 s
  at 100 kHz/s) for opportunity sweepers, and a **single fixed channel** for
  the project's own 30 m SX1262 sounder. Per-dwell stretch processing is
  mathematically validated by `software/ka9q-backend/test_dechirp_sim.py`
  (two-path synthetic ionosphere; delays recovered to within one FFT bin,
  16.7 µs at the default 0.12 s window).
- **Frequency vs time-of-day discipline made explicit.** The GPSDO
  disciplines the RX888 sample clock only. Absolute group delay requires
  host time discipline: gpsd + chrony on the GPSDO 1PPS, plus a one-time
  `--tau-bias` calibration absorbing radiod pipeline latency (1 ms of clock
  error = 300 km of one-way virtual range).

### Additions

- `software/ka9q-backend/` — radiod configuration, `chirp_tracker.py`
  (sweep tracking via the ka9q-radio `tune` utility + `pcmrecord` ingest),
  `dechirp_sweep.py` (segments → ionogram), `test_dechirp_sim.py`.
- `software/gr-chirpsounder/python/ka9q_iq_source.py` — first implemented
  block of the OOT module: native RTP multicast source (f32le/s16le/s16be
  payloads, SSRC filtering, zero-fill on sequence gaps). Replaces the
  planned ANTSDR/Hermes/RTL-SDR source flowgraphs.
- `docs/architecture/rx-ka9q.md` — receiver architecture document.

### Implementation notes traceable to ka9q-radio sources (2026-07)

- radiod creates channels **dynamically** on a `tune` command for an unknown
  SSRC; static config sections force SSRC = freq/kHz — hence no static chirp
  section in `radiod@chirp.conf`.
- Default channel encoding is `s16be`; V0.3 pins `f32le` end to end.
- The `iq` preset defaults to ±5 kHz filter edges; the tracker overrides to
  ±46 kHz, otherwise 90 % of the channel bandwidth is silently discarded.

### Housekeeping

- `software/examples/dechirp_basic.py` reformatted with black — the V0.2
  file did not pass the repository's own `python-lint` CI job. All V0.3
  Python files pass `black --check` and `ruff check`.
- `markdown-lint` CI job made green for the first time (V0.2 carried 72
  violations). Added `.markdownlint.yaml` codifying the project style
  (100-column prose, tables and code blocks exempt, Keep-a-Changelog
  sibling headings allowed); tagged all 20 fenced code blocks with a
  language (`text`/`sh`); fixed fence spacing in `budget.md` and
  `lfm-theory.md` and one trailing space.
- GitHub Actions bumped to Node 24-native majors (`checkout@v6`,
  `setup-python@v6`, `markdownlint-cli2-action@v23`), clearing the
  Node 20 deprecation warnings.

### BoM impact

Receiver BoM for stations already running wsprdaemon: **€0** (the same
RX888/miniPC serves both). For new stations, the wsprdaemon hardware kit
(per HamSCI sourcing guide) replaces the ANTSDR E200 line item. TX BoM
unchanged (~€385 excluding GPSDO).

---

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
