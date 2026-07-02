# Phase noise budget

## V0.2 budget at 10 MHz IF, 1 kHz offset

| Source | Phase noise | Notes |
|--------|-------------|-------|
| GPSDO 10 MHz reference | -125 dBc/Hz | Trimble Thunderbolt or equivalent |
| Si5351 + 32 MHz lock (sine mode, V0.2) | -110 dBc/Hz @ 32 MHz | Improved ~5 dB vs V0.1 CMOS mode |
| ADF4351 + 905 MHz lock | -95 dBc/Hz @ 905 MHz | Dominant term |
| SX1262 PLL @ 915 MHz | -95 dBc/Hz @ 915 MHz | Similar to ADF4351 |
| Mixer ADE-R3+ | negligible (< -130 dBc/Hz) | Floor |
| **Total at 10 MHz IF** | **≈ -95 dBc/Hz @ 1 kHz** | |

## Verification

Combined RSS calculation:

```text
P_total = -10 * log10(sum(10^(P_i/10) for i in sources))
        ≈ -95 dBc/Hz @ 1 kHz offset
```

## Margin analysis for SF12 / BW = 7.8 kHz

Pulse compression gain at SF12:

```text
G_pc = 10 * log10(2^12) = 36 dB
```

Required SNR at output of compression for detection:

```text
SNR_out = 10 dB (typical for ionogram pixel)
```

Required SNR at input:

```text
SNR_in = SNR_out - G_pc = 10 - 36 = -26 dB
```

Phase noise contribution to noise floor in 1 Hz bandwidth:

```text
N_pn = -95 dBc/Hz
```

For BW = 7.8 kHz integration:

```text
N_pn_total = -95 + 10 * log10(7800) = -95 + 38.9 = -56 dBc
```

This is well below the chirp signal level, so phase noise is **not the
limiting factor** for our application. Thermal noise from the receiver
(typically -174 dBm/Hz noise floor at antenna + receiver noise figure
~3 dB) and external HF noise (typically -100 to -120 dBm/Hz at 10 MHz
in rural site) dominate.

## Conclusion

V0.2 phase noise budget is comfortable for the intended SF12 / 7.8 kHz mode.
Future modes with higher SF (compression gain > 40 dB) might benefit from
better LO sources, but for the current scope, we're not phase-noise-limited.
