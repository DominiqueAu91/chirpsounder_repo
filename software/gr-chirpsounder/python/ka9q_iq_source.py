#!/usr/bin/env python3
"""
ka9q_iq_source -- GNU Radio source block for ka9q-radio multicast IQ.

Drop-in replacement for the osmocom/UHD/soapy source planned in V0.2
for gr-chirpsounder. Joins the radiod data multicast group, parses
RTP (RFC 3550 fixed header + CSRC/extension skip), filters on SSRC and
emits complex64.

radiod payload formats supported (set per channel or via `tune -e`):
    f32le : interleaved little-endian float32 I,Q   (recommended)
    s16le : interleaved little-endian int16   I,Q
    s16be : interleaved big-endian    int16   I,Q   (radiod default!)

Notes
-----
* radiod payload types are allocated dynamically (PT 77..127); the
  authoritative PT->encoding mapping is announced on the status stream.
  For a single-purpose chirp channel it is simpler and robust to pin
  the encoding on the radiod side (encoding = f32le or tune -e f32le)
  and configure the same value here.
* Sequence-number gaps are zero-filled so downstream timing (sample
  counting) stays consistent.
* Retunes commanded with `tune` do not interrupt the stream; the block
  keeps producing. Tag-based center-frequency annotation from the
  status stream is a Phase 2 TODO (see docs/architecture/rx-ka9q.md).

Usage in GRC: add an "Embedded Python Block" and paste this class, or
install as a module and instantiate:

    src = ka9q_iq_source(group="chirp-iq.local", port=5004,
                         ssrc=5001, encoding="f32le")

Added in V0.3 (ka9q-radio receiver backend).
License: GPL-3.0-or-later
"""

import socket
import struct

import numpy as np
from gnuradio import gr


class ka9q_iq_source(gr.sync_block):
    def __init__(
        self,
        group="chirp-iq.local",
        port=5004,
        ssrc=5001,
        encoding="f32le",
        iface_ip="0.0.0.0",
    ):
        gr.sync_block.__init__(
            self, name="ka9q_iq_source", in_sig=None, out_sig=[np.complex64]
        )
        self.ssrc = int(ssrc)
        self.encoding = encoding
        if encoding == "f32le":
            self._dtype, self._scale = np.dtype("<f4"), 1.0
        elif encoding == "s16le":
            self._dtype, self._scale = np.dtype("<i2"), 1.0 / 32768.0
        elif encoding == "s16be":
            self._dtype, self._scale = np.dtype(">i2"), 1.0 / 32768.0
        else:
            raise ValueError("encoding must be f32le, s16le or s16be")

        # resolve group (mDNS .local via avahi, or literal IP)
        gaddr = socket.getaddrinfo(group, port, socket.AF_INET, socket.SOCK_DGRAM)[0][
            4
        ][0]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", port))
        mreq = struct.pack("4s4s", socket.inet_aton(gaddr), socket.inet_aton(iface_ip))
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
        s.settimeout(2.0)
        self.sock = s

        self._residual = np.zeros(0, dtype=np.complex64)
        self._last_seq = None
        self._drops = 0

    # ---- RTP ---------------------------------------------------------
    def _parse_rtp(self, pkt):
        if len(pkt) < 12:
            return None
        b0, b1, seq, ts, ssrc = struct.unpack("!BBHII", pkt[:12])
        if (b0 >> 6) != 2:  # RTP version
            return None
        if ssrc != self.ssrc:
            return None
        off = 12 + 4 * (b0 & 0x0F)  # skip CSRC list
        if b0 & 0x10:  # header extension
            if len(pkt) < off + 4:
                return None
            _, xlen = struct.unpack("!HH", pkt[off : off + 4])
            off += 4 + 4 * xlen
        if b0 & 0x20:  # padding
            pkt = pkt[: len(pkt) - pkt[-1]]
        return seq, pkt[off:]

    def _payload_to_iq(self, payload):
        a = np.frombuffer(payload, dtype=self._dtype)
        a = a[: (len(a) // 2) * 2].astype(np.float32) * self._scale
        return (a[0::2] + 1j * a[1::2]).astype(np.complex64)

    # ---- GNU Radio ----------------------------------------------------
    def work(self, input_items, output_items):
        out = output_items[0]
        n_out = 0
        # serve residual first
        if len(self._residual):
            n = min(len(out), len(self._residual))
            out[:n] = self._residual[:n]
            self._residual = self._residual[n:]
            n_out = n
        while n_out < len(out):
            try:
                pkt = self.sock.recv(9000)
            except socket.timeout:
                break  # let the scheduler breathe
            r = self._parse_rtp(pkt)
            if r is None:
                continue
            seq, payload = r
            iq = self._payload_to_iq(payload)
            if self._last_seq is not None:
                gap = (seq - self._last_seq - 1) & 0xFFFF
                if 0 < gap < 100:  # zero-fill small gaps
                    iq = np.concatenate([np.zeros(gap * len(iq), np.complex64), iq])
                    self._drops += gap
            self._last_seq = seq
            n = min(len(out) - n_out, len(iq))
            out[n_out : n_out + n] = iq[:n]
            self._residual = iq[n:]
            n_out += n
        return n_out

    def stop(self):
        self.sock.close()
        return True
