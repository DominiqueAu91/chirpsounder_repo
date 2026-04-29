# gr-chirpsounder

GNU Radio out-of-tree (OOT) module for ionospheric chirpsounder reception and
analysis. Inspired by the structure and quality standards of
[gr-satellites](https://github.com/daniestevez/gr-satellites) by Daniel Estévez
EA4GPZ.

## Status

🚧 **Planned, not yet implemented.** This directory currently contains design
notes only. Implementation begins in Phase 1 of the project (RX-first approach).

## Planned blocks

- `dechirp` — stretch processing matched filter
- `range_fft` — fast-time FFT for range bins
- `direct_leakage_remover` — median subtraction across slow-time
- `doppler_fft` — slow-time FFT for Doppler bins
- `ionogram_sink` — HDF5 archival of range-Doppler frames
- `coherent_int` — coherent integration over multiple chirp trains

## Planned flowgraphs

- `flowgraphs/rx_antsdr_passive.grc` — passive RX from ANTSDR E200
- `flowgraphs/rx_hermeslite_passive.grc` — passive RX from Hermes-Lite 2
- `flowgraphs/rx_rtlsdr_basic.grc` — minimal RTL-SDR + upconverter
- `flowgraphs/calibration_self_test.grc` — internal loopback for pipeline
  validation

## Reference implementation

A standalone Python reference implementation of the dechirp algorithm is
available in [`software/examples/dechirp_basic.py`](../examples/dechirp_basic.py).
This serves as the algorithmic baseline that the GNU Radio blocks will mirror.

## Standards alignment

Output format will follow the **SAO/SBF** convention used by Lowell DIDBase,
allowing direct interoperability with IRI and NeQuick ionospheric models, as
well as with academic groups using existing professional ionosonde data.
