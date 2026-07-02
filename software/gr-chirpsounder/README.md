# gr-chirpsounder

GNU Radio out-of-tree (OOT) module for ionospheric chirpsounder reception and
analysis. Inspired by the structure and quality standards of
[gr-satellites](https://github.com/daniestevez/gr-satellites) by Daniel Estévez
EA4GPZ.

## Status

🚧 **In progress since V0.3.** First block implemented:
[`python/ka9q_iq_source.py`](python/ka9q_iq_source.py), a native RTP
multicast source for [ka9q-radio](https://github.com/ka9q/ka9q-radio)
`radiod` channels (complex64 out; f32le/s16le/s16be payloads; SSRC
filtering; zero-fill on RTP sequence gaps). Usable today as a GRC
"Embedded Python Block". Remaining blocks follow in Phase 2.

## Blocks

- `ka9q_iq_source` — radiod multicast IQ source — **implemented (V0.3)**
- `dechirp` — stretch processing matched filter
- `range_fft` — fast-time FFT for range bins
- `direct_leakage_remover` — median subtraction across slow-time
- `doppler_fft` — slow-time FFT for Doppler bins
- `ionogram_sink` — HDF5 archival of range-Doppler frames
- `coherent_int` — coherent integration over multiple chirp trains

## Planned flowgraphs

- `flowgraphs/rx_ka9q_fixed.grc` — fixed-channel RX (30 m SX1262 sounder,
  Mode A of [`docs/architecture/rx-ka9q.md`](../../docs/architecture/rx-ka9q.md))
- `flowgraphs/rx_ka9q_swept.grc` — stepped-LO tracking RX for opportunity
  illuminators (Mode B; sweep control ported from
  [`software/ka9q-backend/chirp_tracker.py`](../ka9q-backend/chirp_tracker.py))
- `flowgraphs/calibration_self_test.grc` — internal loopback for pipeline
  validation

The V0.2 flowgraph targets (ANTSDR E200, Hermes-Lite 2, RTL-SDR) are
dropped; any SDR remains usable offline via
[`software/examples/dechirp_basic.py`](../examples/dechirp_basic.py).

## Reference implementation

A standalone Python reference implementation of the dechirp algorithm is
available in [`software/examples/dechirp_basic.py`](../examples/dechirp_basic.py).
This serves as the algorithmic baseline that the GNU Radio blocks will mirror.

## Standards alignment

Output format will follow the **SAO/SBF** convention used by Lowell DIDBase,
allowing direct interoperability with IRI and NeQuick ionospheric models, as
well as with academic groups using existing professional ionosonde data.
