# 呜哇·迎客来 · 隆回花瑶迎宾曲

> 一首参考景颇族《目瑙纵歌》、植根于湖南隆回花瑶呜哇山歌、融合全球爆款迎宾曲公式的原创迎宾合唱。

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC_BY--SA_4.0-blue.svg)](LICENSE) [![Status](https://img.shields.io/badge/Status-Open_for_Contribution-brightgreen.svg)](#制作路线图) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**© 2026 贺去病AI工作室 (Hequbing AI Studio) · CC BY-SA 4.0 开源协议**

> 🌸 **欢迎花瑶族群、非遗传承人、音乐工作者、文化研究者参与协作！**
> 看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何贡献。

---

## 这是什么

《呜哇·迎客来》是一首**面向湖南隆回县虎形山花瑶**的原创迎宾曲。

- **源**：花瑶呜哇山歌（国家级非遗，2008）的「呜哇」高腔传统
- **形**：参考景颇族《目瑙纵歌》（国家级非遗，2024-2026 全网爆火）的合唱呼号结构
- **路**：吸收 Jerusalema、Waka Waka、Coco Jamboo 等全球爆款迎宾曲的传播公式
- **果**：可在迎宾仪式、文旅活动、抖音传播中使用的多场景作品

**目标**：做一首比《目瑙纵歌》更适合传播的隆回花瑶迎宾曲，用音乐让世界听到花瑶。

> 📖 **想知道怎么把这事真的推起来？** 看 [`PLAYBOOK.md`](PLAYBOOK.md)
> ——90 天执行手册，对齐 2026 年讨僚皈节窗口（2026-06-30 ~ 07-02）。

---

## 试听

| 文件 | 风格 | 时长 | 状态 |
|---|---|---|---|
| `audio/instrumental-demo.wav` | v1 原版 · 民族+电子混合 | ~47s | ✅ 已生成 |
| `audio/variants/v2-douyin.wav` | v2 抖音 15s 嗨爆版（BPM 128 纯电子） | 18s | ✅ 已生成 |
| `audio/variants/v3-folk.wav` | v3 纯民族原生版（BPM 78 唢呐+鼓+笛） | 2:30 | ✅ 已生成 |
| `audio/variants/v4-ballad.wav` | v4 抒情家国情怀版（BPM 72 钢琴+弦乐） | 3:35 | ✅ 已生成 |
| `audio/variants/v5-duet.wav` | v5 男女对唱故事版（BPM 88 木吉他+中阮） | 4:00 | ✅ 已生成 |
| `audio/variants/v6-world.wav` | v6 跨语言世界版（BPM 100 Tribal+Synth） | 3:20 | ✅ 已生成 |
| `audio/full-vocal-3min.mp3` | 真人录唱完整版 | 3:10 | ⬜ 待制作 |

> 📜 6 个版本各自的歌词、Suno 提示词、传播策略见 [`docs/lyrics-variants/`](docs/lyrics-variants/)。

> ⚠ **关于 instrumental-demo**：这是用 Python+numpy 合成的 chiptune 级别器乐 demo，约 66 秒，**不含人声**。仅作为编曲蓝图、节奏参考、给后续真人录唱或 AI 工具提供骨架。重新生成方式见 [`scripts/README.md`](scripts/README.md)。

---

## 项目结构

```
.
├── README.md                  本文件
├── LICENSE                    All Rights Reserved（保留全部权利）
├── .gitignore
├── docs/
│   ├── 歌词.md               中文 + 「呜哇」衬词版完整歌词
│   ├── 简谱.md               主旋律简谱（F 徵调式 BPM 92）
│   ├── 编曲说明.md            配器/段落/混音方案
│   ├── 创作笔记.md            爆款公式拆解 + 设计决策
│   └── suno-prompt.md         Suno AI 生成提示词
├── references/
│   └── 链接清单.md            参考曲目链接（学习用，不打包音频）
├── audio/
│   └── instrumental-demo.wav  自合成纯器乐 demo
├── scripts/
│   ├── synthesize.py          器乐 demo 合成器（numpy + wave）
│   └── README.md              如何重新生成 demo
├── video/
│   └── dance-tutorial.md      8 拍迎宾舞动作分解
├── contacts.md                协作邀请联系名单（投递地图）
├── outreach-letters/          按收件人分别成稿的邀请信
│   ├── 01-隆回县文旅局.md
│   ├── 02-虎形山瑶族乡政府.md
│   ├── 03-高校学术团队.md
│   ├── 04-花瑶KOL私信.md
│   └── 05-传承人私信.md
├── OUTREACH.md                通用邀请信模板与原则
├── ECOSYSTEM.md               三仓库生态总览
└── PLAYBOOK.md                ★ 爆款 90 天执行手册（核心战略）
```

---

## 创作背景

### 为什么是花瑶？

湖南邵阳隆回县虎形山瑶族乡是中国"花瑶"族群的核心聚居地。花瑶以**挑花刺绣**、**呜哇山歌**两项国家级非遗闻名，但在全国传播度上仍有提升空间。

### 为什么参考《目瑙纵歌》？

景颇族《目瑙纵歌》在 2024-2026 年通过抖音、视频号自发传播，登上全网热搜。它证明了：**国家级非遗 + 简单记忆点 + 真实生活感 = 病毒式传播**。这条路花瑶完全可以走。

### 为什么放眼全球？

Jerusalema、Waka Waka 这些全球爆款迎宾曲背后有一套通用公式：简单重复的副歌、配套舞蹈、跨语言衬词、视觉强符号。我们把这些公式"翻译"成花瑶版本。

完整的爆款公式拆解见 [`docs/创作笔记.md`](docs/创作笔记.md)。

---

## 快速试听 / 上手

### 1. 听 demo
直接双击 `audio/instrumental-demo.wav`（Windows Media Player / VLC / 浏览器都能播放）。

### 2. 看歌词
打开 [`docs/歌词.md`](docs/歌词.md)，朗读副歌核心 hook：

```
呜——哇——呜哇呜哇呜——
呜哇！呜哇！呜哇咧——
迎客来！迎客来！花瑶迎客来！
山再高 路再长 不挡咱情长
```

### 3. 重新合成 demo（修改参数）
修改 `scripts/synthesize.py` 中的 `BPM`、`KEY`、段落配置后：
```bash
python scripts/synthesize.py
```
覆盖输出 `audio/instrumental-demo.wav`。

### 4. 制作真人/AI 完整版
- **AI 路线**：用 [`docs/suno-prompt.md`](docs/suno-prompt.md) 中的提示词在 Suno/Udio/Mureka 上生成
- **真人路线**：把 `instrumental-demo.wav` 当 click track，邀请花瑶歌手或专业唱将进棚

---

## 制作路线图

- [x] 调研三大参考母本（目瑙纵歌、花瑶呜哇山歌、全球爆款迎宾曲）
- [x] 写歌词、简谱、编曲说明、8 拍迎宾舞分解
- [x] 写 Python 合成器 + 生成器乐 demo (instrumental-demo.wav)
- [ ] 生成 MP3 版本
- [ ] 真人或 AI 录制带人声完整版
- [ ] 制作抖音 15 秒切片版
- [ ] 拍摄迎宾舞教学视频
- [ ] 联合隆回县文旅局或非遗中心传播

---

## 授权 · License

**本作品采用 CC BY-SA 4.0 协议开源**

- ✅ 你可以**自由使用**、修改、再创作、**商用**
- ⚠ 必须**署名**（注明原作者贺去病AI工作室 + 仓库链接）
- ⚠ 修改/再创作版本必须**采用相同协议**开源（保持开放）

完整协议见 [LICENSE](LICENSE)。

### 协作与联系

**🌸 我们诚挚欢迎以下伙伴参与：**
- 花瑶族群成员、虎形山瑶族乡乡亲
- 呜哇山歌、花瑶挑花非遗传承人
- 隆回县文旅局、邵阳市文旅工作者
- 音乐制作人、编曲师、歌手
- 文化人类学/音乐学研究者
- AI 音乐工程师、合成器开发者

**怎么参与：**
1. **直接 Fork + Pull Request**（修订歌词、改进合成器、添加录唱版本）
2. **提 GitHub Issue**（指出错误、提供资料、提建议）
3. **联系工作室**：38004547@qq.com / HEFANGSHENG@gmail.com

**📬 想协助我们邀请相关方？**
联系名单见 [`contacts.md`](contacts.md)，按渠道分类的邀请信成稿见 [`outreach-letters/`](outreach-letters/)。
欢迎认领其中一封投递并把回执贴回 issue。

---

## 致敬

- **景颇族同胞**：感谢《目瑙纵歌》提供创作灵感与结构参考
- **花瑶呜哇山歌传承人**：陈治安、奉族群等，致敬千年传承
- **湖南省隆回县虎形山瑶族乡**：致敬这片孕育花瑶文化的山水
- **全球音乐工作者**：Master KG、Shakira、A Tribe Called Red

---

## 参考资料

完整调研资料见 [`docs/创作笔记.md`](docs/创作笔记.md) 和 [`references/链接清单.md`](references/链接清单.md)。

主要资料来源：
- [中国非物质文化遗产网](https://www.ihchina.cn) — 目瑙纵歌、花瑶呜哇山歌官方资料
- 知乎专栏《目瑙纵歌为何全网爆火》
- The Conversation — Jerusalema 爆火现象研究

---

> **创作宣言**：让花瑶的「呜哇」声穿越虎形山，传遍全世界。
>
> © 2026 贺去病AI工作室 · 保留全部权利
