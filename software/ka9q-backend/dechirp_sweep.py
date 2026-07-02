#!/usr/bin/env python3
"""
dechirp_sweep.py -- Phase 1 PoC processing: segments -> oblique ionogram.

Each segment produced by chirp_tracker.py contains the complex baseband
of one dwell, centered on fc, while the sounder chirp sweeps through the
channel. We multiply by the conjugate of the synthetic zero-delay chirp
(referenced to the GPS-scheduled sweep start t0) and take an STFT.

After dechirp, a propagation path with group delay tau appears as a tone
at f_tone = -R * tau  (it lags the reference). The STFT therefore maps
directly to the ionogram:

    time axis  -> sounder frequency:  f = f_start + R * (t - t0)
    STFT freq  -> group delay:        tau = -f_tone / R
    delay res  -> 1 / (R * T_window)  e.g. 0.1 s window @ 100 kHz/s
                                            -> 100 us -> 15 km one-way

Constant timing bias (radiod pipeline latency + host clock offset)
shifts all tau by the same amount; calibrate with --tau-bias.

Usage:
    ./dechirp_sweep.py --indir /dev/shm/chirp --sweep 0 --out ionogram.png

Added in V0.3 (ka9q-radio receiver backend).
License: GPL-3.0-or-later
"""

import argparse
import glob
import os
import re
import sys

import numpy as np


def dechirp_segment(
    z, fs, fc, t_start, t0, rate, f_start, win_s=0.1, tau_max=8e-3, tau_bias=0.0
):
    """Return (freqs_MHz, taus_ms, S_dB) tiles for one dwell."""
    n = len(z)
    t = t_start + np.arange(n) / fs  # wallclock of each sample
    u = t - t0  # time since sweep start
    # zero-delay reference at baseband of this channel:
    #   phi(t) = 2*pi * ( f_start*u + R*u^2/2 - fc*u )
    phi = 2 * np.pi * ((f_start - fc) * u + 0.5 * rate * u**2)
    y = z * np.exp(-1j * phi)

    nw = int(round(win_s * fs))
    nseg = n // nw
    if nseg == 0:
        return None
    y = y[: nseg * nw].reshape(nseg, nw)
    w = np.hanning(nw)
    Y = np.fft.fftshift(np.fft.fft(y * w, axis=1), axes=1)
    fax = np.fft.fftshift(np.fft.fftfreq(nw, 1 / fs))
    tau = -fax / rate - tau_bias  # s
    sel = (tau >= 0) & (tau <= tau_max)
    S = 20 * np.log10(np.abs(Y[:, sel]) + 1e-12)
    # sounder frequency at the center of each STFT window
    tw = t_start + (np.arange(nseg) + 0.5) * nw / fs
    fsound = f_start + rate * (tw - t0)
    return fsound / 1e6, tau[sel] * 1e3, S


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--indir", default="/dev/shm/chirp")
    ap.add_argument("--sweep", type=int, default=0)
    ap.add_argument(
        "--win", type=float, default=0.1, help="STFT window, s (delay res = 1/(R*win))"
    )
    ap.add_argument("--tau-max", type=float, default=8e-3)
    ap.add_argument(
        "--tau-bias",
        type=float,
        default=0.0,
        help="calibration bias to subtract from delay, s",
    )
    ap.add_argument("--out", default="ionogram.png")
    args = ap.parse_args()

    files = sorted(
        glob.glob(os.path.join(args.indir, f"seg_{args.sweep:03d}_*.npz")),
        key=lambda p: int(re.search(r"_(\d{4})_", p).group(1)),
    )
    if not files:
        print("no segments found", file=sys.stderr)
        return 1

    cols_f, cols_S, taus = [], [], None
    for fn in files:
        d = np.load(fn)
        r = dechirp_segment(
            d["z"],
            float(d["fs"]),
            float(d["fc"]),
            float(d["t_start"]),
            float(d["t0_sweep"]),
            float(d["rate"]),
            float(d["f_start"]),
            win_s=args.win,
            tau_max=args.tau_max,
            tau_bias=args.tau_bias,
        )
        if r is None:
            continue
        f, taus, S = r
        cols_f.append(f)
        cols_S.append(S)

    F = np.concatenate(cols_f)
    S = np.vstack(cols_S)  # [freq, tau]
    order = np.argsort(F)
    F, S = F[order], S[order]

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 6))
    vmax = np.percentile(S, 99.5)
    m = ax.pcolormesh(
        F, taus, S.T, vmin=vmax - 40, vmax=vmax, shading="auto", cmap="inferno"
    )
    ax.set_xlabel("Sounder frequency (MHz)")
    ax.set_ylabel("Group delay (ms)")
    ax2 = ax.secondary_yaxis(
        "right", functions=(lambda t: t * 149.9, lambda h: h / 149.9)
    )
    ax2.set_ylabel("One-way virtual range (km)")
    fig.colorbar(m, ax=ax, label="dB (uncal)")
    ax.set_title("Chirpsounder PoC — ka9q-radio / RX888 MkII backend")
    fig.tight_layout()
    fig.savefig(args.out, dpi=130)
    print(f"wrote {args.out}: {len(F)} freq bins x {len(taus)} delay bins")
    return 0


if __name__ == "__main__":
    sys.exit(main())
