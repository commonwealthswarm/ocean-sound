"""Dependency-free WAV reader for 16-bit and 24-bit integer PCM.

Uses the standard library ``wave`` module for the container and decodes the sample bytes by hand (24-bit values are
sign-extended manually). Measurements are in full-scale units: a sample value divided by 2 ** (bits - 1), so a
full-scale negative sample is -1.0. Nothing here interprets audio content; it only reads and measures it.
"""

import math
import struct
import wave
from dataclasses import dataclass
from typing import List, Sequence

SUPPORTED_SAMPLE_WIDTHS = (2, 3)


class WavError(ValueError):
    """The file is not a readable, complete 16-bit or 24-bit integer PCM WAV file."""


@dataclass(frozen=True)
class WavData:
    sample_rate: int
    channels: int
    sample_width: int  # bytes per sample: 2 (16-bit) or 3 (24-bit)
    frame_count: int
    samples: List[List[int]]  # samples[channel][frame], signed integers

    @property
    def bits(self) -> int:
        return self.sample_width * 8

    @property
    def duration_seconds(self) -> float:
        return self.frame_count / self.sample_rate

    @property
    def full_scale(self) -> int:
        return 1 << (self.bits - 1)

    def peak(self) -> float:
        """Largest absolute sample value over all channels, in full-scale units."""
        return max(abs(v) for channel in self.samples for v in channel) / self.full_scale

    def rms(self) -> float:
        """Root mean square over all channels and frames, in full-scale units."""
        total = 0
        count = 0
        for channel in self.samples:
            total += sum(v * v for v in channel)
            count += len(channel)
        return math.sqrt(total / count) / self.full_scale


def decode_pcm(raw: bytes, sample_width: int) -> List[int]:
    """Decode little-endian signed integer PCM bytes into a flat list of ints."""
    if sample_width not in SUPPORTED_SAMPLE_WIDTHS:
        raise WavError("unsupported sample width: %d bytes (only 16-bit and 24-bit PCM)" % sample_width)
    if len(raw) % sample_width:
        raise WavError("sample data length %d is not a multiple of the sample width %d" % (len(raw), sample_width))
    if sample_width == 2:
        return list(struct.unpack("<%dh" % (len(raw) // 2), raw))
    out = []
    for i in range(0, len(raw), 3):
        v = raw[i] | (raw[i + 1] << 8) | (raw[i + 2] << 16)
        if v & 0x800000:
            v -= 0x1000000
        out.append(v)
    return out


def deinterleave(flat: Sequence[int], channels: int) -> List[List[int]]:
    return [list(flat[c::channels]) for c in range(channels)]


def read_wav(path) -> WavData:
    """Read a 16-bit or 24-bit PCM WAV file. Raises WavError for non-PCM, empty or truncated files."""
    try:
        with wave.open(str(path), "rb") as w:
            if w.getcomptype() != "NONE":
                raise WavError("not PCM: compression type %r" % w.getcomptype())
            sample_rate = w.getframerate()
            channels = w.getnchannels()
            sample_width = w.getsampwidth()
            frame_count = w.getnframes()
            raw = w.readframes(frame_count)
    except WavError:
        raise
    except (wave.Error, EOFError, struct.error) as exc:
        raise WavError("not a readable PCM WAV file: %s" % exc) from exc
    if sample_width not in SUPPORTED_SAMPLE_WIDTHS:
        raise WavError("unsupported sample width: %d bytes (only 16-bit and 24-bit PCM)" % sample_width)
    if channels < 1:
        raise WavError("invalid channel count: %d" % channels)
    if sample_rate <= 0:
        raise WavError("invalid sample rate: %d" % sample_rate)
    if frame_count == 0:
        raise WavError("empty data chunk: no audio frames")
    expected = frame_count * channels * sample_width
    if len(raw) != expected:
        raise WavError("truncated file: data chunk declares %d bytes but only %d are present" % (expected, len(raw)))
    flat = decode_pcm(raw, sample_width)
    return WavData(
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
        frame_count=frame_count,
        samples=deinterleave(flat, channels),
    )
