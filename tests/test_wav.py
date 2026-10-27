"""Tests for ocean_sound.wav.

Every fixture is SYNTHETIC: generated tones and hand-built headers written to a temporary directory at test time.
No audio file is committed and nothing here is research evidence.
"""

import math
import os
import struct
import tempfile
import unittest
import wave

from ocean_sound.wav import WavError, decode_pcm, read_wav


def encode_pcm(frames, sample_width):
    """Pack interleaved signed ints as little-endian PCM, independently of the reader's decoder."""
    if sample_width == 2:
        return struct.pack("<%dh" % len(frames), *frames)
    if sample_width == 3:
        return b"".join((v & 0xFFFFFF).to_bytes(3, "little") for v in frames)
    raise ValueError(sample_width)


def write_wav(path, channels_data, sample_width, sample_rate=16000):
    """Write a SYNTHETIC WAV file from per-channel lists of signed ints."""
    channels = len(channels_data)
    frame_count = len(channels_data[0]) if channels_data else 0
    interleaved = [channels_data[c][i] for i in range(frame_count) for c in range(channels)]
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        w.writeframes(encode_pcm(interleaved, sample_width))


def sine(frequency, seconds, sample_rate, amplitude):
    n = int(round(seconds * sample_rate))
    return [int(round(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))) for i in range(n)]


class WavReaderTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def test_16bit_round_trip_known_values(self):
        values = [0, 1, -1, 32767, -32768, 12345, -12345]
        p = self.path("synthetic_16.wav")
        write_wav(p, [values], 2)
        data = read_wav(p)
        self.assertEqual(data.sample_width, 2)
        self.assertEqual(data.bits, 16)
        self.assertEqual(data.samples, [values])

    def test_24bit_round_trip_known_values(self):
        values = [0, 1, -1, 8388607, -8388608, 1234567, -1234567, 256, -256]
        p = self.path("synthetic_24.wav")
        write_wav(p, [values], 3)
        data = read_wav(p)
        self.assertEqual(data.sample_width, 3)
        self.assertEqual(data.bits, 24)
        self.assertEqual(data.samples, [values])

    def test_24bit_sign_extension_of_raw_bytes(self):
        raw = b"\x00\x00\x80" + b"\xff\xff\x7f" + b"\xff\xff\xff" + b"\x01\x00\x00"
        self.assertEqual(decode_pcm(raw, 3), [-8388608, 8388607, -1, 1])

    def test_mono_16khz_24bit_metadata(self):
        p = self.path("synthetic_mono.wav")
        write_wav(p, [sine(440, 0.5, 16000, 2 ** 22)], 3, sample_rate=16000)
        data = read_wav(p)
        self.assertEqual(data.channels, 1)
        self.assertEqual(data.sample_rate, 16000)
        self.assertEqual(data.frame_count, 8000)
        self.assertEqual(len(data.samples), 1)
        self.assertEqual(len(data.samples[0]), 8000)

    def test_stereo_channels_deinterleaved(self):
        left = [100, 200, 300, -400]
        right = [-1, -2, -3, 4]
        p = self.path("synthetic_stereo.wav")
        write_wav(p, [left, right], 2)
        data = read_wav(p)
        self.assertEqual(data.channels, 2)
        self.assertEqual(data.frame_count, 4)
        self.assertEqual(data.samples, [left, right])

    def test_stereo_24bit(self):
        left = [8388607, 0, -5]
        right = [-8388608, 7, 5]
        p = self.path("synthetic_stereo_24.wav")
        write_wav(p, [left, right], 3)
        self.assertEqual(read_wav(p).samples, [left, right])

    def test_exact_duration_of_one_second_tone(self):
        p = self.path("synthetic_1s.wav")
        write_wav(p, [sine(1000, 1.0, 16000, 10000)], 2, sample_rate=16000)
        data = read_wav(p)
        self.assertEqual(data.frame_count, 16000)
        self.assertEqual(data.duration_seconds, 1.0)

    def test_peak_and_rms_of_square_wave_16bit(self):
        square = [16384 if (i // 8) % 2 == 0 else -16384 for i in range(1600)]
        p = self.path("synthetic_square_16.wav")
        write_wav(p, [square], 2)
        data = read_wav(p)
        self.assertEqual(data.peak(), 0.5)
        self.assertAlmostEqual(data.rms(), 0.5, places=12)

    def test_peak_and_rms_of_square_wave_24bit(self):
        square = [2 ** 21 if (i // 4) % 2 == 0 else -(2 ** 21) for i in range(800)]
        p = self.path("synthetic_square_24.wav")
        write_wav(p, [square], 3)
        data = read_wav(p)
        self.assertEqual(data.peak(), 0.25)
        self.assertAlmostEqual(data.rms(), 0.25, places=12)

    def test_sine_rms_close_to_amplitude_over_root_two(self):
        p = self.path("synthetic_sine.wav")
        write_wav(p, [sine(100, 1.0, 16000, 16000)], 2)
        data = read_wav(p)
        self.assertAlmostEqual(data.rms(), (16000 / 32768) / math.sqrt(2), places=4)

    def test_truncated_file_rejected(self):
        p = self.path("synthetic_truncated.wav")
        write_wav(p, [sine(440, 0.1, 16000, 1000)], 2)
        size = os.path.getsize(p)
        with open(p, "r+b") as f:
            f.truncate(size - 100)
        with self.assertRaises(WavError) as ctx:
            read_wav(p)
        self.assertIn("truncated", str(ctx.exception))

    def test_truncated_header_rejected(self):
        p = self.path("synthetic_header_only.wav")
        write_wav(p, [[1, 2, 3]], 2)
        with open(p, "r+b") as f:
            f.truncate(20)
        with self.assertRaises(WavError):
            read_wav(p)

    def test_empty_data_chunk_rejected(self):
        p = self.path("synthetic_empty.wav")
        write_wav(p, [[]], 2)
        with self.assertRaises(WavError) as ctx:
            read_wav(p)
        self.assertIn("empty", str(ctx.exception))

    def test_zero_length_file_rejected(self):
        p = self.path("synthetic_zero_bytes.wav")
        open(p, "wb").close()
        with self.assertRaises(WavError):
            read_wav(p)

    def test_non_pcm_format_rejected(self):
        # SYNTHETIC IEEE float (format tag 3) header with one 32-bit sample.
        fmt = struct.pack("<HHIIHH", 3, 1, 16000, 64000, 4, 32)
        body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", 4) + b"\x00" * 4
        p = self.path("synthetic_float.wav")
        with open(p, "wb") as f:
            f.write(b"RIFF" + struct.pack("<I", len(body)) + body)
        with self.assertRaises(WavError):
            read_wav(p)

    def test_non_wav_file_rejected(self):
        p = self.path("synthetic_not_wav.wav")
        with open(p, "wb") as f:
            f.write(b"SYNTHETIC not a wav file at all" * 4)
        with self.assertRaises(WavError):
            read_wav(p)

    def test_unsupported_sample_width_rejected(self):
        p = self.path("synthetic_8bit.wav")
        with wave.open(p, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(1)
            w.setframerate(8000)
            w.writeframes(b"\x80\x81\x7f")
        with self.assertRaises(WavError):
            read_wav(p)


if __name__ == "__main__":
    unittest.main()
