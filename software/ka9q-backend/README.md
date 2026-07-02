# ka9q-backend

Receiver backend on the wsprdaemon reference hardware (GPSDO + RX888 MkII +
Beelink miniPC, Ubuntu Server 24.04 LTS) running
[ka9q-radio](https://github.com/ka9q/ka9q-radio). Introduced in **V0.3**,
replacing the ANTSDR E200 / Hermes-Lite 2 / RTL-SDR options of V0.2.

Full design rationale and the stepped-LO tracking theory:
[`docs/architecture/rx-ka9q.md`](../../docs/architecture/rx-ka9q.md).

## Contents

| File | Role |
|------|------|
| `radiod@chirp.conf` | radiod config: RX888 @ 64.8 Msps, GPSDO reference |
| `chirp_tracker.py` | Sweep tracker for opportunity illuminators (Mode B) |
| `dechirp_sweep.py` | Dwell segments → oblique ionogram (PNG) |
| `test_dechirp_sim.py` | Offline validation — run it before anything else |

## Quick start

```sh
# 1. ka9q-radio (build per its INSTALL.md)
git clone https://github.com/ka9q/ka9q-radio && cd ka9q-radio
make -j && sudo make install
sudo cp radiod@chirp.conf /etc/radio/
sudo systemctl enable --now radiod@chirp

# 2. time discipline (mandatory — see rx-ka9q.md)
sudo apt install gpsd chrony

# 3. validate the DSP chain offline
python3 test_dechirp_sim.py     # must print PASS

# 4. track a known sounder (example: 100 kHz/s, every 15 min, offset 5 s)
./chirp_tracker.py --f-start 2e6 --f-stop 30e6 --rate 100e3 \
    --period 900 --offset 5.0 --outdir /dev/shm/chirp --sweeps 1
./dechirp_sweep.py --indir /dev/shm/chirp --out ionogram.png
```

For the project's own SX1262 sounder on 30 m (Mode A), no tracker is needed:
create one fixed IQ channel with `tune` and feed
`software/examples/dechirp_basic.py` or the `gr-chirpsounder`
`ka9q_iq_source` block.
