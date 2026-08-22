# 阶段 R3B-M 构建复现记录

## 环境

- macOS，Python 3（venv）：`过程文件/Kimi开发/.venv/bin/python3`
- 依赖：Pillow（已在 venv）；中文字体 PingFang.ttc（审核图标签用）
- Node.js（仅用于 `node --check` 语法校验 baked.js）

## 构建命令

```bash
cd "/Users/xingbili/Downloads/kimi/阳阳游泳游戏/过程文件/Kimi开发/R3B-M"
../.venv/bin/python3 build_identity_masks_r3bm.py
```

- 生成器用 `Path(__file__).resolve().parent` 定位输入输出，不依赖当前工作目录。
- 输入 SHA 钉值校验全部通过后才开始构建；任一断言失败以非零退出码终止（显式 `SystemExit`，非 `assert`，`python -O` 无法绕过）。
- 自检全部通过后才写文件（tmp + rename）；失败时不覆盖已有正式输出。

## 输入钉值（SHA-256）

| 文件 | SHA-256（前16位） | 角色 |
|---|---|---|
| ../sprites_r3a_human_baked.js | bbd40b05f6d71438… | R3A 批准人体母版（只读） |
| ../build_sprites_r3a.py | bffb7e445be037fe… | R3A 生成器（只校验未改动） |
| ../avatar_paint.py | 615daea6e81acbc6… | Stage2 身份母版（只校验存在与哈希，不读取像素） |
| ../阶段3A-R3A人体母版清单.md | f49af48471782e5e… | R3A 文档（只读） |
| ../阶段3A-R3A人体母版验收记录.md | 6c0fe04e5aff1f7a… | R3A 文档（只读） |
| ../阶段3A-R3A构建复现记录.md | d480a7207fe28344… | R3A 文档（只读） |
| ../阶段3A-R3A人体母版审核表.png | 1069f4f055f26dcd… | R3A 审核图（只读） |
| ../阶段3A-R3A人体盲审图.png | 2b3fd17060e925dc… | R3A 盲审图（只读） |

**主HTML（`../../../阳阳水泳大乱斗-原版复刻.html`）不是构建输入，不参与输出计算**：
仅作范围保护——构建开始检查存在并记录当前 SHA 到终端日志，全部计算与自检完成、
正式落盘前再复核 SHA 未变化。不固定任何特定版本 SHA，也不写入 JSON/JS/PNG 任何输出物。
因此干净 Git 基线（3a1c5cb，主HTML SHA=44f94a01…）与工作区（主HTML SHA=412416e9…）
均可复现完全相同的产物（见下文"双环境复现测试"）。

另复核 R3A 母版 `contentSha256ByDir`：`sha256("\n".join(rows)+"\n", ascii)`，6 组全部一致。

## 输出 SHA-256（本轮最终）

```
deac9f147ae26d43f61ee62a7146d8866a7d30208f802e9e64ea176116a37d6c  build_identity_masks_r3bm.py
00448adfa11cacd37a9b1aa39d94f2772cb6a311e2f86a4a79b852d5699053f1  identity_masks_r3bm.json
9ffd8aafa8ce77315d42f2f8e5a3fb85ffc3a107c22404bd5ba327a65f91ffaa  identity_masks_r3bm_baked.js
32e99bd671e372c067e4873b393416413ff4d67c9c0f4c1935b105b757aeaa33  阶段R3B-M身份蒙版审核表.png
17fe344ffe90ed12c6c455ef5cecde8d0cd9c5aadc3f0845c0fa571f75f87c3d  阶段R3B-M身份蒙版盲审图.png
934a5953c0563b5a90a3ef61fc003a6ab9a459a41d8195d5f81eed4a7a21b798  masks/JUMP_AIR_L.png
b6933b8f3f7b6387a2052f9f4815b169fbf05f0f06b801810fb4a741ec16aa48  masks/JUMP_AIR_R.png
bda8467a690ba1ed200dddf7caccfc4c062a9e0b18f45704041d54bee0ef4fe7  masks/SURF0_L.png
36c2098bd40a798bbb5e7d0da769ec991bc9950addcc6fd90df90163e5b7da8c  masks/SURF0_R.png
9bc410184b085889e478c0eb8ea2c021e15e75f76f7b6cf3a3e74da3789c76c2  masks/UW_NORMAL_L.png
c97bff16cdc05f006ace80cb3655d97155abab019a788932ca1c4a5049eec65c  masks/UW_NORMAL_R.png
```

（masks/sub/ 24 张子蒙版 PNG 同批生成，亦纳入双跑一致性校验。）

**蒙版数据和审核产物 SHA 保持不变**：2026-08-22 最小返修（主HTML 范围保护化）
仅改动生成器，返修前后全部 34 个生成物（30 张 PNG + JSON + JS + 审核表 + 盲审图）
SHA-256 逐字节一致；仅生成器自身 SHA 由 80184e48… 变为 df6d2c84…。
（2026-08-22 基线提交桥接：生成器头部注释中主HTML相对路径 `../../` 修正为 `../../../`，
纯注释修正，不改任何执行逻辑；生成器 SHA 随之由 df6d2c84… 变为 deac9f14…；
30 张蒙版PNG、JSON、JS、审核表和盲审图内容均未改变，双跑 SHA 与修正前逐字节一致。）

## 双环境复现测试（2026-08-22）

在 /private/tmp 建立两个相互独立的最小复现目录，同一套已批准 R3A 输入 + 同一生成器：

| 环境 | 主HTML 来源 | 主HTML SHA | 构建退出码 |
|---|---|---|---|
| A（/private/tmp/r3bm_envA） | 当前工作区 | 412416e95bfe4c98f4b039dc4a24fd9b28c2c23989254f22ee494d2e7bcde306 | 0 |
| B（/private/tmp/r3bm_envB） | Git 基线 3a1c5cb（`git show HEAD:…`） | 44f94a01d1262e18703331fce61f0df7a3ba8a6e313ab708595151eaab9f297f | 0 |

- A 与 B 各自生成的全部 34 个产物（30 张蒙版 PNG + JSON + JS + 审核表 + 盲审图）
  经 `shasum -a 256` 逐一 diff **逐字节完全一致**。
- A、B 全部产物与工作区正式产物、返修前现有产物亦逐字节一致。
- 日志确认主HTML SHA 仅打印到终端（A=412416e9…、B=44f94a01…），未写入任何输出物。

## 失败路径测试（2026-08-22）

在 /private/tmp/r3bm_envC（环境A副本）中篡改 R3A 批准输入
`sprites_r3a_human_baked.js`（追加一字节使 SHA 不符）：

- 生成器以退出码 **1** 终止：`R3B-M FAIL: sprites_r3a_human_baked.js SHA 不符…`
- 测试前已存在的全部正式输出 SHA **保持不变**（前后 diff 无输出）——失败不落盘、不覆盖。

## 可复现性验证

1. 连续运行两次生成器，全部输出文件（masks 30 张 PNG + JSON + JS + 审核表 + 盲审图）SHA-256 逐一比对 **完全一致**（`diff` 无输出）。
2. `node --check identity_masks_r3bm_baked.js` PASS。
3. `python3 -m py_compile build_identity_masks_r3bm.py` PASS。
4. 盲审图顺序为固定乱序（确定性），保证双跑一致。

## 自检输出（原文）

```
SURF0/L: 有效px=457 蒙版=78 (17.1%) 子区={'hairOrCapMask': 48, 'eyesOrGlassesMask': 13, 'faceDetailMask': 9, 'mouthMask': 8} 簇=1 禁区=0 颈肩=0
SURF0/R: 有效px=457 蒙版=78 (17.1%) 子区={同上} 簇=1 禁区=0 颈肩=0
JUMP_AIR/L: 有效px=1437 蒙版=130 (9.0%) 子区={'hairOrCapMask': 85, 'eyesOrGlassesMask': 24, 'faceDetailMask': 7, 'mouthMask': 14} 簇=1 禁区=0 颈肩=0
JUMP_AIR/R: 有效px=1437 蒙版=130 (9.0%) 子区={同上} 簇=1 禁区=0 颈肩=0
UW_NORMAL/L: 有效px=425 蒙版=38 (8.9%) 子区={'hairOrCapMask': 11, 'eyesOrGlassesMask': 12, 'faceDetailMask': 10, 'mouthMask': 5} 簇=1 禁区=0 颈肩=0
UW_NORMAL/R: 有效px=425 蒙版=38 (8.9%) 子区={同上} 簇=1 禁区=0 颈肩=0
本轮身份实际绘制像素 changedPixels=0(必须为0)
ALL R3B-M CHECKS PASS
```
