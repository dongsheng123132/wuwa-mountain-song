"""
多版本器乐 demo 合成器 (v2-v6)
================================

复用 synthesize.py 中的声部函数，按 5 个版本不同的 BPM/编曲/段落
组合输出 wav 到 audio/variants/。

输出：
  v2-douyin.wav  18s  BPM 128  纯电子+chant
  v3-folk.wav    2:30  BPM 78  唢呐+鼓+人声，无电子
  v4-ballad.wav  3:30  BPM 72  钢琴+弦乐+唢呐 solo
  v5-duet.wav    4:00  BPM 88  木吉他+中阮对唱长版
  v6-world.wav   3:20  BPM 100 Tribal+world，对标 Jerusalema

依赖：numpy（与 synthesize.py 相同）
"""
from __future__ import annotations
import wave
import sys
import io
from pathlib import Path
import numpy as np

# 导入主合成器中的声部
sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthesize import (
    NOTES, SR, MASTER_GAIN,
    adsr, silence,
    suona, suona_call, drum, kick, gong, pad, wuwa_chant,
    mix_at, simple_reverb, to_stereo, write_wav,
)

OUT_DIR = Path(__file__).resolve().parent.parent / "audio" / "variants"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================== #
# 新声部（变体专用）
# ============================================================== #

def piano(freq: float, dur: float, vol: float = 0.45) -> np.ndarray:
    """钢琴：基音 + 谐波 + 指数衰减（v4 抒情版用）"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    body = (
        np.sin(2 * np.pi * freq * t) * 0.6
        + np.sin(2 * np.pi * freq * 2 * t) * 0.3
        + np.sin(2 * np.pi * freq * 3 * t) * 0.12
        + np.sin(2 * np.pi * freq * 4 * t) * 0.06
    )
    env = np.exp(-2.0 * t) * (1 - np.exp(-50 * t))
    return body * env * vol


def strings(freq: float, dur: float, vol: float = 0.3) -> np.ndarray:
    """弦乐：多正弦轻微失谐 + 慢 attack（v4 v5 用）"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    detunes = [1.0, 1.003, 0.997, 2.0, 0.5]
    weights = [1.0, 0.5, 0.5, 0.25, 0.4]
    wave_arr = np.zeros(n)
    for d, w in zip(detunes, weights):
        wave_arr += w * np.sin(2 * np.pi * freq * d * t)
    wave_arr /= sum(weights)
    env = adsr(n, a=0.18, d=0.1, s=0.85, r=0.25)
    return wave_arr * env * vol


def guitar(freq: float, dur: float, vol: float = 0.4) -> np.ndarray:
    """木吉他指弹：谐波 + 拨弦 attack + 中速衰减（v5 用）"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    body = (
        np.sin(2 * np.pi * freq * t) * 0.5
        + np.sin(2 * np.pi * freq * 2 * t) * 0.25
        + np.sin(2 * np.pi * freq * 3 * t) * 0.15
        + np.sin(2 * np.pi * freq * 4 * t) * 0.08
        + np.sin(2 * np.pi * freq * 5 * t) * 0.04
    )
    pluck = np.random.randn(n) * np.exp(-180 * t) * 0.2
    env = np.exp(-3.0 * t)
    return (body + pluck) * env * vol


def zhongruan(freq: float, dur: float, vol: float = 0.4) -> np.ndarray:
    """中阮：三角波 + 谐波，弹拨感（v5 用）"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    phase = 2 * np.pi * freq * t
    triangle = (2 / np.pi) * np.arcsin(np.sin(phase))
    body = triangle * 0.5 + np.sin(phase * 2) * 0.2 + np.sin(phase * 3) * 0.1
    env = np.exp(-4.0 * t) * (1 - np.exp(-80 * t))
    return body * env * vol


def tribal_drum(dur: float = 0.4, vol: float = 0.7) -> np.ndarray:
    """部落鼓：低中频复合 + 慢衰减（v6 用，对标 Jerusalema）"""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    pitch = 70 * np.exp(-6 * t)
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR)
    mid = np.sin(2 * np.pi * 180 * t) * np.exp(-15 * t) * 0.3
    noise = np.random.randn(n) * np.exp(-20 * t) * 0.25
    env = np.exp(-5 * t)
    return (body * 0.65 + mid + noise) * env * vol


def synth_pad(freq: float, dur: float, vol: float = 0.22) -> np.ndarray:
    """合成器 pad：宽 detune + 慢动态（v2 v6 用）"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    saws = []
    for d in [0.99, 1.0, 1.01, 1.5, 2.0]:
        phase = 2 * np.pi * freq * d * t
        saw = 2 * (phase / (2 * np.pi) - np.floor(0.5 + phase / (2 * np.pi)))
        # 低通近似：累加平滑
        saw = np.convolve(saw, np.ones(20) / 20, mode='same')
        saws.append(saw)
    wave_arr = sum(saws) / len(saws)
    env = adsr(n, a=0.3, d=0.15, s=0.85, r=0.4)
    return wave_arr * env * vol


def synth_stab(freq: float, dur: float = 0.2, vol: float = 0.5) -> np.ndarray:
    """合成器短促 stab（v2 用，副歌爆发）"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    phase = 2 * np.pi * freq * t
    saw = 2 * (phase / (2 * np.pi) - np.floor(0.5 + phase / (2 * np.pi)))
    sub = np.sin(2 * np.pi * freq / 2 * t) * 0.3
    env = np.exp(-8 * t)
    return (saw + sub) * env * vol


def hihat(dur: float = 0.08, vol: float = 0.25) -> np.ndarray:
    """高帽：白噪声 + 高通近似 + 急速衰减"""
    n = int(SR * dur)
    noise = np.random.randn(n)
    # 高通近似：差分
    noise = np.diff(noise, prepend=0)
    env = np.exp(-40 * np.linspace(0, dur, n, endpoint=False))
    return noise * env * vol


# ============================================================== #
# v2 抖音 15s 嗨爆版
# ============================================================== #
def render_v2_douyin() -> np.ndarray:
    """v2: 18 秒 / BPM 128 / 纯电子 + chant + 锣 + 唢呐 stab
       结构: 4 拍 build → 8 拍 hook × 2 + 收尾"""
    bpm = 128
    beat = 60.0 / bpm
    total_dur = 18.0
    track = np.zeros(int(total_dur * SR))

    # ---- 0-4 拍 Build-up (1.875s) ----
    build_start = 0.0
    # 渐进 hihat 16 分音符 + 锣一击 + 上升 synth pad
    for i in range(16):
        t = build_start + i * (beat / 4)
        v = 0.1 + i * 0.025
        mix_at(track, hihat(0.06, vol=v), t)
    mix_at(track, gong(2.0, vol=0.55), build_start + 3.5 * beat)
    # 上升音 pad
    rise = synth_pad(NOTES['5'], 4 * beat, vol=0.3)
    mix_at(track, rise, build_start)

    # ---- 4 拍后 Drop / Hook 1 (8 拍 ≈ 3.75s) ----
    h1_start = 4 * beat
    # 简谱 hook melody (压缩到 8 拍)：呜哇 呜哇 呜哇咧 / 迎客来 迎客来 花瑶迎客来
    melody = [
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('3', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
    ]
    cur = h1_start
    for note, b in melody:
        d = b * beat
        if note != '0':
            mix_at(track, synth_stab(NOTES[note], d * 0.95, vol=0.45), cur)
            mix_at(track, suona(NOTES[note], d * 0.9, vol=0.35), cur)
        cur += d

    # 8 拍 four-on-floor kick + 锣每 4 拍
    for i in range(8):
        t = h1_start + i * beat
        mix_at(track, kick(0.18, vol=0.85), t)
        # 反拍 hihat
        mix_at(track, hihat(0.05, vol=0.3), t + beat / 2)
    mix_at(track, gong(1.5, vol=0.45), h1_start)

    # 「呜哇」chant 三连击在第 1-3 拍
    for i in range(3):
        mix_at(track, wuwa_chant(0.35, vol=0.45), h1_start + i * beat)

    # synth pad 持续低音
    mix_at(track, synth_pad(NOTES['5'] / 2, 8 * beat, vol=0.25), h1_start)

    # ---- Hook 2 (8 拍) ----
    h2_start = h1_start + 8 * beat
    # 「干一杯！干一杯！米酒满满杯」
    melody2 = [
        ('5', 0.5), ('6', 0.5), ('5', 1.0),
        ('5', 0.5), ('6', 0.5), ('5', 1.0),
        ('1_hi', 0.5), ('6', 0.5), ('5', 0.5), ('3', 0.5),
        ('5', 1.0), ('6', 1.0),
    ]
    cur = h2_start
    for note, b in melody2:
        d = b * beat
        if note != '0':
            mix_at(track, synth_stab(NOTES[note], d * 0.95, vol=0.5), cur)
            mix_at(track, suona(NOTES[note], d * 0.9, vol=0.4), cur)
        cur += d

    for i in range(8):
        t = h2_start + i * beat
        mix_at(track, kick(0.18, vol=0.9), t)
        mix_at(track, hihat(0.05, vol=0.32), t + beat / 2)
    mix_at(track, gong(1.5, vol=0.45), h2_start)
    for i in range(3):
        mix_at(track, wuwa_chant(0.35, vol=0.5), h2_start + i * beat)
    mix_at(track, synth_pad(NOTES['5'] / 2, 8 * beat, vol=0.25), h2_start)

    # ---- 收尾 1 拍 ----
    final_t = h2_start + 8 * beat
    mix_at(track, gong(2.0, vol=0.6), final_t)
    mix_at(track, kick(0.3, vol=0.7), final_t)
    mix_at(track, suona_call(NOTES['5'], 1.2, vol=0.35), final_t)

    return track


# ============================================================== #
# v3 纯民族原生版
# ============================================================== #
def render_v3_folk() -> np.ndarray:
    """v3: 2:30 / BPM 78 / 唢呐+长鼓+锣+笛，无电子
       结构: Intro(自由) → Verse(rubato) → Pre → Hook → Verse → Hook → Outro"""
    bpm = 78
    beat = 60.0 / bpm
    total_dur = 150.0
    track = np.zeros(int(total_dur * SR))
    cur = 0.0

    # ---- Intro 自由速度唢呐 8 拍 (~6.2s) ----
    intro_melody = [
        ('6', 1.5), ('5', 1.0), ('3', 1.0),
        ('5', 1.5), ('3', 1.0), ('2', 1.0),
        ('3', 2.0), ('6_low', 4.0),
    ]
    for note, b in intro_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona_call(NOTES[note], d * 1.1, vol=0.55), cur)
        cur += d

    # ---- Verse 1 男声叙事 16 拍 ----
    verse_melody = [
        ('5', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('5', 0.5),
        ('3', 0.5), ('2', 0.5), ('0', 1.0),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 2.0),
    ]
    verse_start = cur
    for note, b in verse_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona(NOTES[note], d, vol=0.42), cur)
        cur += d
    # 弱长鼓每 2 拍一击
    for i in range(8):
        mix_at(track, drum(0.4, vol=0.32), verse_start + i * 2 * beat)

    # ---- Pre 8 拍 长鼓+大锣进入节拍 ----
    pre_melody = [
        ('0', 0.5), ('5', 0.5), ('5', 0.5), ('6', 0.5),
        ('1_hi', 1.0), ('1_hi', 1.0),
        ('3', 0.5), ('3', 0.5), ('5', 0.5), ('6', 0.5),
        ('5', 1.0), ('3', 1.0),
    ]
    pre_start = cur
    for note, b in pre_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona(NOTES[note], d, vol=0.5), cur)
        cur += d
    for i in range(8):
        mix_at(track, drum(0.35, vol=0.4 + i * 0.04), pre_start + i * beat)
    mix_at(track, gong(2.0, vol=0.5), pre_start)
    mix_at(track, gong(2.0, vol=0.5), pre_start + 4 * beat)

    # ---- Hook 16 拍（无电子，纯民族）----
    cur = render_folk_hook(track, cur, beat)

    # ---- Verse 2 女声 16 拍（同 verse）----
    verse2_start = cur
    for note, b in verse_melody:
        d = b * beat
        if note != '0':
            # 高八度模拟女声
            f = NOTES[note] * 1.5 if NOTES[note] > 0 else 0
            mix_at(track, suona(f, d, vol=0.4), cur)
        cur += d
    for i in range(8):
        mix_at(track, drum(0.4, vol=0.3), verse2_start + i * 2 * beat)

    # ---- Hook 16 拍 (升一档)----
    cur = render_folk_hook(track, cur, beat, female=True)

    # ---- Outro 8 拍 + 收尾 ----
    outro_melody = [
        ('6', 2.0), ('5', 2.0),
        ('3', 2.0), ('6_low', 4.0),
    ]
    outro_start = cur
    for note, b in outro_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona_call(NOTES[note], d, vol=0.5), cur)
        cur += d
    mix_at(track, gong(3.5, vol=0.55), outro_start)

    return track


def render_folk_hook(track, t0, beat, female=False) -> float:
    """纯民族 hook：唢呐+长鼓+锣+笛，无电子底鼓"""
    melody = [
        ('6', 1.5), ('1_hi', 1.5),
        ('6', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('3', 1.0),
        ('5', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('3', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 0.5), ('3', 0.5),
        ('5', 1.0), ('3', 0.5), ('2', 0.5),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 1.0),
    ]
    cur = t0
    hook_start = cur
    for note, b in melody:
        d = b * beat
        if note != '0':
            f = NOTES[note] * (1.5 if female else 1.0) if NOTES[note] > 0 else 0
            mix_at(track, suona(f, d, vol=0.5), cur)
        cur += d
    # 长鼓每拍
    for i in range(16):
        mix_at(track, drum(0.35, vol=0.5), hook_start + i * beat)
    # 锣段落标记
    mix_at(track, gong(2.5, vol=0.55), hook_start)
    mix_at(track, gong(2.5, vol=0.55), hook_start + 8 * beat)
    # 「呜哇」合唱（无电子，纯人声暗示）
    mix_at(track, wuwa_chant(0.5, vol=0.4), hook_start + 4 * beat)
    mix_at(track, wuwa_chant(0.5, vol=0.4), hook_start + 5 * beat)
    mix_at(track, wuwa_chant(1.0, vol=0.4), hook_start + 6 * beat)
    return cur


# ============================================================== #
# v4 抒情家国情怀版
# ============================================================== #
def render_v4_ballad() -> np.ndarray:
    """v4: 3:30 / BPM 72 / 钢琴+弦乐+唢呐 solo
       结构: Intro钢琴 → Verse → Pre → Hook → Verse → Hook → Bridge → Final Hook 升 key → Outro"""
    bpm = 72
    beat = 60.0 / bpm
    total_dur = 215.0
    track = np.zeros(int(total_dur * SR))
    cur = 0.0

    # ---- Intro 钢琴 8 拍 ----
    intro_chords = [
        ('1', 2.0), ('5_low', 2.0),
        ('6_low', 2.0), ('5', 2.0),
    ]
    intro_start = cur
    for note, b in intro_chords:
        d = b * beat
        if note != '0':
            mix_at(track, piano(NOTES[note], d, vol=0.45), cur)
            mix_at(track, piano(NOTES[note] * 2, d, vol=0.25), cur)
        cur += d
    # Intro 末尾远音呼号
    mix_at(track, suona_call(NOTES['6'], 3.0, vol=0.3), intro_start + 6 * beat)

    # ---- Verse 1 钢琴+弦乐 16 拍 ----
    verse_melody = [
        ('5', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('5', 0.5),
        ('3', 0.5), ('2', 0.5), ('0', 1.0),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 2.0),
    ]
    verse_start = cur
    for note, b in verse_melody:
        d = b * beat
        if note != '0':
            mix_at(track, piano(NOTES[note], d, vol=0.4), cur)
        cur += d
    # 弦乐持续 chord pad
    chord_notes = ['1', '5', '3']
    for ch in chord_notes:
        mix_at(track, strings(NOTES[ch], 16 * beat, vol=0.18), verse_start)

    # ---- Pre 8 拍 弦乐渐强+唢呐入 ----
    pre_melody = [
        ('0', 0.5), ('5', 0.5), ('5', 0.5), ('6', 0.5),
        ('1_hi', 1.0), ('1_hi', 1.0),
        ('3', 0.5), ('3', 0.5), ('5', 0.5), ('6', 0.5),
        ('5', 1.0), ('3', 1.0),
    ]
    pre_start = cur
    for note, b in pre_melody:
        d = b * beat
        if note != '0':
            mix_at(track, piano(NOTES[note], d, vol=0.4), cur)
            if NOTES[note] > 0:
                mix_at(track, suona(NOTES[note], d * 0.8, vol=0.25), cur)
        cur += d
    mix_at(track, strings(NOTES['1'], 8 * beat, vol=0.22), pre_start)
    mix_at(track, strings(NOTES['5'], 8 * beat, vol=0.22), pre_start)

    # ---- Hook 16 拍 抒情演绎 ----
    cur = render_ballad_hook(track, cur, beat, key_shift=1.0)

    # ---- Verse 2 16 拍 ----
    verse2_start = cur
    for note, b in verse_melody:
        d = b * beat
        if note != '0':
            mix_at(track, piano(NOTES[note] * 1.3, d, vol=0.4), cur)
        cur += d
    for ch in chord_notes:
        mix_at(track, strings(NOTES[ch] * 1.5, 16 * beat, vol=0.2), verse2_start)

    # ---- Hook 16 拍 ----
    cur = render_ballad_hook(track, cur, beat, key_shift=1.0)

    # ---- Bridge 16 拍 弦乐独白 ----
    bridge_melody = [
        ('5', 1.5), ('6', 1.0), ('1_hi', 1.5),
        ('1_hi', 2.0), ('6', 2.0),
        ('3_hi', 1.5), ('1_hi', 1.0), ('6', 1.5),
        ('5', 4.0),
    ]
    bridge_start = cur
    for note, b in bridge_melody:
        d = b * beat
        if note != '0':
            mix_at(track, strings(NOTES[note], d * 1.05, vol=0.4), cur)
            mix_at(track, piano(NOTES[note], d, vol=0.25), cur)
        cur += d

    # ---- Final Hook 升半度 16 拍 ----
    cur = render_ballad_hook(track, cur, beat, key_shift=1.06)

    # ---- Outro 8 拍 ----
    outro_chords = [('5', 4.0), ('1', 4.0)]
    outro_start = cur
    for note, b in outro_chords:
        d = b * beat
        if note != '0':
            mix_at(track, piano(NOTES[note], d, vol=0.4), cur)
            mix_at(track, strings(NOTES[note], d, vol=0.25), cur)
        cur += d
    mix_at(track, suona_call(NOTES['6'], 4.0, vol=0.3), outro_start)

    return track


def render_ballad_hook(track, t0, beat, key_shift=1.0) -> float:
    """抒情 hook：钢琴+弦乐+唢呐solo+轻底鼓"""
    melody = [
        ('6', 1.5), ('1_hi', 1.5),
        ('6', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('3', 1.0),
        ('5', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('3', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 0.5), ('3', 0.5),
        ('5', 1.0), ('3', 0.5), ('2', 0.5),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 1.0),
    ]
    cur = t0
    hook_start = cur
    for note, b in melody:
        d = b * beat
        if note != '0':
            f = NOTES[note] * key_shift if NOTES[note] > 0 else 0
            mix_at(track, piano(f, d, vol=0.42), cur)
            mix_at(track, suona(f, d * 0.95, vol=0.3), cur)
        cur += d
    # 弦乐铺底
    for ch in ['1', '5', '3']:
        mix_at(track, strings(NOTES[ch] * key_shift, 16 * beat, vol=0.2), hook_start)
    # 轻底鼓 每 2 拍一击
    for i in range(8):
        mix_at(track, drum(0.4, vol=0.3), hook_start + i * 2 * beat)
    # 「呜哇」合唱
    mix_at(track, wuwa_chant(0.6, vol=0.3), hook_start + 4 * beat)
    mix_at(track, wuwa_chant(0.6, vol=0.3), hook_start + 5 * beat)
    mix_at(track, wuwa_chant(1.2, vol=0.3), hook_start + 6 * beat)
    return cur


# ============================================================== #
# v5 男女对唱故事版
# ============================================================== #
def render_v5_duet() -> np.ndarray:
    """v5: 4:00 / BPM 88 / 木吉他+中阮+唢呐+长鼓
       结构: Intro吉他 → V1男 → V2女 → Pre → Hook → V3男 → V4女 → Bridge → Final Hook"""
    bpm = 88
    beat = 60.0 / bpm
    total_dur = 240.0
    track = np.zeros(int(total_dur * SR))
    cur = 0.0

    # ---- Intro 木吉他 8 拍 ----
    intro_pattern = [
        ('1', 0.5), ('3', 0.5), ('5', 0.5), ('1_hi', 0.5),
        ('5', 0.5), ('3', 0.5), ('1', 0.5), ('0', 0.5),
        ('5_low', 0.5), ('1', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 1.0),
    ]
    intro_start = cur
    for note, b in intro_pattern:
        d = b * beat
        if note != '0':
            mix_at(track, guitar(NOTES[note], d, vol=0.4), cur)
        cur += d
    mix_at(track, suona_call(NOTES['6'], 3.0, vol=0.3), intro_start + 6 * beat)

    # ---- Verse 1 男声 (低音区) 16 拍 ----
    verse_melody = [
        ('5', 0.5), ('5', 0.5), ('6', 0.5), ('5', 0.5),
        ('3', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('5', 0.5),
        ('3', 0.5), ('2', 0.5), ('1', 1.0),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('5', 0.5),
        ('3', 2.0),
    ]
    cur = render_duet_verse(track, cur, beat, verse_melody, voice='male')

    # ---- Verse 2 女声 (高音区) 16 拍 ----
    cur = render_duet_verse(track, cur, beat, verse_melody, voice='female')

    # ---- Pre 8 拍 长鼓进入 ----
    pre_melody = [
        ('0', 0.5), ('5', 0.5), ('5', 0.5), ('6', 0.5),
        ('1_hi', 1.0), ('1_hi', 1.0),
        ('3', 0.5), ('3', 0.5), ('5', 0.5), ('6', 0.5),
        ('5', 1.0), ('3', 1.0),
    ]
    pre_start = cur
    for note, b in pre_melody:
        d = b * beat
        if note != '0':
            mix_at(track, guitar(NOTES[note], d, vol=0.4), cur)
            mix_at(track, zhongruan(NOTES[note], d, vol=0.3), cur)
        cur += d
    for i in range(8):
        mix_at(track, drum(0.35, vol=0.35 + i * 0.04), pre_start + i * beat)

    # ---- Hook 16 拍 男女轮答 ----
    cur = render_duet_hook(track, cur, beat)

    # ---- Verse 3 男声延展 16 拍 ----
    cur = render_duet_verse(track, cur, beat, verse_melody, voice='male')

    # ---- Verse 4 女声 16 拍 ----
    cur = render_duet_verse(track, cur, beat, verse_melody, voice='female')

    # ---- Bridge 16 拍 真假声转换 ----
    bridge_melody = [
        ('5', 1.5), ('3', 1.0), ('1', 1.5),
        ('1_hi', 2.0), ('6', 2.0),
        ('3_hi', 1.5), ('2_hi', 1.0), ('1_hi', 1.5),
        ('6', 4.0),
    ]
    bridge_start = cur
    for note, b in bridge_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona(NOTES[note], d * 1.05, vol=0.45), cur)
            mix_at(track, strings(NOTES[note], d * 1.05, vol=0.3), cur)
            mix_at(track, zhongruan(NOTES[note], d, vol=0.25), cur)
        cur += d
    for i in range(8):
        mix_at(track, drum(0.35, vol=0.4), bridge_start + i * 2 * beat)

    # ---- Final Hook 全员合唱 16 拍 ----
    cur = render_duet_hook(track, cur, beat, full=True)

    # ---- Outro 6 拍 ----
    outro_pattern = [('6', 2.0), ('5', 2.0), ('1', 2.0)]
    outro_start = cur
    for note, b in outro_pattern:
        d = b * beat
        if note != '0':
            mix_at(track, guitar(NOTES[note], d, vol=0.4), cur)
            mix_at(track, suona_call(NOTES[note], d, vol=0.3), cur)
        cur += d

    return track


def render_duet_verse(track, t0, beat, melody, voice='male') -> float:
    cur = t0
    verse_start = cur
    pitch_shift = 1.5 if voice == 'female' else 1.0
    for note, b in melody:
        d = b * beat
        if note != '0':
            f = NOTES[note] * pitch_shift if NOTES[note] > 0 else 0
            # 主旋律用 zhongruan 暗示人声音区
            mix_at(track, zhongruan(f, d, vol=0.4), cur)
        # 木吉他底色
        if note != '0':
            mix_at(track, guitar(NOTES[note], d * 0.9, vol=0.25), cur)
        cur += d
    # 弱长鼓
    n_beats = int((cur - verse_start) / beat)
    for i in range(0, n_beats, 2):
        mix_at(track, drum(0.4, vol=0.25), verse_start + i * beat)
    return cur


def render_duet_hook(track, t0, beat, full=False) -> float:
    melody = [
        ('6', 1.5), ('1_hi', 1.5),
        ('6', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('3', 1.0),
        ('5', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('3', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 0.5), ('3', 0.5),
        ('5', 1.0), ('3', 0.5), ('2', 0.5),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 1.0),
    ]
    cur = t0
    hook_start = cur
    # 男女轮答：奇数 phrase 男（低音区），偶数 phrase 女（高音区）
    phrase_idx = 0
    accumulated_beats = 0.0
    for note, b in melody:
        d = b * beat
        # 每 2 拍切换男/女
        is_female = int(accumulated_beats / 2) % 2 == 1
        pitch = 1.5 if is_female else 1.0
        if note != '0':
            f = NOTES[note] * pitch if NOTES[note] > 0 else 0
            mix_at(track, suona(f, d * 0.95, vol=0.45), cur)
            mix_at(track, zhongruan(NOTES[note], d, vol=0.25), cur)
        cur += d
        accumulated_beats += b
    # 长鼓每拍
    for i in range(16):
        v = 0.55 if full else 0.45
        mix_at(track, drum(0.3, vol=v), hook_start + i * beat)
    if full:
        for i in range(16):
            mix_at(track, kick(0.2, vol=0.4), hook_start + i * beat)
    # 锣
    mix_at(track, gong(2.5, vol=0.5), hook_start)
    mix_at(track, gong(2.5, vol=0.5), hook_start + 8 * beat)
    # 「呜哇」合唱
    for i, off in enumerate([4, 5, 6]):
        d = 1.0 if off == 6 else 0.5
        mix_at(track, wuwa_chant(d, vol=0.4), hook_start + off * beat)
    return cur


# ============================================================== #
# v6 跨语言世界版（对标 Jerusalema）
# ============================================================== #
def render_v6_world() -> np.ndarray:
    """v6: 3:20 / BPM 100 / Tribal drums + Suona + Synth pad + Bass
       结构: Intro tribal → Verse → Pre → Hook → Verse → Hook → Bridge → Final → Outro"""
    bpm = 100
    beat = 60.0 / bpm
    total_dur = 200.0
    track = np.zeros(int(total_dur * SR))
    cur = 0.0

    # ---- Intro Tribal drums fade-in 8 拍 ----
    intro_start = cur
    for i in range(8):
        v = 0.3 + i * 0.06
        mix_at(track, tribal_drum(0.5, vol=v), intro_start + i * beat)
    mix_at(track, suona_call(NOTES['6'], 4.0, vol=0.3), intro_start + 4 * beat)
    cur += 8 * beat

    # ---- Verse 1 16 拍 ----
    verse_melody = [
        ('5', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('5', 0.5),
        ('3', 0.5), ('2', 0.5), ('0', 1.0),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 2.0),
    ]
    verse_start = cur
    for note, b in verse_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona(NOTES[note], d, vol=0.4), cur)
        cur += d
    # bass + tribal drums 每拍
    for i in range(16):
        mix_at(track, tribal_drum(0.4, vol=0.5), verse_start + i * beat)
    mix_at(track, synth_pad(NOTES['5'] / 2, 16 * beat, vol=0.2), verse_start)

    # ---- Pre 8 拍 ----
    pre_melody = [
        ('0', 0.5), ('5', 0.5), ('5', 0.5), ('6', 0.5),
        ('1_hi', 1.0), ('1_hi', 1.0),
        ('3', 0.5), ('3', 0.5), ('5', 0.5), ('6', 0.5),
        ('5', 1.0), ('3', 1.0),
    ]
    pre_start = cur
    for note, b in pre_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona(NOTES[note], d, vol=0.45), cur)
            mix_at(track, synth_stab(NOTES[note], d * 0.7, vol=0.25), cur)
        cur += d
    for i in range(8):
        mix_at(track, tribal_drum(0.4, vol=0.55), pre_start + i * beat)
        mix_at(track, kick(0.2, vol=0.5), pre_start + i * beat)

    # ---- Hook 16 拍 中英混合 ----
    cur = render_world_hook(track, cur, beat)

    # ---- Verse 2 16 拍 ----
    verse2_start = cur
    for note, b in verse_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona(NOTES[note] * 1.3, d, vol=0.38), cur)
        cur += d
    for i in range(16):
        mix_at(track, tribal_drum(0.4, vol=0.5), verse2_start + i * beat)
    mix_at(track, synth_pad(NOTES['5'] / 2, 16 * beat, vol=0.22), verse2_start)

    # ---- Hook 16 拍 ----
    cur = render_world_hook(track, cur, beat)

    # ---- Bridge 16 拍 假声 + 英文呼号 ----
    bridge_melody = [
        ('1_hi', 1.5), ('2_hi', 1.0), ('3_hi', 1.5),
        ('3_hi', 2.0), ('1_hi', 2.0),
        ('6', 1.5), ('5', 1.0), ('3', 1.5),
        ('5', 4.0),
    ]
    bridge_start = cur
    for note, b in bridge_melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona(NOTES[note], d * 1.05, vol=0.5), cur)
            mix_at(track, synth_pad(NOTES[note], d * 1.05, vol=0.25), cur)
        cur += d
    # 「呜哇」chant 在 bridge 中段
    for i, off in enumerate([2, 6, 10]):
        mix_at(track, wuwa_chant(0.6, vol=0.4), bridge_start + off * beat)

    # ---- Final Hook 16 拍 全员爆发 ----
    cur = render_world_hook(track, cur, beat, full=True)

    # ---- Outro 8 拍 drum fade out ----
    outro_start = cur
    for i in range(8):
        v = 0.5 - i * 0.05
        mix_at(track, tribal_drum(0.4, vol=v), outro_start + i * beat)
    mix_at(track, suona_call(NOTES['6'], 4.0, vol=0.3), outro_start)

    return track


def render_world_hook(track, t0, beat, full=False) -> float:
    melody = [
        ('6', 1.5), ('1_hi', 1.5),
        ('6', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('0', 0.5),
        ('6', 0.5), ('5', 0.5), ('3', 1.0),
        ('5', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('3', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 0.5), ('3', 0.5),
        ('5', 1.0), ('3', 0.5), ('2', 0.5),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 1.0),
    ]
    cur = t0
    hook_start = cur
    for note, b in melody:
        d = b * beat
        if note != '0':
            mix_at(track, suona(NOTES[note], d * 0.95, vol=0.5), cur)
            mix_at(track, synth_stab(NOTES[note], d * 0.5, vol=0.25), cur)
        cur += d
    # tribal drums + kick four-on-floor
    for i in range(16):
        mix_at(track, tribal_drum(0.4, vol=0.6 if full else 0.55), hook_start + i * beat)
        mix_at(track, kick(0.2, vol=0.7 if full else 0.55), hook_start + i * beat)
        if i % 2 == 1:
            mix_at(track, hihat(0.05, vol=0.25), hook_start + i * beat)
    # 锣
    mix_at(track, gong(2.0, vol=0.5), hook_start)
    mix_at(track, gong(2.0, vol=0.5), hook_start + 8 * beat)
    # synth pad bass
    mix_at(track, synth_pad(NOTES['5'] / 2, 16 * beat, vol=0.25), hook_start)
    # 「呜哇」chant
    for i, off in enumerate([4, 5, 6]):
        d = 1.0 if off == 6 else 0.5
        mix_at(track, wuwa_chant(d, vol=0.45), hook_start + off * beat)
    return cur


# ============================================================== #
# 后处理 + 写文件
# ============================================================== #
def finalize(track: np.ndarray, reverb_mix=0.16, decay=0.35) -> np.ndarray:
    track = simple_reverb(track, mix=reverb_mix, decay=decay)
    return to_stereo(track)


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    versions = [
        ('v2-douyin.wav',  render_v2_douyin,  0.10, 0.30),
        ('v3-folk.wav',    render_v3_folk,    0.22, 0.45),
        ('v4-ballad.wav',  render_v4_ballad,  0.25, 0.45),
        ('v5-duet.wav',    render_v5_duet,    0.18, 0.38),
        ('v6-world.wav',   render_v6_world,   0.15, 0.35),
    ]

    for fname, render_fn, rmix, rdecay in versions:
        out = OUT_DIR / fname
        print(f'[*] Rendering {fname}...')
        track = render_fn()
        stereo = finalize(track, reverb_mix=rmix, decay=rdecay)
        write_wav(out, stereo)
        size_mb = out.stat().st_size / 1024 / 1024
        dur = len(track) / SR
        print(f'    -> {out.name}  {size_mb:.1f}MB  {dur:.1f}s')
    print('[OK] all variants rendered')


if __name__ == '__main__':
    main()
