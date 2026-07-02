#!/usr/bin/env python3
"""
test_dechirp_sim.py -- validate the stepped-LO dechirp chain offline.

Simulates what radiod's IQ channel would deliver during 6 dwells while a
100 kHz/s sounder sweeps through, with a two-path ionosphere:
   path 1: tau = 2.0 ms (one-way virtual range ~300 km), 0 dB
   path 2: tau = 3.4 ms (~510 km), -10 dB
plus noise, then runs dechirp_segment() and checks the recovered delays.

Added in V0.3 (ka9q-radio receiver backend).
License: GPL-3.0-or-later
"""

import numpy as np
from dechirp_sweep import dechirp_segment

rng = np.random.default_rng(1)

fs = 96e3
rate = 100e3
f_start = 8e6
step = 48e3
dwell = step / rate  # 0.48 s
n = int(dwell * fs)
t0 = 1000.0  # sweep start epoch (arbitrary)
paths = [(2.0e-3, 1.0), (3.4e-3, 0.316)]

segs = []
for k in range(6):
    fc = f_start + (k + 0.5) * step
    t_start = t0 + k * dwell
    t = t_start + np.arange(n) / fs
    z = np.zeros(n, dtype=np.complex128)
    for tau, a in paths:
        u = t - tau - t0  # emission time since sweep start
        frf_phase = f_start * u + 0.5 * rate * u**2  # RF phase/(2pi) at emission
        z += a * np.exp(2j * np.pi * (frf_phase - fc * t))
    z += (rng.normal(size=n) + 1j * rng.normal(size=n)) * 0.05
    segs.append((z.astype(np.complex64), fc, t_start))

ok = True
for z, fc, t_start in segs:
    f_MHz, tau_ms, S = dechirp_segment(
        z, fs, fc, t_start, t0, rate, f_start, win_s=0.12, tau_max=6e-3
    )
    prof = S.mean(axis=0)
    # find the two strongest local peaks
    idx = np.argsort(prof)[::-1]
    found = []
    for i in idx:
        if all(abs(tau_ms[i] - f) > 0.3 for f in found):
            found.append(tau_ms[i])
        if len(found) == 2:
            break
    found.sort()
    err = [abs(found[j] - [2.0, 3.4][j]) for j in range(2)]
    print(
        f"dwell fc={fc/1e6:.3f} MHz  f_sound={f_MHz[0]:.3f}-{f_MHz[-1]:.3f} "
        f"MHz  peaks at {found[0]:.3f}, {found[1]:.3f} ms  "
        f"(err {err[0]*1e3:.1f}, {err[1]*1e3:.1f} us)"
    )
    ok &= max(err) < 0.05  # 50 us tolerance
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
