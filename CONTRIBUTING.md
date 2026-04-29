# Contributing

Thank you for considering contributing to this ProAm chirpsounder project.

## Scope of contributions

This repository accepts contributions in five areas:

- **Hardware reviews** — schematic critique, layout suggestions, component
  alternatives, EMC observations
- **Firmware** — RP2040 control firmware, state machine improvements, IHM
- **Software** — `gr-chirpsounder` GNU Radio module, dechirp algorithms, data
  format
- **Documentation** — clarifications, additional measurement procedures,
  translations
- **Field reports** — bench measurement results, antenna data, ionospheric
  observations from your station

## How to contribute

1. **Open an issue first** for any non-trivial change, to discuss scope and
   approach before investing implementation time.
2. **Fork the repository** and create a feature branch (`feature/short-name` or
   `fix/short-name`).
3. **Submit a pull request** with a clear description, references to the issue
   it addresses, and any relevant measurement data or simulation results.

## Coding conventions

- **Python**: Black formatting (line length 88), type hints encouraged, docstrings
  in Google style.
- **C (RP2040)**: Linux kernel style, 4-space indent, descriptive function names.
- **Markdown documentation**: 80-character soft wrap, tables for tabular data,
  prose paragraphs for narrative.
- **CSV BoM files**: UTF-8, comma-separated, header row required.

## Hardware contributions

Schematic reviews are welcome. Please format proposed changes as:

- A clear statement of the issue identified
- The proposed correction with component-level detail
- Justification (datasheet reference, simulation result, measurement data)
- Estimated cost impact on BoM

We track design changes in [`docs/CHANGELOG.md`](docs/CHANGELOG.md) and
maintain version V0.x for design iterations. A change accepted as a substantive
correction triggers a CHANGELOG entry.

## Licensing

By contributing, you agree that your contributions will be licensed under the
project's licenses:

- Hardware → CERN-OHL-S v2
- Software → GPL-3.0-or-later
- Documentation → CC BY-SA 4.0

## Code of conduct

Discussion is technical, factual, and collegial. We follow the spirit of the
amateur radio code of conduct: respect for fellow operators, honesty about
limitations, willingness to learn from mistakes.

Disagreements happen and are welcome — they are how engineering moves forward.
Personal attacks, gatekeeping, and dismissive language are not.

## Contact

Maintainer: Dominique Auprince — <dominique_au91 at yahoo.com>

For sensitive issues (security disclosures, etc.), email rather than
public issue tracker.
