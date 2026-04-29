# KiCad project files

Schematics and PCB layouts in KiCad format will go here.

## Status

🚧 **Placeholder.** KiCad migration is planned for V0.3 once the V0.2
schematic corrections are validated on bench prototypes built from the
Markdown documentation.

## Planned files (per card)

- `card-XX/card-XX.kicad_pro` — project file
- `card-XX/card-XX.kicad_sch` — schematic
- `card-XX/card-XX.kicad_pcb` — PCB layout
- `card-XX/exports/` — generated Gerbers, BoM, schematic PDF

## Conventions

- KiCad version 7.x or later
- Schematic page size A3
- PCB grid 0.05 mm, design rules per JLCPCB capabilities (4-mil traces minimum)
- Symbol libraries: KiCad standard + project-local for non-standard parts
- Footprint libraries: KiCad standard + project-local for QRP-Labs PA mating

## Migration plan

Once bench prototypes validate the V0.2 schematic, the KiCad migration will:

1. Create symbols for any non-standard components (E22-900M30S module,
   QRP-Labs PA mating connector, BN43-7051 binocular)
2. Draw schematics matching the Markdown documentation
3. Layout PCBs with attention to RF best practices (microstrip, shielding,
   star grounding)
4. Generate Gerbers for JLCPCB 5-piece prototype lots
5. Validate first prototype against the bench procedures in `tests/bench/`
