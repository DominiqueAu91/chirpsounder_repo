#!/usr/bin/env python3
"""
chirp_tracker.py -- Phase 1 PoC capture front end for the ka9q-radio backend.

Replaces the direct-SDR capture (ANTSDR E200 / Hermes-Lite 2 / RTL-SDR) of
V0.2 with a stepped-LO tracking receiver on top of radiod
(RX888 MkII @ 64.8 Msps, GPSDO-disciplined).

Principle
---------
A linear chirp sounder sweeps f_start..f_stop at rate R (typ. 100 kHz/s,
GPS-synchronized to a repeating schedule). We follow it with ONE radiod
IQ channel (bandwidth = samprate, default 96 kHz):

  * the channel is retuned every `step`/R seconds by `step` Hz using the
    ka9q-radio `tune` utility (dynamic channel, SSRC fixed);
  * IQ samples are ingested continuously via
        pcmrecord --stdout --raw --ssrc SSRC chirp-iq.local
    (pcmrecord handles RTP reassembly; --raw gives headerless f32le
    stereo = interleaved I,Q float32);
  * each dwell is written as one .npz segment with its center frequency
    and nominal start time, ready for dechirp.py.

Timing model (PoC): absolute time of sample n is approximated as
t_capture_start + n/fs. The unknown constant pipeline latency of
radiod (~1-2 block times, 20-40 ms) plus host clock error appears as a
constant group-delay bias -> a constant virtual-height offset on the
ionogram. Discipline the host clock with gpsd+chrony (PPS from the
GPSDO) to keep the error < 1 ms (300 km one-way -> after calibration
against a known-range sounder the residual is the chrony jitter,
~10 us with PPS). Phase 2 (gr-chirpsounder) replaces this with
RTP-timestamp/GPS-time bookkeeping from the radiod status stream.

Usage example (a 100 kHz/s sounder starting at :00 +05 s of every
15 min, 2->30 MHz):

  ./chirp_tracker.py --radio hf.local --data chirp-iq.local --ssrc 5001 \
      --f-start 2e6 --f-stop 30e6 --rate 100e3 \
      --period 900 --offset 5.0 --outdir /dev/shm/chirp

Requires: ka9q-radio installed (tune, pcmrecord in PATH), Python 3.10+,
numpy.

Added in V0.3 (ka9q-radio receiver backend).
License: GPL-3.0-or-later
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import numpy as np

BYTES_PER_FRAME = 8  # f32le stereo: 4 bytes I + 4 bytes Q


def next_sweep_start(period: float, offset: float, now: float) -> float:
    """Next UTC epoch time the sounder passes f_start."""
    k = int(now // period) + 1
    t = k * period + offset
    # handle offset making the previous slot still in the future
    while t - period > now:
        t -= period
    return t


def tune_cmd(args, freq_hz: float) -> list[str]:
    half = args.samprate / 2.0
    guard = args.samprate * 0.04  # stay off the filter skirts
    return [
        args.tune_bin,
        "--radio",
        args.radio,
        "--ssrc",
        str(args.ssrc),
        "--mode",
        "iq",
        "--samprate",
        str(int(args.samprate)),
        "--encoding",
        "f32le",
        "--low",
        str(-(half - guard)),
        "--high",
        str(+(half - guard)),
        "--destination",
        args.data,
        "--frequency",
        f"{freq_hz:.0f}",
    ]


def retune(args, freq_hz: float) -> None:
    subprocess.run(tune_cmd(args, freq_hz), check=True, capture_output=True, timeout=5)


def read_exact(pipe, nbytes: int) -> bytes:
    buf = bytearray()
    while len(buf) < nbytes:
        chunk = pipe.read(nbytes - len(buf))
        if not chunk:
            raise EOFError("pcmrecord stream ended")
        buf.extend(chunk)
    return bytes(buf)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--radio",
        default="hf.local",
        help="radiod status/command group (default hf.local)",
    )
    ap.add_argument(
        "--data",
        default="chirp-iq.local",
        help="multicast data group for the chirp IQ channel",
    )
    ap.add_argument("--ssrc", type=int, default=5001)
    ap.add_argument(
        "--samprate",
        type=float,
        default=96e3,
        help="channel sample rate / bandwidth, Hz (default 96k)",
    )
    ap.add_argument("--f-start", type=float, required=True)
    ap.add_argument("--f-stop", type=float, required=True)
    ap.add_argument(
        "--rate", type=float, default=100e3, help="chirp rate, Hz/s (default 100k)"
    )
    ap.add_argument(
        "--period", type=float, default=900.0, help="sounder repetition period, s"
    )
    ap.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="sweep start offset within the period, s (UTC)",
    )
    ap.add_argument(
        "--step", type=float, default=None, help="retune step, Hz (default samprate/2)"
    )
    ap.add_argument("--outdir", default="/dev/shm/chirp")
    ap.add_argument(
        "--sweeps",
        type=int,
        default=1,
        help="number of sweeps to capture (0 = forever)",
    )
    ap.add_argument("--tune-bin", default="tune")
    ap.add_argument("--pcmrecord-bin", default="pcmrecord")
    args = ap.parse_args()

    if args.step is None:
        args.step = args.samprate / 2.0  # 48 kHz steps for a 96 kHz channel
    dwell = args.step / args.rate  # s per segment (0.48 s default)
    n_steps = int(np.ceil((args.f_stop - args.f_start) / args.step))
    fs = args.samprate
    n_dwell = int(round(dwell * fs))

    os.makedirs(args.outdir, exist_ok=True)
    print(
        f"Sweep {args.f_start/1e6:.3f}->{args.f_stop/1e6:.3f} MHz @ "
        f"{args.rate/1e3:.0f} kHz/s: {n_steps} steps of {args.step/1e3:.0f} kHz, "
        f"dwell {dwell*1e3:.0f} ms ({n_dwell} samples)",
        flush=True,
    )

    # Park the channel (creates it dynamically) and start the ingest pipe.
    park = args.f_start + args.step / 2.0
    retune(args, park)
    time.sleep(0.5)
    rec = subprocess.Popen(
        [args.pcmrecord_bin, "--stdout", "--raw", "--ssrc", str(args.ssrc), args.data],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
    )
    # flush whatever accumulated while parking
    assert rec.stdout is not None

    sweep_count = 0
    try:
        while args.sweeps == 0 or sweep_count < args.sweeps:
            now = time.time()
            t0 = next_sweep_start(args.period, args.offset, now)
            print(
                f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] "
                f"next sweep at UTC epoch {t0:.3f} (in {t0-now:.1f} s)",
                flush=True,
            )

            for k in range(n_steps):
                fc = args.f_start + (k + 0.5) * args.step  # dwell center freq
                # chirp reaches the lower edge of this dwell at:
                t_enter = t0 + k * dwell
                # retune slightly early (radiod retune ~1 block, 20 ms)
                t_retune = t_enter - 0.05
                dt = t_retune - time.time()
                if dt > 0:
                    # drain the pipe while waiting so pcmrecord never blocks
                    drain_frames = int(dt * fs)
                    if drain_frames > 0:
                        read_exact(rec.stdout, drain_frames * BYTES_PER_FRAME)
                retune(args, fc)
                # drain the retune guard interval, then capture the dwell
                read_exact(rec.stdout, int(0.05 * fs) * BYTES_PER_FRAME)
                t_seg = time.time()  # nominal start-of-dwell wallclock
                raw = read_exact(rec.stdout, n_dwell * BYTES_PER_FRAME)
                iq = np.frombuffer(raw, dtype="<f4").reshape(-1, 2)
                z = (iq[:, 0] + 1j * iq[:, 1]).astype(np.complex64)
                fn = os.path.join(
                    args.outdir, f"seg_{sweep_count:03d}_{k:04d}_{fc/1e3:.0f}kHz.npz"
                )
                np.savez(
                    fn,
                    z=z,
                    fc=fc,
                    fs=fs,
                    t_start=t_seg,
                    t0_sweep=t0,
                    rate=args.rate,
                    f_start=args.f_start,
                )
            sweep_count += 1
            print(f"sweep {sweep_count} done -> {args.outdir}", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        rec.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
