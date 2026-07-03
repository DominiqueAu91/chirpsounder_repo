# Regulatory framework — French amateur 30m operation

## Allocation status

The 10.100–10.150 MHz amateur allocation in France is **secondary**, shared
with the primary fixed service (notably government links). Amateur emissions
must not interfere with primary services.

The band is restricted to **CW and data modes only** (no phone). Maximum
power: 150 W PEP (ARCEP), well above our 10 W target.

## Operational frequency window

Avoid common digital mode frequencies:

| Frequency | Mode | Status |
|-----------|------|--------|
| 10.130 MHz | FT8 | avoid |
| 10.136 MHz | FT8 expansion | avoid |
| 10.140 MHz | WSPR | avoid absolutely |
| 10.142 MHz | JS8 | avoid |

**Target window: 10.115–10.125 MHz**, naturally quiet. To be coordinated with
REF (beacon coordinator F5NOD or successor) before first activation.

## NCDXF-style discipline

| Aspect | Practice |
|--------|----------|
| Identification | Callsign in CW at start, end, and every 10 minutes during emission |
| Coordination | Frequency and schedule announced to REF and IARU R1 ProAm groups |
| Duty cycle | Maximum 30 s ON / 870 s OFF in beacon mode = 3.3% average |
| Power | Lowest power that closes the link — typically 1–10 W |
| Logs | All dwells recorded UTC with parameters, archived and queryable |
| Neighbor complaint | Emission immediately suspended, log analyzed, resumed only after agreement |
| Maintenance | Annual spectral purity check on bench, coupler recalibration |

## Hardware-enforced limits

**[V0.4 correction]** The V0.2 text claimed the Card 6 watchdog imposed a
hardwired 10-minute emission limit. It did not: the 555 is a 1.7 s
firmware-liveness watchdog and holds as long as firmware kicks it — a
compliance claim must match the hardware. As of V0.4 the claim is made true:

- The firmware FSM enforces the precise limit (re-identification every
  10 minutes of accumulated TX, dwell/pause scheduling — see
  `firmware/rp2040/src/main.c`).
- A **CD4060 TX-time counter on Card 6** (nominal 10.4 min, RC-tolerance
  band 8.3–12.4 min, reset on PTT release) is the hardwired backstop that
  opens the PA relay even if healthy firmware is misconfigured into
  continuous transmission. This element is not firmware-configurable.

## Pre-deployment notifications

Before first activation:

- **REF** (beacons and experimental coordinator) — email with technical description
- **ANFR** — only if power > 100 W, not applicable for our 10 W
- **Local amateurs** within line-of-sight (F4/F5/F6 cluster) — courtesy
- **IARU R1 ProAm Working Group** — for European network integration

## Response to interference reports

1. Cease emission immediately (latching kill switch or STOP command)
2. Request from reporter: exact frequency, UTC timestamp, mode affected
3. Cross-reference with station logs
4. Analyze: unfiltered harmonic? antenna mismatch? intermod product?
5. Correct physically before resuming (additional filter, lower power,
   frequency change)
6. Confirm resolution with reporter before resuming emissions
