# Card 6 — Safety

> Hardwired AND chain protecting PA Vcc. Four independent conditions must hold
> simultaneously for the relay to close.

## Function

Heterogeneous redundancy: each protection detects a different failure class
using a different technology, so no single common-cause failure can defeat
multiple protections at once.

## Schematic

```
Card 5 GP15 PA_ENABLE (software logic)
    │
    v
[4N35 opto, R_in 220 Ω, 5 kV galvanic isolation]
    │ open-collector output
    v
[Soft EN] → [Kill SW] → [Watchdog 555] → [Thermal LM393] → [12V relay coil]
contact     manual NC    monostable       comparator       DPDT, 5A NO contact
closed      latching     retriggerable    NTC < 70 °C       diode flyback 1N4007
when EN OK  type ALPS    timeout 1.7 s    open-collector    LED green "PA armed"

Relay NO contact:
12V_in ────o   o────► 12V_PA → Card 4 PA Vcc

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

## Why four diverse protections

| Protection | Failure class | Technology | Independence |
|------------|---------------|------------|--------------|
| Software (PA_EN) | Logic errors, misconfiguration | RP2040 GPIO | Programmed logic |
| Kill switch | Human intervention, neighbor complaint, emergency | Mechanical contact | 100% software-independent |
| Watchdog 555 | Firmware crash, deadlock, blocked IRQ | Analog RC timer | Detects software failures |
| Thermal LM393 | Antenna mismatch, fan failure, PA aging | Analog comparator | Detects physical failures |

## V0.2 changes from V0.1

| Change | Reason |
|--------|--------|
| Thermal threshold 70 °C → 65 °C | NTC moved closer to IRF510 die in V0.2 (Card 4 change) but small thermal lag remains. Lower threshold gives margin. |

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

5. **Combined test.** Drop one protection at a time, verify relay always
   opens when any single condition fails.

## BoM

See [`hardware/bom/card-06-safety.csv`](../../hardware/bom/card-06-safety.csv).
~€18 total.
