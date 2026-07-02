# LFM pulse compression — theoretical reference

## Fundamentals

LFM = Linear Frequency Modulation. A coherent chirp signal whose instantaneous
frequency increases (or decreases) linearly with time:

```text
s(t) = exp(j π μ t²)        for 0 ≤ t < T_sym
```

with chirp rate `μ = BW / T_sym` (Hz/s).

## Key relations

```text
T_sym  = 2^SF / BW                    symbol duration (s)
μ      = BW / T_sym = BW² / 2^SF      chirp rate (Hz/s)
PRF    = 1 / T_sym = BW / 2^SF        repetition frequency (Hz)
BT     = BW × T_sym = 2^SF            time-bandwidth product
G_pc   = 10·log10(2^SF) ≈ 3.01·SF     pulse-compression gain (dB)
Δr     = c / (2·BW)                   monostatic range resolution
R_ua   = c · T_sym / 2                monostatic unambiguous range
f_d_ua = PRF / 2                      unambiguous Doppler (Hz)
v_ua   = c · PRF / (4 · f_0)          unambiguous radial velocity (m/s)
```

**Invariant** (independent of SF, BW choices):

```text
R_ua × v_ua = c² / (8 · f_0)
```

At 10 MHz: `R_ua × v_ua = 1.124 × 10⁹ m²/s`.

## Recommended ionospheric configurations

| Application | SF | BW (Hz) | T_sym (s) | Δr (km) | G_pc (dB) |
|-------------|----|---------|-----------|---------|-----------|
| Chirpsounder F-layer | 11 | 7812.5 | 0.262 | 19.2 | 33 |
| Chirpsounder F-layer fine | 12 | 7812.5 | 0.524 | 19.2 | 36 |
| E-layer fast sounding | 10 | 15625 | 0.0655 | 9.6 | 30 |
| TID detection (Doppler) | 11 | 15625 | 0.131 | 9.6 | 33 |
| 6m meteor radar (50 MHz) | 10 | 62500 | 0.0164 | 2.4 | 30 |

Typical choices favor high SF (max compression gain compatible with low amateur
power) and narrow BW (resolution matching ionospheric coherence ~ 10 km). The
SF12 / BW = 7.8 kHz mode gives 36 dB gain and 19 km resolution — exactly the
amateur ionospheric chirpsounder profile, and it matches the cover photo of the
SX1262_CHIRP repository.

## Stretch processing principle

In stretch processing (used in our RX pipeline), the received chirp is mixed
with the local reference chirp:

```text
y(t) = r(t) · s*(t)   ≈ exp(j 2π μ τ t)    for delay τ
```

The product is a tone at frequency `f_b = μ · τ` proportional to delay.
A simple FFT on the dechirped signal yields a frequency spectrum whose peaks
correspond to range bins, with range resolution `Δr = c / (2·BW)` and
processing gain equal to `BT = 2^SF`.

## Implementation in Python

See [`software/examples/dechirp_basic.py`](../../software/examples/dechirp_basic.py)
for the canonical 100-line dechirp pipeline.
