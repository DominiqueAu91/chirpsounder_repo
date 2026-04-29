# Card 5 — Control

> RP2040 supervisor: PLL control, IHM (OLED + encoder + buttons), USB host
> for log storage, GPSDO PPS capture, ADC monitoring, safety chain coordination.

## Function

Single point of control for the entire transmitter. Headless or interactive
operation; standalone (no PC required) once configured. The RP2040 dual-core
architecture lets us separate hard real-time RF sequencing (Core 1) from
soft real-time IHM and logging (Core 0).

## RP2040 GPIO mapping

| GPIO | Direction | Function |
|------|-----------|----------|
| GP0/GP1 | UART | Optional debug console |
| GP2 | in | BUSY SX1262 |
| GP3 | out | NSS SX1262 |
| GP4 | out | SPI0 MOSI (SX1262 + ADF4351) |
| GP5 | out | SPI0 SCK (shared) |
| GP6 | in | SPI0 MISO (SX1262 only) |
| GP7 | out | LE ADF4351 |
| GP8 | in | DIO1 SX1262 (IRQ) |
| GP9 | out | NRST SX1262 |
| GP10 | out | CE ADF4351 |
| GP11 | in | MUXOUT ADF4351 (lock detect) |
| GP12 | I²C0 SDA | Si5351 + OLED |
| GP13 | I²C0 SCL | shared |
| GP14 | in | PPS_IN (PIO sub-µs capture) |
| GP15 | out | PA_ENABLE → Card 6 |
| GP16 | out | PTT_KEY → Card 4 opto |
| GP17 | in | PA_FAULT ← Card 6 |
| GP18 | in | ENC_A |
| GP19 | in | ENC_B |
| GP20 | in | ENC_SW push |
| GP21 | in | BTN_RUN green |
| GP22 | in | BTN_STOP red |
| GP23 | in | BTN_MENU yellow |
| GP24/25 | i/o | Reserved TinyUSB host |
| ADC0 (GP26) | in | V_fwd from coupler |
| ADC1 (GP27) | in | V_rev from coupler |
| ADC2 (GP28) | in | T_PA from NTC |
| ADC4 internal | in | RP2040 die temperature |

## State machine

```
   BOOT → init OLED, USB host, Si5351, ADF4351, SX1262
     │
     v
   IDLE ◄────────────────────────────────────┐
     │ RUN button                             │
     v                                        │
   ARMING → self-test, GPSDO lock check       │
     │ all checks OK                          │ FAULT path
     v                                        │ (any state)
   CW_ID → emit callsign                      │
     │                                        │
     v                                        │
   DWELL_TX → 30 s chirp                      │
     │                                        │
     v                                        │
   PAUSE → silence 5 s ◄─── more dwells       │
     │ schedule done                          │
     v                                        │
   CW_ID_FINAL                                │
     │                                        │
     └──────────────────────────────────────► │
                                              │
   FAULT ←───────────────────────────────────┘
     │ PA cut, log error
     │ MENU button = acknowledge
     v
   IDLE
```

## Firmware architecture

- **Core 0**: state machine, IHM (OLED, encoder, buttons), USB host log
- **Core 1**: RF chain piloting (SX1262, ADF4351), PPS-aligned sequencing
- **PIO0**: PPS sub-µs capture (custom assembler)
- **PIO1**: reserved for future TinyUSB host
- **DMA**: I²C/SPI offload
- **USB-CDC**: AT-style command console for configuration

Languages: **C with pico-sdk** for production, **MicroPython** acceptable for
fast PoC iteration. Recommendation: start MicroPython, migrate hot paths to C.

## Peripherals

**OLED 128×64 SSD1306** — I²C at 0x3C. Idle: 6-line status. TX: dashboard
(frequency, dwell timer, V_fwd/V_rev, VSWR, T_PA, GPSDO state, RF active LED).
5 Hz refresh in TX, 1 Hz in idle.

**Encoder KY-040** — 24-detent rotary, quadrature ENC_A/B, push integrated.
GPIO interrupt + 10 ms software debounce.

**Three buttons** — RUN green, STOP red, MENU yellow.

**USB host CH376S** — UART at 9600 baud, FAT16/32 on USB sticks up to 32 GB.
Per-dwell CSV: timestamp UTC, frequency, SF, BW, duration, P_fwd, P_rev,
VSWR, T_PA, GPSDO_lock.

## BoM

See [`hardware/bom/card-05-control.csv`](../../hardware/bom/card-05-control.csv).
~€28 total.
