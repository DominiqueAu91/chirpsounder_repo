# Receiver architecture — ka9q-radio backend (V0.3)

V0.3 replaces the direct-SDR receivers of V0.2 (ANTSDR E200, Hermes-Lite 2,
RTL-SDR + upconverter) with the **wsprdaemon reference hardware** running
**ka9q-radio**:

```text
HF antenna
   |
   v
RX888 MkII  (16-bit direct sampling, 64.8 Msps)
   |  27 MHz ext. reference from GPSDO  (frequency discipline)
   v
Beelink miniPC — Ubuntu Server 24.04 LTS
   |  gpsd + chrony on GPSDO 1PPS       (time-of-day discipline)
   v
radiod  (ka9q-radio: fast-convolution filterbank, ttl=0 multicast)
   |
   +--> chirp-iq.local, SSRC 5001  — IQ channel, 96 kHz, f32le
   |        |
   |        +--> software/ka9q-backend/chirp_tracker.py   (sweep tracking)
   |        +--> gr-chirpsounder ka9q_iq_source block     (GNU Radio)
   |
   +--> wspr-pcm.local — the same box keeps serving wsprdaemon
```

## Rationale

1. **One box, many instruments.** radiod demodulates hundreds of channels
   from a single A/D stream. The chirpsounder receiver coexists with a full
   wsprdaemon installation on the same RX888 — the marginal hardware cost of
   the sounder RX is zero for the many stations already running this stack.
2. **Coherence for free.** The RX888 external 27 MHz reference is disciplined
   by the station GPSDO; every radiod channel inherits GPS frequency accuracy,
   matching design principle 1 (coherence by construction) on the RX side.
3. **Standard ProAm platform.** HamSCI/wsprdaemon already documents sourcing,
   assembly and tuning of exactly this hardware, lowering the entry barrier
   for network nodes.

## Two reception modes

### Mode A — fixed channel (SX1262 sounder on 30 m, CODAR)

The project's own transmitter emits short repeating chirps of bandwidth
7.8–500 kHz around 10.1 MHz. One **static** radiod IQ channel covers this
entirely — no retuning. The stream feeds either the reference pipeline
(`software/examples/dechirp_basic.py`, unchanged) or the `gr-chirpsounder`
flowgraph through the `ka9q_iq_source` block.

Channel setup (dynamic, from the shell):

```sh
tune --radio hf.local --ssrc 5001 --mode iq --samprate 96k \
     --encoding f32le --low -46k --high +46k \
     --destination chirp-iq.local --frequency 10m120
```

### Mode B — swept channel (opportunity illuminators, 2–30 MHz)

Military/ionospheric sweepers chirp the whole HF band at typically
50–125 kHz/s. Behind radiod the raw 64.8 Msps stream is neither available
nor needed: `chirp_tracker.py` implements a **stepped-LO tracking
receiver** — the 96 kHz channel is retuned by 48 kHz every 0.48 s
(at 100 kHz/s) with the ka9q-radio `tune` utility, and each dwell is
dechirped independently against the synthetic zero-delay reference.

Stretch-processing identity: a path of group delay τ appears after dechirp
as a tone at −Rτ (R = chirp rate). Per-dwell STFT columns assemble directly
into the ionogram.

| Quantity | Expression | Default value |
|----------|-----------|---------------|
| Dwell duration | (B/2)/R | 0.48 s (B = 96 kHz, R = 100 kHz/s) |
| Delay resolution | 1/(R·T_win) | 100 µs → 15 km one-way (T_win = 0.1 s) |
| Doppler-induced delay error | f_d/R | 10 µs per Hz |
| Retune guard (discarded) | ≥ 2 radiod blocks | 50 ms |

radiod retunes are **not phase-continuous**; this is irrelevant because
dwells are processed independently. The DSP chain is validated offline by
`software/ka9q-backend/test_dechirp_sim.py` (two-path synthetic ionosphere,
delays recovered to within one FFT bin).

## Timing discipline — frequency vs time-of-day

The GPSDO disciplines the RX888 **sample clock** (chirp-rate match, Doppler
integrity). It does **not** set the host **time-of-day**, which maps delay to
absolute range: a wallclock error of 1 ms shifts the whole ionogram by
300 km of one-way virtual range. Requirements:

- gpsd + chrony with the GPSDO 1PPS as refclock → host time to ~1–10 µs;
- the residual constant bias (radiod pipeline latency, 1–2 × 20 ms blocks,
  plus USB buffering) is calibrated once with `--tau-bias` against a sounder
  of known location;
- proper removal via radiod RTP timestamps + GPS time from the status stream
  is planned for the GNU Radio phase (stream tags on retune boundaries).

## Implementation facts (verified against ka9q-radio sources, 2026-07)

- radiod **creates channels dynamically** when a `tune` command addresses an
  unknown SSRC (`data =` must be set in `[global]`). Static config sections
  force SSRC = freq/kHz and do not accept a manual SSRC — hence no static
  chirp section in `radiod@chirp.conf`.
- Default channel encoding is **s16be**; V0.3 pins `f32le` everywhere.
- The `iq` preset defaults to ±5 kHz filter edges; the tracker must override
  with `--low/--high` (±46 kHz for a 96 kHz channel) or 90 % of the channel
  is silently discarded.
- `pcmrecord --stdout --raw --ssrc N group` handles all RTP reassembly and
  emits headerless f32le stereo (I = left, Q = right) — the Phase 1 capture
  path contains zero RTP code. The GNU Radio block parses RTP natively
  (RFC 3550) with zero-fill on sequence gaps.

## Files

| Path | Role |
|------|------|
| `software/ka9q-backend/radiod@chirp.conf` | radiod configuration (RX888 @ 64.8 Msps) |
| `software/ka9q-backend/chirp_tracker.py` | Mode B sweep tracker (tune + pcmrecord) |
| `software/ka9q-backend/dechirp_sweep.py` | Mode B segments → ionogram |
| `software/ka9q-backend/test_dechirp_sim.py` | Offline validation of the Mode B chain |
| `software/gr-chirpsounder/python/ka9q_iq_source.py` | GNU Radio source block |

## Deprecated in V0.3

The V0.2 receiver options remain *possible* (any SDR feeding
`dechirp_basic.py` still works) but are no longer the reference platform:

- ANTSDR E200 — no longer required; USRP-class capture path dropped.
- Hermes-Lite 2 — superseded by RX888 direct sampling.
- RTL-SDR + upconverter — insufficient dynamic range for a network node.
