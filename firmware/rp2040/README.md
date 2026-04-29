# RP2040 Firmware

Skeleton firmware for the Card 5 supervisor. Currently only `main.c` is
implemented as a structural placeholder; the module headers (`config.h`,
`coherence.h`, etc.) and their implementations are TBD.

## Build

```bash
mkdir build && cd build
cmake .. -DPICO_SDK_PATH=/path/to/pico-sdk
make -j
```

## Status

- ✅ State machine skeleton (`main.c`)
- 🚧 Module headers
- 🚧 Coherence driver (Si5351 + ADF4351)
- 🚧 SX1262 driver
- 🚧 IHM driver (OLED + encoder + buttons)
- 🚧 Safety driver (watchdog kick, fault detection)
- 🚧 Logging driver (USB host, FAT FS via CH376S)
- ⏳ PIO PPS capture
- ⏳ TinyUSB host integration

## Alternative: MicroPython

For initial PoC, MicroPython is acceptable. See `firmware/rp2040/micropython/`
(future) for a higher-level prototype implementation.
