# FORK-0 Git 检查点清单

> **⚠️ 已作废：本文件由 `FORK-0-R1精确提交清单.md`（并经 FORK-0-R2 返修）替代。**
> 本文中的统计（如 181 个文件）与状态（如 R3B-M 记录 0 字节）均为 2026-08-23 上午的旧现场，
> 不再反映当前仓库，请勿据以执行任何 git 操作；保留仅为历史存档。

- 审计时间：2026-08-23
- 当前分支：`main`（唯一分支；`fc-replica`、`concept-style-game` 均不存在，本轮未创建）
- 当前 HEAD：`679cb3615862eb233f6a219e56dbfc15aaac90be`（`stage3b-m-identity-mask-approved`）
- 暂存区：空
- 本轮动作：仅只读检查 + 新建本文件与 `输出/概念画风版开发路线草案.md`；未提交、未暂存、未切分支、未修改/删除任何既有文件。

## 1. 工作区状态

### 1.1 已跟踪但被修改（5 个，`git diff --name-status`）

| 文件 | 改动规模 | 说明 |
|---|---|---|
| `.gitignore` | +36 行 | 新增家庭照片、原版参考、概念图、可再生成中间文件等忽略规则 |
| `开发规格书.md` | ±28 行 | 规格书更新（用户/Codex 手改） |
| `输出/给Kimi的分阶段执行指令.md` | ±39 行 | 分阶段指令更新（用户/Codex 手改） |
| `过程文件/Kimi开发/R3B-M/阶段R3B-M构建复现记录.md` | -106 行 | **当前为 0 字节，见第 4 节核验** |
| `阳阳水泳大乱斗-原版复刻.html` | +1064 / -51 | 主程序大量新增（状态机/自检等，未接入任何 R3B 人物数据，见第 5 节） |

### 1.2 未跟踪且未被忽略：181 个文件，合计约 3.05 MB

按目录统计：R3B-I 664 KB、R3B-I-P1 288 KB、Codex R3B-I-P2 约 82 KB（未忽略部分；目录总 1.6 MB 含被忽略概念图）、Codex R3B-I-P3 172 KB、阶段3 556 KB、阶段3A0参考 112 KB，其余为根级散文件。

### 1.3 被 `.gitignore` 排除的未跟踪文件（抽样核验均生效）

| 路径 | 命中规则 | 大小 |
|---|---|---|
| `17296.jpeg` / `IMG_0387.jpeg` / `IMG_0806.jpeg`（家庭照片） | .gitignore:4-6 | 0.6/1.7/4.1 MB |
| `过程文件/原版参考/实机视频-JP-Bydl-MUoLGU.mp4`（原版视频） | .gitignore:9 | 59 MB |
| `过程文件/原版参考/实机视频-USA-vjlUJSGGE3g.mp4` | .gitignore:9 | 21 MB |
| `过程文件/Kimi开发/R3B-I-LikenessTest/阳阳爸爸头像方向参考-本地勿提交.png` | .gitignore:29 | 1.15 MB |
| `过程文件/Codex开发/R3B-I-P2/阳阳爸爸多动作概念参考-本地勿提交.png` | .gitignore:31 | 1.58 MB |
| `过程文件/Kimi开发/.venv/` | .gitignore:27 | 含 49 MB ffmpeg 二进制等 |

**超过 5 MB 的未跟踪文件共 3 个（venv 内 ffmpeg 49 MB、两个原版视频 59/21 MB），全部被忽略规则命中，无误入 Git 风险。** 未被忽略的未跟踪文件中无超过 5 MB 者。

## 2. 建议进入"FC路线暂停点提交"（wip-fc-route-before-concept-fork）的文件

### 2.1 修改类（4/5 个）

- `.gitignore` — 忽略规则是隐私安全前提，必须先入库。
- `开发规格书.md`、`输出/给Kimi的分阶段执行指令.md` — 现行规划事实来源。
- `阳阳水泳大乱斗-原版复刻.html` — FC 路线当前游戏实体。
- **不建议提交** `过程文件/Kimi开发/R3B-M/阶段R3B-M构建复现记录.md` 的当前改动（0 字节清空，见第 4 节；建议先由 Codex 决定恢复后再入库）。

### 2.2 未跟踪类：构建必需源码

- `过程文件/Kimi开发/build_sprites.py`（主 HTML 现行人物的生成器，.gitignore 明确不忽略）
- `过程文件/Kimi开发/build_sprites_3a.py`、`build_sprites_3a0.py`
- `过程文件/Kimi开发/R3B-I/build_identity_sprites_r3bi.py`
- `过程文件/Kimi开发/R3B-I-P1/build_likeness_sprites_r3bip1.py`
- `过程文件/Codex开发/R3B-I-P2/build_concept_sprites_r3bip2.py`
- `过程文件/Codex开发/R3B-I-P3/build_identity_enhanced_r3bip3.py`

### 2.3 未跟踪类：正式输出 / 验收证据

- `过程文件/Kimi开发/R3B-I/` 其余全部：identity_sprites_r3bi.json / _baked.js、sprites/ 12 张、diff/ 36 张、审核表、盲审图、清单、构建复现记录、验收记录
- `过程文件/Kimi开发/R3B-I-P1/` 全部：JSON、blind_map、sprites/ 4 张、masks/ 4 张、diff/ 8 张、对照表、盲审图、三份 md
- `过程文件/Codex开发/R3B-I-P2/`：`concept_sprites_r3bip2.json`、sprites/ 8 张、对照表、场景效果图、说明 md（**不含**被忽略的概念参考图）
- `过程文件/Codex开发/R3B-I-P3/` 全部：JSON、sprites/ 12 张、尺寸预览、对照表、说明 md
- `过程文件/Kimi开发/阶段3验收记录.md`、`阶段3A0-R1返修验收记录.md`、`阶段3A0-R2接手验收记录.md`、`阶段3A0构建复现记录.md`、`阶段3A0精灵清单.md`、`阶段3A精灵清单.md`
- `过程文件/Kimi开发/阶段3/` 证据与诊断图（556 KB）、`阶段3演示.gif`、阶段3A0/3A 精灵审核表 4 张、`阶段3A0场景验收图` 2 张

### 2.4 建议提交量估算

约 170 个文件、约 2.9 MB（181 个未跟踪减去 2.4 节待定项，外加 4 个修改文件）。

## 3. 建议只留本地（继续由 .gitignore 排除）

- 三张家庭照片；`过程文件/原版参考/`（原版视频 80 MB）；
- 两张概念图（LikenessTest 头像参考、Codex P2 多动作参考）；
- `.venv/`；`.DS_Store`；
- .gitignore 已列的可再生成中间文件（bg_data.js、pool_data.js、各 preview、crop_*、migrate_r3-r6.py、oxy_scan.py、shoot_r6.py、sprites_baked.js、sprites_3a_baked.js、action_scan/、st3_shots/ 等）。

## 4. 0 字节文件核验：`过程文件/Kimi开发/R3B-M/阶段R3B-M构建复现记录.md`

- 工作区：0 字节，SHA-256 = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（空文件哈希）
- HEAD 版：6558 字节，SHA-256 = `bfaf9e8598bf7c99cb5f49d8a755e68545a28d32ab17f22831091e904c1265da`，开头为正常的"# 阶段 R3B-M 构建复现记录"
- **结论：HEAD 中保存着完整版本，工作区副本是被意外清空（非内容演进）。**
- **建议（不执行）**：由 Codex 决定是否 `git checkout -- <该文件>` 恢复，或在检查点提交前先恢复再提交完整版本。本轮未修改该文件。

## 5. 主 HTML 只读检查结论

- 改动规模：相对 HEAD +1064/-51 行，现 1414 行。
- 语法：提取唯一 `<script>` 块 `node --check` 通过；HTML 结构完整（有 `</html>`）。
- 画布：单一 `<canvas width="256" height="224">`，`imageSmoothingEnabled=false`，CSS 像素化整数倍缩放（fitCanvas 只改 CSS）——符合 FC 复刻底座。
- **人物接入结论（依据代码，非文档）**：人物渲染为"阶段2烘焙 24×24 头像 + build_sprites.py 生成的 16×16 像素身体"（drawSwimmers，行 1028 起）；全文件 grep 不到 `r3bi / r3bip / R3B / identity_sprites / sprites_r3a / identity_masks / likeness / concept_sprites / identity_enhanced` 任何引用。**主 HTML 未接入 R3B-I、R3B-I-P1、R3B-I-P2、R3B-I-P3 的任何人物稿，当前跑的仍是 R3A 之前的旧人物方案。**

## 6. 暂时无法判断、需 Codex 决定

| 文件/目录 | 疑点 |
|---|---|
| `过程文件/Kimi开发/阶段3A0参考/`（112 KB，10 个文件） | 内容是原版视频帧提取/蒙版（jump_ref、surf0_real_f12393、uw_ref 系列）。属"原版参考素材"，按隐私/版权谨慎原则倾向留本地，但它未被 .gitignore 覆盖，且是 3A0 复现链的输入——留本地则干净环境无法复现 3A0。 |
| `过程文件/Kimi开发/sprites_3a0_baked.js`（31 KB） | 构建产物（可再生成），但不在忽略列表；若 3A0 参考帧留本地，该产物是否入库作证据待定。 |
| 阶段3 诊断图（s1-s11、z_ 前缀，约 400 KB） | 介于"验收证据"与"可再生成中间文件"之间。 |
| R3B-M 0 字节文件的处置方式 | 恢复 vs 提交空文件，需 Codex 定夺。 |

## 7. 建议的后续 Git 操作（仅命令草案，本轮未执行）

```bash
# 0. （可选，待 Codex 决定）恢复被清空的记录
# git checkout -- "过程文件/Kimi开发/R3B-M/阶段R3B-M构建复现记录.md"

# 1. 在 main 上建立检查点提交（不使用 git add -A，按第 2 节清单逐项添加）
git add .gitignore 开发规格书.md "输出/给Kimi的分阶段执行指令.md" \
  "阳阳水泳大乱斗-原版复刻.html" \
  过程文件/Kimi开发/build_sprites.py 过程文件/Kimi开发/build_sprites_3a.py \
  过程文件/Kimi开发/build_sprites_3a0.py \
  "过程文件/Kimi开发/R3B-I" "过程文件/Kimi开发/R3B-I-P1" \
  "过程文件/Codex开发/R3B-I-P2" "过程文件/Codex开发/R3B-I-P3" \
  过程文件/Kimi开发/阶段3 \
  过程文件/Kimi开发/阶段3验收记录.md \
  过程文件/Kimi开发/阶段3A0-R1返修验收记录.md \
  过程文件/Kimi开发/阶段3A0-R2接手验收记录.md \
  过程文件/Kimi开发/阶段3A0构建复现记录.md \
  过程文件/Kimi开发/阶段3A0精灵清单.md \
  过程文件/Kimi开发/阶段3A精灵清单.md \
  过程文件/Kimi开发/阶段3A0精灵审核表-1.png \
  过程文件/Kimi开发/阶段3A0精灵审核表-2.png \
  过程文件/Kimi开发/阶段3A0场景验收图.png \
  过程文件/Kimi开发/阶段3A0场景验收图-8x.png \
  过程文件/Kimi开发/阶段3A精灵审核表-1.png \
  过程文件/Kimi开发/阶段3A精灵审核表-2.png \
  过程文件/Kimi开发/阶段3演示.gif \
  过程文件/Kimi开发/阶段3证据-下潜-f15615-f15620.png \
  过程文件/Kimi开发/阶段3证据-换气-f16044-f16066.png \
  过程文件/Kimi开发/阶段3证据-水下方向-f15554-f15680.png \
  过程文件/Kimi开发/阶段3证据-跳跃-官方截图.png
git commit -m "wip-fc-route-before-concept-fork"

# 2. 在该提交上创建并保留 fc-replica 分支（不切换）
git branch fc-replica

# 3. 创建并切换到 concept-style-game 分支
git switch -c concept-style-game

# 注意：若 fc-replica 或 concept-style-game 已存在，上述命令会直接报错，
# 届时不得使用 -f / -B / --force 覆盖，必须先停下来人工确认。
```

## 8. 风险提示

- 私人照片、原版视频、两张概念图、venv 均被忽略规则命中；只要不使用 `git add -A`/`git add .` 之外的强制 `-f` 添加，无误入风险。
- 当前 .gitignore 本身是未提交修改，**在检查点提交前，任何clone/干净环境都没有这些忽略规则**——这是把 .gitignore 列入首批提交文件的原因。
