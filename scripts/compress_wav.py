"""
把 audio/variants/ 里的 wav 文件压缩为更小体积：
- 立体声 → 单声道
- 44100 Hz → 22050 Hz
- 16-bit PCM 保留

体积下降 ~4 倍。对 demo 试听完全够用。
"""
from pathlib import Path
import wave
import struct
import numpy as np
from scipy import signal

VARIANTS_DIR = Path(__file__).resolve().parent.parent / "audio" / "variants"
TARGET_SR = 22050


def load_wav(path: Path):
    with wave.open(str(path), 'rb') as w:
        n_ch = w.getnchannels()
        sw = w.getsampwidth()
        sr = w.getframerate()
        n = w.getnframes()
        data = w.readframes(n)
    pcm = np.frombuffer(data, dtype=np.int16)
    if n_ch == 2:
        pcm = pcm.reshape(-1, 2)
    return pcm, sr, n_ch, sw


def save_wav(path: Path, mono_int16: np.ndarray, sr: int):
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(mono_int16.tobytes())


def main():
    for wav in sorted(VARIANTS_DIR.glob("*.wav")):
        pcm, sr, n_ch, sw = load_wav(wav)
        # to mono
        if n_ch == 2:
            mono = pcm.mean(axis=1).astype(np.float32)
        else:
            mono = pcm.astype(np.float32)
        # resample
        if sr != TARGET_SR:
            n_target = int(len(mono) * TARGET_SR / sr)
            mono_rs = signal.resample(mono, n_target)
        else:
            mono_rs = mono
        # back to int16
        peak = np.max(np.abs(mono_rs))
        if peak > 0:
            mono_rs = mono_rs / peak * 32000
        mono_int16 = mono_rs.astype(np.int16)
        # overwrite
        old_size = wav.stat().st_size / 1024 / 1024
        save_wav(wav, mono_int16, TARGET_SR)
        new_size = wav.stat().st_size / 1024 / 1024
        print(f'{wav.name}: {old_size:.1f}MB -> {new_size:.1f}MB')


if __name__ == "__main__":
    main()
