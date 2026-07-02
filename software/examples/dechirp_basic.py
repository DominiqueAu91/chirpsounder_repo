"""
dechirp_basic.py — Reference dechirp pipeline for SX1262-style LFM sounders.

This is the canonical 100-line dechirp implementation. It demonstrates the
stretch-processing approach used by gr-chirpsounder. Suitable for offline
analysis of recorded IQ from any SDR with sufficient bandwidth coverage of
the 10 MHz IF band.

Pipeline:
  1. Load IQ samples (recorded from ANTSDR E200 / Hermes-Lite 2 / RTLSDR-30m)
  2. Generate local reference chirp matching emitter parameters
  3. Multiply IQ by conjugate reference (the dechirp step)
  4. Reshape into (N_chirps, N_samples_per_chirp) matrix
  5. FFT along fast-time axis → range bins
  6. Median subtraction across slow-time → remove direct leakage
  7. FFT along slow-time axis → Doppler bins
  8. Plot range-Doppler ionogram

Author: Dominique Auprince
License: GPL-3.0-or-later
"""

import numpy as np
import matplotlib.pyplot as plt


def generate_reference_chirp(sf: int, bw: float, fs: float) -> np.ndarray:
    """Generate one period of a SX1262-style LFM chirp at baseband.

    Args:
        sf: Spreading factor (e.g. 12 for ionospheric F-layer)
        bw: Bandwidth in Hz (e.g. 7812.5)
        fs: Sample rate in Hz (must be >= 2 * bw)

    Returns:
        Complex baseband chirp, length = 2^sf samples per symbol.
    """
    n_sym = int(2**sf * fs / bw)
    t = np.arange(n_sym) / fs
    mu = bw**2 / 2**sf
    return np.exp(1j * np.pi * mu * t**2)


def dechirp(iq: np.ndarray, sf: int, bw: float, fs: float) -> np.ndarray:
    """Apply stretch processing to IQ samples.

    Args:
        iq: Complex IQ samples, contiguous chirp train.
        sf, bw, fs: Chirp parameters (must match emitter).

    Returns:
        Dechirped signal, same length as input.
    """
    ref = generate_reference_chirp(sf, bw, fs)
    n_sym = len(ref)
    n_chirps = len(iq) // n_sym
    iq = iq[: n_chirps * n_sym]
    ref_train = np.tile(np.conj(ref), n_chirps)
    return iq * ref_train


def range_doppler_map(dechirped: np.ndarray, sf: int, fs: float) -> np.ndarray:
    """Build range-Doppler matrix from a dechirped chirp train.

    Args:
        dechirped: Output of dechirp().
        sf: Spreading factor used.
        fs: Sample rate.

    Returns:
        2D array (n_chirps, n_range_bins) in dB, ready for plotting.
    """
    n_sym = int(2**sf)
    n_chirps = len(dechirped) // n_sym
    matrix = dechirped[: n_chirps * n_sym].reshape(n_chirps, n_sym)

    # Fast-time FFT: each row → range bins
    range_pre = np.fft.fft(matrix, axis=1)

    # Median subtraction across slow-time: removes direct leakage
    median_per_range = np.median(np.abs(range_pre), axis=0)
    range_clean = range_pre - median_per_range[np.newaxis, :]

    # Slow-time FFT: each column → Doppler bins
    range_doppler = np.fft.fft(range_clean, axis=0)

    return 20 * np.log10(np.abs(range_doppler) + 1e-12)


def plot_ionogram(rd_map: np.ndarray, fs: float, f0: float, sf: int, bw: float):
    """Plot range-Doppler map with proper axis labels for ionospheric data."""
    n_chirps, n_range = rd_map.shape
    c = 3e8
    delta_r = c / (2 * bw)  # m
    ranges_km = np.arange(n_range // 2) * delta_r / 1000
    prf = bw / 2**sf
    dopplers = np.fft.fftfreq(n_chirps, d=1 / prf)

    fig, ax = plt.subplots(figsize=(10, 6))
    rd_half = rd_map[:, : n_range // 2]
    rd_shift = np.fft.fftshift(rd_half, axes=0)
    dop_shift = np.fft.fftshift(dopplers)

    im = ax.pcolormesh(
        ranges_km,
        dop_shift,
        rd_shift,
        shading="auto",
        cmap="viridis",
        vmin=np.percentile(rd_shift, 50),
        vmax=np.percentile(rd_shift, 99),
    )
    ax.set_xlabel("Virtual range (km)")
    ax.set_ylabel("Doppler (Hz)")
    ax.set_title(f"Ionogram — f0 = {f0/1e6:.3f} MHz, SF{sf}, BW = {bw/1e3:.2f} kHz")
    plt.colorbar(im, ax=ax, label="Power (dB)")
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    # Example with synthetic data
    fs = 100e3
    f0 = 10.12e6
    sf = 12
    bw = 7812.5
    n_chirps = 64

    # Synthesize an emitter chirp + a delayed echo
    ref = generate_reference_chirp(sf, bw, fs)
    direct = np.tile(ref, n_chirps)
    echo_delay = 200e3 * 2 / 3e8  # 200 km virtual range
    echo_samples = int(echo_delay * fs)
    echo = np.roll(direct, echo_samples) * 0.1
    iq = (
        direct
        + echo
        + 0.01 * (np.random.randn(len(direct)) + 1j * np.random.randn(len(direct)))
    )

    dechirped = dechirp(iq, sf, bw, fs)
    rd_map = range_doppler_map(dechirped, sf, fs)
    plot_ionogram(rd_map, fs, f0, sf, bw)
    plt.savefig("ionogram_demo.png", dpi=120)
    print("Saved ionogram_demo.png")
