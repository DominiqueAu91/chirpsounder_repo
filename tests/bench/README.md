# Bench validation procedures

This directory contains per-card and integration bench validation procedures.
Each procedure specifies the measurement, expected result, and the instrument
required.

## Per-card procedures

- [`card-01-power.md`](card-01-power.md) — DC rails, ripple, thermal
- [`card-02-coherence.md`](card-02-coherence.md) — Squarer, PLLs, frequency lock
- [`card-03-rf-low.md`](card-03-rf-low.md) — Chirp, mixer, BPF alignment
- [`card-04-rf-high.md`](card-04-rf-high.md) — Driver, PA, coupler, LPF
- [`card-05-control.md`](card-05-control.md) — IHM, USB host, ADC calibration
- [`card-06-safety.md`](card-06-safety.md) — Watchdog, thermal trip, kill switch

## Integration procedures

- [`integration-rf-chain.md`](integration-rf-chain.md) — Full chain end-to-end
- [`integration-vswr-cal.md`](integration-vswr-cal.md) — Coupler calibration
- [`integration-thermal.md`](integration-thermal.md) — Continuous TX thermal cycle
- [`integration-spectral-purity.md`](integration-spectral-purity.md) — Harmonics
  and spurs vs ETSI EN 301 783 limits

## Measurement instruments required

| Instrument | Purpose | Suggested model |
|------------|---------|-----------------|
| Spectrum analyzer | Spectral purity, phase noise | Rigol DSA815 or better |
| Oscilloscope | Time-domain waveforms | Rigol DS1054Z (≥ 50 MHz BW) |
| VNA | Filter alignment | NanoVNA H4 or better |
| Frequency counter | Lock verification | Any 10-digit counter referenced |
| Wattmeter | Power calibration | Bird 43 with appropriate slug |
| Dummy load | TX testing | 50 Ω, 25 W rated minimum |
| Thermometer | NTC calibration | IR thermometer or thermocouple |
