# 合成器使用说明

## 这是什么

`synthesize.py` 是一个**纯 Python（numpy + 标准库 wave）** 的简易音频合成器。
它根据 `docs/简谱.md` 的旋律和 `docs/编曲说明.md` 的编曲方案，生成纯器乐 demo。

**注意**：这是 chiptune 级别的器乐 demo，**不包含人声**。要做带人声的成品，请走 Suno/Udio 或真人录唱路线。

---

## 怎么跑

### 依赖
- Python 3.10+
- numpy（已在系统中）

### 运行
```bash
cd <仓库根目录>
python scripts/synthesize.py
```

输出：`audio/instrumental-demo.wav`（约 66 秒，立体声 16-bit / 44.1 kHz，约 8.3 MB）。

---

## 转 MP3（可选）

WAV 是无损但文件大。要 MP3 需要 ffmpeg：

```bash
# 已下载便携版到 scripts/bin/ffmpeg.exe
./scripts/bin/ffmpeg.exe -i audio/instrumental-demo.wav -b:a 192k audio/instrumental-demo.mp3

# 或全局安装的 ffmpeg
ffmpeg -i audio/instrumental-demo.wav -b:a 192k audio/instrumental-demo.mp3
```

`scripts/bin/` 目录已在 `.gitignore` 中，便携版工具不会进仓库。

---

## 自定义参数

打开 `synthesize.py`，可调：

| 参数 | 默认 | 说明 |
|---|---|---|
| `SR` | 44100 | 采样率 |
| `BPM` | 92 | 速度（拍每分钟） |
| `MASTER_GAIN` | 0.85 | 主音量（0-1） |
| `NOTES` | F 徵调式 | 改这里换调式 |

段落顺序在 `main()` 函数里改：
```python
cursor = render_intro(track, cursor)
cursor = render_verse1(track, cursor)
cursor = render_pre(track, cursor)
cursor = render_hook(track, cursor)      # 副歌
cursor = render_hook(track, cursor)      # 副歌重复
cursor = render_outro(track, cursor)
```

---

## 声部对照

| 函数 | 模拟 | 实现 |
|---|---|---|
| `suona()` | 唢呐 | 方波 + 5.5Hz 颤音 + 高次谐波 |
| `suona_call()` | 唢呐拖音呼号 | 长 attack 版 |
| `drum()` | 大鼓 / 瑶族长鼓 | 90Hz 衰减正弦 + 噪声 |
| `kick()` | 电子底鼓 | 65Hz 急速衰减 |
| `gong()` | 铜锣 | 7 频率金属合成 + 长尾 |
| `pad()` | 和声铺底 | 多正弦失谐叠加 |
| `wuwa_chant()` | 「呜哇」合唱（粗近似） | 元音 formant 模拟 |

---

## 已知局限

1. **没有人声**：合成器无法生成带歌词的演唱
2. **音色粗糙**：方波/正弦合成 ≠ 真乐器采样
3. **「呜哇」合唱**只是 formant 暗示，不像人在唱
4. **混响是廉价 5 抽头 comb-filter**，不是专业卷积混响

要做出能传播的成品，**必须**用此 demo 作为蓝图，对接：
- 真人花瑶歌手 + 真乐器录制
- 或 Suno / Udio / Mureka 等 AI 音乐生成工具

---

## 法律声明

本合成器代码及生成的音频均归《呜哇·迎客来》著作权人**贺去病AI工作室**所有，遵循根目录 [LICENSE](../LICENSE) 中的 All Rights Reserved 条款。

未经授权不得用于商业用途，不得用于训练 AI 模型。
