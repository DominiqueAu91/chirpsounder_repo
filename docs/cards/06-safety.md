# Card 6 — Safety

> Hardwired AND chain protecting PA Vcc. **Six** (V0.4, was four) independent
> conditions must hold simultaneously for the relay to close.

## Function

Heterogeneous redundancy: each protection detects a different failure class
using a different technology, so no single common-cause failure can defeat
multiple protections at once.

## Schematic

```text
Card 5 GP15 PA_ENABLE (software logic)
    │
    v
[4N35 opto, R_in 220 Ω, 5 kV galvanic isolation]
    │ open-collector output
    v
[Soft EN] → [Kill SW] → [WD 555] → [Thermal LM393A] → [VSWR LM393B] → [TX-limit 4060]
contact     manual NC    monost.    comparator          comparator      counter/timer
closed      latching     retrig.    NTC < 65 °C          V_rev < trip    Q14 low < ~10 min
when EN OK  type ALPS    1.7 s      open-collector       (V0.4 NEW)      (V0.4 NEW)
                                                                │
                                                                v
   **[V0.4 CHANGE] The series AND chain is now LOGIC ONLY: it pulls the gate
   of Q1 (2N7000, gate pull-down 10 kΩ) which switches the relay coil
   low-side. The V0.2 drawing routed the coil current (30–80 mA) through the
   4N35 output (50 mA abs max) and the LM393 open collector (~20 mA sink) —
   neither device can hold a relay coil reliably. One transistor restores
   electrical sanity; the AND philosophy is untouched.**
                                                                │
                                                                v
                                            Q1 2N7000 ──► [12 V relay coil]
                                                           flyback 1N4007

Relay NO contact:
12V_in ────o   o────► 12V_PA → Card 4 PA Vcc

VSWR comparator (V0.4 — uses the second, previously unused half of the LM393):
  V_rev (from Card 4 coupler, post-divider) → LM393B +IN
  Threshold ≈ 0.65 V post-divider (≈ 3:1 VSWR at 10 W forward: 2.5 W
  reflected → +14 dBm at the −20 dB tap → ≈ 1.3 V detector DC → ÷2)
  Set by trimmer, calibrate during the Card 4 VSWR procedure.
  Small RC (10 kΩ + 100 nF ≈ 1 ms) at the input rides through relay bounce.
  Fast, hardwired, independent of the 50 ms firmware loop. Cost: 3 R + 1 C.

TX-time limiter (V0.4 — makes the regulatory 10-minute claim true in hardware):
  CD4060 ripple counter, internal RC oscillator Rt = 330 kΩ, Ct = 100 nF film
  → f ≈ 13.2 Hz → Q14 goes high after 2^13 cycles ≈ 622 s ≈ 10.4 min
  (RC ±20 % → 8.3–12.4 min: a BACKSTOP above the firmware dwell logic,
  which remains the precise limit).
  Reset pin driven by inverted PTT: counter held at zero whenever PTT is
  released — any pause restarts the budget.
  Q14 high → (a) opens its element of the AND chain, (b) self-latches via a
  diode to the oscillator-inhibit input until PTT release resets it.
  Cost ≈ €1.

Watchdog 555 monostable retriggerable:
  R_t = 33 kΩ, C_t = 47 µF tantalum
  T = 1.1 × R × C ≈ 1.7 s
  Trigger: rising edge through C_diff 10 nF + R 1 kΩ
  Source: Card 5 GP_WD pulse 1 ms every 100 ms

Thermal comparator LM393:
  NTC 10 kΩ β = 3950 on radiator near IRF510 (V0.2: closer to die)
  Threshold V_seuil = 1.65 V (Vcc/2 tuned for 65 °C, V0.2: was 70 °C)
  Output open-collector, pull-up 10 kΩ to +12 V via opto
  Hysteresis: intrinsic LM393 + R 1 MΩ feedback

Kill switch:
  Push-button latching SPST 16 mm red ALPS panel mount
  Physically breaks ground of AND chain
  LED red on switch output (lit when kill engaged)

Panel indicators:
  LED green   "PA armed"      — relay coil energized
  LED red     "PA fault"      — LM393 trip OR software flag
  LED orange  "WD warning"    — 555 inverse output
  LED blue    "Kill engaged"  — kill switch state
```

## Why six diverse protections (V0.4)

| Protection | Failure class | Technology | Independence |
|------------|---------------|------------|--------------|
| Software (PA_EN) | Logic errors, misconfiguration | RP2040 GPIO | Programmed logic |
| Kill switch | Human intervention, neighbor complaint, emergency | Mechanical contact | 100% software-independent |
| Watchdog 555 | Firmware crash, deadlock, blocked IRQ | Analog RC timer | Detects software failures |
| Thermal LM393A | Fan failure, PA aging, slow overload | Analog comparator | Detects physical failures |
| VSWR LM393B (V0.4) | Antenna break/short, feedline fault | Analog comparator | Fast (~ms) — thermal alone reacts in tens of seconds |
| TX-limit CD4060 (V0.4) | Firmware stuck in TX with WD still kicked | Digital counter | The one failure the 555 cannot see: healthy firmware doing the wrong thing |

## V0.2 changes from V0.1

| Change | Reason |
|--------|--------|
| Thermal threshold 70 °C → 65 °C | NTC moved closer to IRF510 die in V0.2 (Card 4 change) but small thermal lag remains. Lower threshold gives margin. |

## V0.4 changes from V0.2 (design review)

| Change | Reason |
|--------|--------|
| AND chain gates a **2N7000** driving the coil | V0.2 routed 30–80 mA coil current through a 4N35 (50 mA abs max) and an LM393 OC (~20 mA): electrically unworkable. |
| **+ VSWR trip** on the spare LM393 half | Antenna-fault protection was software-only; thermal backstop reacts in tens of seconds. Hardware trip in ~1 ms for 3 resistors. |
| **+ CD4060 TX-time limiter** (~10.4 min) | `regulatory.md` claimed a hardwired 10-minute limit that did not exist — the 555 is a firmware-liveness watchdog and holds as long as firmware kicks it. The counter makes the claim true. |

## Fault acknowledgment policy

When any fault triggers, the relay opens, PA Vcc is cut. The chain output
returns to RP2040 GP17 PA_FAULT, which transitions FSM to FAULT state. The
OLED displays the diagnostic (cause identified by reading ADCs and feedback
GPIOs). User must press MENU to acknowledge after physical verification. The
transition back to IDLE is **not automatic** — deliberate choice, because
auto-restart would worsen problems like an antenna mismatch causing thermal
overload.

## Verification procedure

1. **Software EN test.** All other paths OK (kill switch, WD running, thermal
   below threshold). Toggle GP15 from RP2040 — relay opens/closes accordingly.

2. **Kill switch test.** With software EN held high, press kill button.
   Relay opens within 50 ms (limited by relay mechanical time).

3. **WD timeout test.** Run firmware with WD pulses, verify relay holds.
   Disable WD pulses (e.g. block in debugger). After ~1.7 s, 555 times out,
   relay opens. Resume pulses, verify relay does NOT auto-close (because
   software has flagged FAULT and dropped GP15).

4. **Thermal test.** Heat NTC manually (hair dryer). Verify LM393 trips at
   65 °C ± 2 °C (calibrate against thermometer if needed).

5. **VSWR trip test (V0.4).** TX at 10 W into a 3:1 mismatch stub. Relay
   opens within a few ms (scope on the coil). Verify no trip at 1.5:1.

6. **TX-limit test (V0.4).** Hold PTT active with firmware limits disabled
   (bench build). Relay opens at 10.4 min ± 2 min. Release PTT 5 s, re-key:
   full budget restored (reset works).

7. **Combined test.** Drop one protection at a time, verify relay always
   opens when any single condition fails.

## BoM

See [`hardware/bom/card-06-safety.csv`](../../hardware/bom/card-06-safety.csv).
~€18 total.
