# Chirpsounder ProAm — Amateur HF ionospheric sounder

> Coherent LFM radar transmitter, GPSDO-disciplined, for amateur ionospheric sounding
> on the 30m band (10.1 MHz). Distributed ProAm architecture — passive receiver first,
> dedicated transmitter second.

## Why this project

The ionosphere remains one of the least instrumented geophysical objects in amateur
practice. Professional ionosondes (Lowell DIDBase network, military Digisondes, CODAR)
produce data that is partly public, partly proprietary, with uneven geographic coverage.
On the amateur side, WSPRnet and PSKReporter give an indirect mapping of propagation, but
no distributed **coherent LFM sounder** equivalent exists.

The [SX1262_CHIRP hack by Peter Ibelings](https://github.com/ibelinp/SX1262_CHIRP) has
shown that a GPSDO-disciplinable coherent LFM chirp can be generated for ~€20 of silicon.
This project aims to **extend that hack** toward a distributed European ProAm
infrastructure, with:

- A Python / GNU Radio receiver that dechirps existing opportunity illuminators
  (military chirpsounders, CODAR, amateur SX1262 signals) — **phase 1, no transmission**.
  Since V0.3 the reference RX platform is the wsprdaemon architecture (GPSDO +
  RX888 MkII + miniPC) running [ka9q-radio](https://github.com/ka9q/ka9q-radio),
  so existing wsprdaemon stations become sounder nodes at zero hardware cost.
- A standalone 30m transmitter disciplined by an amateur GPSDO, NCDXF-style regulatory
  practice, BoM ~€330 — **phase 2, after RX validation**.
- A standardized HDF5 archival format, compatible with professional ionospheric models
  (IRI, NeQuick) — **shared data infrastructure**.
- A coordinated operational protocol with REF / IARU R1 for transmitting nodes.

## Status — V0.3

- ✅ Conceptual architecture defined (6-card partitioning)
- ✅ RF chain budget computed and revised after V0.1 review
- ✅ V0.1 design flaws identified and addressed (see [`docs/CHANGELOG.md`](docs/CHANGELOG.md))
- ✅ **V0.3: receiver platform migrated to ka9q-radio / RX888 MkII (wsprdaemon
  architecture)** — see [`docs/architecture/rx-ka9q.md`](docs/architecture/rx-ka9q.md)
- ✅ Stepped-LO dechirp chain implemented and validated by simulation
  ([`software/ka9q-backend/`](software/ka9q-backend/))
- ✅ First gr-chirpsounder block implemented: `ka9q_iq_source`
- 🚧 Card-level schematics under revision (TX, unchanged since V0.2)
- 🚧 PCB floorplans pending KiCad migration
- ⏳ Phase 1 RX on-air validation against a known sounder — next milestone
- ⏳ TX bench validation — after RX validated end-to-end

## Repository structure

```text
docs/             Design documents, theory, calculations, operating practice
hardware/         Schematics, BoM, KiCad placeholders
firmware/         RP2040 firmware (control card)
software/         GNU Radio OOT module, ka9q-radio backend, Python tools
simulations/      Filter synthesis, phase noise modeling
tests/            Bench validation procedures, field test logs
.github/          CI workflows and issue templates
```

See [`docs/architecture/overview.md`](docs/architecture/overview.md) for a guided tour.

## Phasing

The project follows a deliberately conservative phasing — RX first, TX second — for two
reasons. First, the RX side has near-zero regulatory friction and a BoM near zero
(reusing existing SDR hardware), which lets us validate the dechirp pipeline end-to-end
on opportunity signals before committing to TX hardware. Second, RX validation generates
the analytical tools (matched filter, FFT pipeline, ionogram extraction) that the
network needs whether or not we ever build a TX.

| Phase | Goal | Duration | Status |
|-------|------|----------|--------|
| 0 | Repository scaffold, V0.3 design freeze | 1 month | 🚧 |
| 1 | Python PoC dechirp on ka9q-radio / RX888 MkII + GPSDO | 2-3 months | 🚧 |
| 2 | `gr-chirpsounder` GNU Radio module (`ka9q_iq_source` done) | 3-4 months | 🚧 |
| 3 | TX prototype validation, single node | 6 months | ⏳ |
| 4 | First multi-node operations (3-4 stations) | 12 months | ⏳ |

## Inspiration

Three project lineages converge here:

- **[SX1262_CHIRP](https://github.com/ibelinp/SX1262_CHIRP)** by Peter Ibelings — the
  original silicon hack that makes coherent LFM accessible at amateur cost.
- **[gr-satellites](https://github.com/daniestevez/gr-satellites)** by Daniel Estévez
  EA4GPZ — the gold standard for ProAm GNU Radio out-of-tree modules, our software
  template.
- **NCDXF/IARU beacon network** — the operational template for coordinated, identified,
  low-duty-cycle persistent emissions on amateur HF.

## License

- Hardware designs: [CERN-OHL-S v2](LICENSE-HARDWARE)
- Software: [GPL-3.0-or-later](LICENSE-SOFTWARE)
- Documentation: [CC BY-SA 4.0](LICENSE-DOCS)

## Contact

Author: Dominique Auprince — <dominique_au91 at yahoo.com>

Contributions welcome via Pull Request. Please read
[`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting.
