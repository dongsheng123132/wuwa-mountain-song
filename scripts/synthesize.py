"""
《呜哇·迎客来》纯器乐 demo 合成器
================================

依据 docs/简谱.md，用 numpy + 标准库 wave 合成 instrumental WAV。
不需要 ffmpeg、不需要外部音频库。Python 3.10+ + numpy 即可。

声部：
  suona  唢呐  方波 + 5Hz 颤音 + ADSR
  drum   大鼓  80Hz 衰减正弦 + 噪声
  gong   铜锣  5 频率金属合成 + 长 reverb tail
  kick   电子底鼓  60Hz 衰减正弦 + 紧促包络
  pad    和声铺底  多正弦叠加

调式：F 徵调式 (1=F)，BPM 92。
段落：Intro 8 + Verse1 16 + Pre 8 + Hook 16 + Hook 16 + Outro 8 = 72 拍 ≈ 47 秒

输出：audio/instrumental-demo.wav (16-bit stereo PCM, 44.1 kHz)
"""

from __future__ import annotations
import wave
import struct
from pathlib import Path
import numpy as np

# ---------------------------------------------------------------- #
# 全局参数
# ---------------------------------------------------------------- #
SR = 44100                    # 采样率
BPM = 92
BEAT = 60.0 / BPM             # 一拍秒数 ≈ 0.652
MASTER_GAIN = 0.85            # 防削波

# F 徵调式音高 (Hz)。简谱数字 → 频率
NOTES = {
    '0':       0.0,             # 休止
    '5_low':   174.61,          # F3 sol (低音)
    '6_low':   196.00,          # G3 la
    '7_low':   220.00,          # A3 si
    '1':       261.63,          # C4 do
    '2':       293.66,          # D4 re
    '3':       329.63,          # E4 mi
    '5':       349.23,          # F4 sol (主音)
    '6':       392.00,          # G4 la
    '1_hi':    523.25,          # C5 do
    '2_hi':    587.33,          # D5 re
    '3_hi':    659.25,          # E5 mi
}

OUTPUT = Path(__file__).resolve().parent.parent / "audio" / "instrumental-demo.wav"


# ---------------------------------------------------------------- #
# 包络与基础工具
# ---------------------------------------------------------------- #
def adsr(n: int, a: float = 0.05, d: float = 0.1, s: float = 0.7, r: float = 0.2) -> np.ndarray:
    """简易 ADSR 包络。a/d/r 是相对长度（占比）"""
    if n <= 0:
        return np.array([])
    na = max(1, int(n * a))
    nd = max(1, int(n * d))
    nr = max(1, int(n * r))
    ns = max(1, n - na - nd - nr)
    env = np.concatenate([
        np.linspace(0, 1, na),
        np.linspace(1, s, nd),
        np.full(ns, s),
        np.linspace(s, 0, nr),
    ])
    # 长度修正
    if len(env) < n:
        env = np.concatenate([env, np.zeros(n - len(env))])
    return env[:n]


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(SR * seconds))


# ---------------------------------------------------------------- #
# 合成器声部
# ---------------------------------------------------------------- #
def suona(freq: float, dur: float, vol: float = 0.5) -> np.ndarray:
    """唢呐：方波 + 颤音 + 高次谐波 + ADSR"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    vibrato = 1 + 0.025 * np.sin(2 * np.pi * 5.5 * t)        # 5.5 Hz 颤音
    f = freq * vibrato
    # 方波 + 谐波叠加
    phase = 2 * np.pi * np.cumsum(f) / SR
    wave_arr = (
        np.sign(np.sin(phase)) * 0.55                         # 主方波
        + np.sin(phase * 2) * 0.25                            # 二次谐波
        + np.sin(phase * 3) * 0.15                            # 三次谐波
        + np.sin(phase * 4) * 0.08                            # 四次谐波
    )
    env = adsr(n, a=0.03, d=0.05, s=0.85, r=0.15)
    return wave_arr * env * vol


def suona_call(freq: float, dur: float, vol: float = 0.6) -> np.ndarray:
    """唢呐拖音呼号（Intro/Outro 用）：长 attack，慢颤"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    vibrato = 1 + 0.04 * np.sin(2 * np.pi * 4.0 * t)
    f = freq * vibrato
    phase = 2 * np.pi * np.cumsum(f) / SR
    wave_arr = (
        np.sign(np.sin(phase)) * 0.5
        + np.sin(phase * 2) * 0.3
        + np.sin(phase * 3) * 0.12
    )
    env = adsr(n, a=0.18, d=0.15, s=0.75, r=0.35)
    return wave_arr * env * vol


def drum(dur: float = 0.35, vol: float = 0.7) -> np.ndarray:
    """大鼓：80Hz 衰减正弦 + 短噪声 + 快衰减"""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    pitch = 90 * np.exp(-12 * t)                              # 频率从 90 衰减
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR)
    noise = np.random.randn(n) * np.exp(-25 * t) * 0.4
    env = np.exp(-8 * t)
    return (body * 0.7 + noise * 0.3) * env * vol


def kick(dur: float = 0.25, vol: float = 0.8) -> np.ndarray:
    """电子底鼓：60Hz 急速衰减"""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    pitch = 65 * np.exp(-25 * t)
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR)
    click = np.random.randn(n) * np.exp(-80 * t) * 0.15        # 起音 click
    env = np.exp(-12 * t)
    return (body + click) * env * vol


def gong(dur: float = 1.8, vol: float = 0.6) -> np.ndarray:
    """铜锣：多频金属 + 长尾"""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freqs = [180, 290, 410, 580, 770, 1050, 1450]
    weights = [1.0, 0.7, 0.55, 0.4, 0.3, 0.2, 0.12]
    wave_arr = np.zeros(n)
    for f, w in zip(freqs, weights):
        wave_arr += w * np.sin(2 * np.pi * f * t + np.random.rand() * 2 * np.pi)
    wave_arr /= sum(weights)
    # 起音 attack 噪声 + 长衰减
    attack_noise = np.random.randn(n) * np.exp(-30 * t) * 0.3
    env = np.exp(-1.8 * t)
    return (wave_arr + attack_noise) * env * vol


def pad(freq: float, dur: float, vol: float = 0.25) -> np.ndarray:
    """和声 pad：多个相邻正弦叠加，慢 attack/release"""
    if freq <= 0 or dur <= 0:
        return silence(dur)
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    detunes = [1.0, 1.005, 0.995, 1.5]   # 八度+轻微失谐
    wave_arr = sum(np.sin(2 * np.pi * freq * d * t) for d in detunes) / len(detunes)
    env = adsr(n, a=0.25, d=0.1, s=0.85, r=0.3)
    return wave_arr * env * vol


def wuwa_chant(dur: float, vol: float = 0.4) -> np.ndarray:
    """模拟「呜哇」合唱：滤波噪声 + 元音 formant 粗近似（无 voice 模型，仅暗示）"""
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    # 「呜」段 (前半):低 formant，模拟 'u'
    half = n // 2
    f1u, f2u = 300, 800     # 'u' 元音的 F1/F2
    u_part = (
        np.sin(2 * np.pi * f1u * t[:half]) * 0.5
        + np.sin(2 * np.pi * f2u * t[:half]) * 0.3
    )
    # 「哇」段 (后半):高 formant，模拟 'a'
    f1a, f2a = 750, 1300
    a_part = (
        np.sin(2 * np.pi * f1a * t[half:]) * 0.5
        + np.sin(2 * np.pi * f2a * t[half:]) * 0.3
    )
    wave_arr = np.concatenate([u_part, a_part])
    # 加点噪声给"人声感"
    wave_arr += np.random.randn(n) * 0.05
    env = adsr(n, a=0.1, d=0.1, s=0.8, r=0.2)
    return wave_arr * env * vol


# ---------------------------------------------------------------- #
# 节奏与编曲：把声部按时间排上轨
# ---------------------------------------------------------------- #
def mix_at(track: np.ndarray, sample: np.ndarray, start_sec: float):
    """把 sample 加到 track 的 start_sec 位置（in-place）"""
    start = int(start_sec * SR)
    end = start + len(sample)
    if end > len(track):
        sample = sample[: len(track) - start]
        end = len(track)
    if start >= len(track):
        return
    track[start:end] += sample


def render_intro(track: np.ndarray, t0: float) -> float:
    """Intro 8 拍 ≈ 5.2s。唢呐独奏远山呼号（| 6 - 5 3 | 5 - 3 2 | 3 - 2 1 | 6 - - - |）"""
    # 简谱: 6,5,3 / 5,3,2 / 3,2,1 / 6 长拖
    melody = [
        ('6', 1.0), ('5', 1.0), ('3', 1.0), ('0', 1.0),
        ('5', 1.0), ('3', 1.0), ('2', 1.0), ('0', 1.0),
        ('3', 1.0), ('2', 1.0), ('1', 1.0), ('0', 1.0),
        ('6', 4.0),
    ]
    cur = t0
    for note, beats in melody:
        dur = beats * BEAT
        if note != '0':
            mix_at(track, suona_call(NOTES[note], dur, vol=0.55), cur)
        cur += dur
    return cur


def render_verse1(track: np.ndarray, t0: float) -> float:
    """Verse1 16 拍 ≈ 10.4s。唢呐主旋律 + 弱鼓垫底"""
    # 来自简谱:虎形山上/火一塘/竹楼里头/客来访/红裙银泡/笑盈盈/长鼓敲开/八方郎
    melody = [
        # 「虎形山上,火一塘」
        ('5', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('5', 0.5),
        ('3', 0.5), ('2', 0.5), ('0', 1.0),
        # 「竹楼里头,客来访」
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('0', 1.0),
        ('3', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 2.0),
    ]
    cur = t0
    melody_start = cur
    for note, beats in melody:
        dur = beats * BEAT
        if note != '0':
            mix_at(track, suona(NOTES[note], dur, vol=0.45), cur)
        cur += dur

    # 弱鼓:每拍一个轻鼓
    for i in range(16):
        beat_t = melody_start + i * BEAT
        if i % 4 in (0, 2):
            mix_at(track, drum(dur=0.25, vol=0.3), beat_t)
    return cur


def render_pre(track: np.ndarray, t0: float) -> float:
    """Pre-Chorus 8 拍 ≈ 5.2s。鼓点渐进 + 旋律预告"""
    melody = [
        # 「举起酒——抬起头——」
        ('0', 0.5), ('5', 0.5), ('5', 0.5), ('6', 0.5),
        ('1_hi', 1.0), ('1_hi', 1.0),
        # 「唱给远方的——朋友听——」
        ('3', 0.5), ('3', 0.5), ('5', 0.5), ('6', 0.5),
        ('5', 1.0), ('3', 1.0),
    ]
    cur = t0
    melody_start = cur
    for note, beats in melody:
        dur = beats * BEAT
        if note != '0':
            mix_at(track, suona(NOTES[note], dur, vol=0.5), cur)
        cur += dur

    # 鼓点渐进：4 拍弱 → 4 拍强
    for i in range(8):
        beat_t = melody_start + i * BEAT
        vol = 0.3 + i * 0.06
        mix_at(track, drum(dur=0.3, vol=vol), beat_t)
        if i >= 4:
            # 后半加电子底鼓
            mix_at(track, kick(dur=0.25, vol=0.5), beat_t)
    return cur


def render_hook(track: np.ndarray, t0: float, with_synth: bool = True) -> float:
    """副歌 ★ 16 拍 ≈ 10.4s。全编制：唢呐主旋律 + 大鼓 + 锣 + 电子底鼓 + 呜哇合唱"""
    # 来自简谱:呜哇呜哇呜→呜哇!呜哇!呜哇咧→迎客来!迎客来!花瑶迎客来→山再高 路再长 不挡咱情长
    melody = [
        # 第 1-4 拍:「呜——哇——呜哇呜哇呜——」拖腔
        ('6', 1.5), ('1_hi', 1.5),
        ('6', 0.5), ('5', 0.5), ('6', 0.5), ('1_hi', 0.5),
        ('6', 1.0),
        # 第 5-8 拍:「呜哇! 呜哇! 呜哇咧——」三连击
        ('6', 0.5), ('5', 0.5), ('0', 0.5),     # 呜哇!
        ('6', 0.5), ('5', 0.5), ('0', 0.5),     # 呜哇!
        ('6', 0.5), ('5', 0.5), ('3', 1.0),     # 呜哇咧
        ('5', 1.0),
        # 第 9-12 拍:「迎客来! 迎客来! 花瑶迎客来!」
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('5', 0.5), ('6', 0.5), ('1_hi', 1.0),
        ('3', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 0.5), ('5', 0.5),
        # 第 13-16 拍:「山再高 路再长 不挡咱情长」
        ('6', 1.0), ('5', 0.5), ('3', 0.5),
        ('5', 1.0), ('3', 0.5), ('2', 0.5),
        ('1', 0.5), ('2', 0.5), ('3', 0.5), ('5', 0.5),
        ('6', 1.0), ('5', 1.0),
    ]
    cur = t0
    hook_start = cur
    for note, beats in melody:
        dur = beats * BEAT
        if note != '0':
            mix_at(track, suona(NOTES[note], dur, vol=0.55), cur)
        cur += dur

    # 大鼓 + 电子底鼓:four-on-floor 每拍一击
    for i in range(16):
        beat_t = hook_start + i * BEAT
        mix_at(track, drum(dur=0.3, vol=0.55), beat_t)
        if with_synth:
            mix_at(track, kick(dur=0.25, vol=0.65), beat_t)

    # 锣:第 1, 9 拍各一击 (段落标记)
    mix_at(track, gong(dur=2.0, vol=0.5), hook_start + 0)
    mix_at(track, gong(dur=2.0, vol=0.5), hook_start + 8 * BEAT)

    # 「呜哇」合唱:第 5、6、7 拍三连击位置
    mix_at(track, wuwa_chant(0.45, vol=0.35), hook_start + 4 * BEAT)
    mix_at(track, wuwa_chant(0.45, vol=0.35), hook_start + 5 * BEAT)
    mix_at(track, wuwa_chant(1.0, vol=0.35), hook_start + 6 * BEAT)

    # Pad 和声铺底（主音 5 持续）
    pad_dur = 16 * BEAT
    mix_at(track, pad(NOTES['5'] / 2, pad_dur, vol=0.18), hook_start)  # 低八度
    mix_at(track, pad(NOTES['1'], pad_dur, vol=0.12), hook_start)

    return cur


def render_outro(track: np.ndarray, t0: float) -> float:
    """Outro 8 拍 ≈ 5.2s。唢呐拖音 + 一声锣 + 渐弱"""
    melody = [
        ('6', 2.0), ('5', 2.0),
        ('3', 2.0), ('5', 2.0),
    ]
    cur = t0
    outro_start = cur
    for note, beats in melody:
        dur = beats * BEAT
        if note != '0':
            mix_at(track, suona_call(NOTES[note], dur, vol=0.5), cur)
        cur += dur

    # 收尾锣
    mix_at(track, gong(dur=3.0, vol=0.55), outro_start)
    return cur


# ---------------------------------------------------------------- #
# 立体声 & 极简 reverb
# ---------------------------------------------------------------- #
def simple_reverb(mono: np.ndarray, mix: float = 0.18, decay: float = 0.4) -> np.ndarray:
    """5 抽头 comb-filter 风格的廉价混响。够用即可。"""
    delays = [int(SR * d) for d in (0.029, 0.041, 0.067, 0.089, 0.113)]
    out = mono.copy()
    for i, d in enumerate(delays):
        gain = decay ** (i + 1)
        delayed = np.zeros_like(mono)
        delayed[d:] = mono[:-d] * gain
        out += delayed * mix
    return out


def to_stereo(mono: np.ndarray, width: float = 0.15) -> np.ndarray:
    """单声道 → 立体声，加微小延迟扩展"""
    delay_samples = int(SR * 0.012)
    left = mono.copy()
    right = np.concatenate([np.zeros(delay_samples), mono[:-delay_samples]])
    # 左右轻微 EQ 分离感（粗暴混音）
    return np.stack([left, right], axis=1)


# ---------------------------------------------------------------- #
# WAV 写入
# ---------------------------------------------------------------- #
def write_wav(path: Path, stereo: np.ndarray, sr: int = SR) -> None:
    """16-bit PCM WAV"""
    # 归一化
    peak = np.max(np.abs(stereo))
    if peak > 0:
        stereo = stereo / peak * MASTER_GAIN
    # 转 int16
    pcm = (stereo * 32767).astype(np.int16)
    interleaved = pcm.flatten()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)        # 16-bit = 2 bytes
        w.setframerate(sr)
        w.writeframes(interleaved.tobytes())


# ---------------------------------------------------------------- #
# 主流程
# ---------------------------------------------------------------- #
def main() -> None:
    # 总长度估算:Intro 8 + Verse1 16 + Pre 8 + Hook 16 + Hook 16 + Outro 8 = 72 拍 + 收尾
    total_beats = 72 + 4
    total_dur = total_beats * BEAT
    n_total = int(total_dur * SR)
    track = np.zeros(n_total)

    print(f"[*] 渲染中… 总长度 ≈ {total_dur:.1f}s")
    cursor = 0.0
    cursor = render_intro(track, cursor);     print(f"  Intro     end @ {cursor:.2f}s")
    cursor = render_verse1(track, cursor);    print(f"  Verse1    end @ {cursor:.2f}s")
    cursor = render_pre(track, cursor);       print(f"  Pre       end @ {cursor:.2f}s")
    cursor = render_hook(track, cursor);      print(f"  Hook 1    end @ {cursor:.2f}s")
    cursor = render_hook(track, cursor);      print(f"  Hook 2    end @ {cursor:.2f}s")
    cursor = render_outro(track, cursor);     print(f"  Outro     end @ {cursor:.2f}s")

    print("[*] 加混响…")
    track = simple_reverb(track, mix=0.16, decay=0.35)

    print("[*] 立体声化…")
    stereo = to_stereo(track)

    print(f"[*] 写入 {OUTPUT} …")
    write_wav(OUTPUT, stereo)

    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"[OK] 完成: {OUTPUT.name}  {size_mb:.1f} MB  时长 {total_dur:.1f}s")


if __name__ == "__main__":
    import sys, io
    # 让 Windows GBK 终端也能正常打印
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    main()
