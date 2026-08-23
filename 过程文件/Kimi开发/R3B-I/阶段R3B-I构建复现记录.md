# 阶段 R3B-I 构建复现记录

## 环境

- macOS，Python 3（venv）：`过程文件/Kimi开发/.venv/bin/python3`
- 依赖：Pillow（已在 venv）；中文字体 Hiragino Sans GB.ttc（审核图标签用；PingFang.ttc 在本环境
  无法被 Pillow 打开，生成器按既有回退链自动选用）
- Node.js v24.18.0（仅用于 `node --check` 语法校验 baked.js）

## 构建命令

```bash
cd "/Users/xingbili/Downloads/kimi/阳阳游泳游戏/过程文件/Kimi开发/R3B-I"
../.venv/bin/python3 build_identity_sprites_r3bi.py
```

- 生成器用 `Path(__file__).resolve().parent` 定位输入输出，不依赖当前工作目录。
- 输入 SHA 钉值校验全部通过后才开始构建；任一检查失败以非零退出码终止（显式 `SystemExit`，
  非 `assert`，`python -O` 无法绕过）。
- 全部产物先生成于内存、自检全过后统一落盘（tmp + rename 原子替换）；失败时不覆盖已有合格产物。
- 不读取照片/视频/网络 API/网页/被忽略的临时文件；主 HTML 不是构建输入。

## 输入钉值（SHA-256）

| 文件 | SHA-256（前16位） | 角色 |
|---|---|---|
| ../sprites_r3a_human_baked.js | bbd40b05f6d71438… | R3A 批准人体母版（唯一身体底稿，只读） |
| ../build_sprites_r3a.py | bffb7e445be037fe… | R3A 生成器（只校验未改动） |
| ../avatar_paint.py | 615daea6e81acbc6… | Stage2 身份母版（只校验哈希，不把头像贴入动作帧） |
| ../阶段3A-R3A人体母版清单.md | f49af48471782e5e… | R3A 文档（只读） |
| ../阶段3A-R3A人体母版验收记录.md | 6c0fe04e5aff1f7a… | R3A 文档（只读） |
| ../阶段3A-R3A构建复现记录.md | d480a7207fe28344… | R3A 文档（只读） |
| ../阶段3A-R3A人体母版审核表.png | 1069f4f055f26dcd… | R3A 审核图（只读） |
| ../阶段3A-R3A人体盲审图.png | 2b3fd17060e925dc… | R3A 盲审图（只读） |
| ../R3B-M/build_identity_masks_r3bm.py | deac9f147ae26d43… | R3B-M 生成器（只校验未改动） |
| ../R3B-M/identity_masks_r3bm.json | 00448adfa11cacd3… | R3B-M 批准蒙版（唯一可编辑范围来源） |
| ../R3B-M/identity_masks_r3bm_baked.js | 9ffd8aafa8ce7731… | R3B-M JS 版（只校验未改动） |

另逐像素复核 `R3B-M/masks/` 下 30 张蒙版 PNG（6 张总蒙版 + 24 张子蒙版，L 模式二值 0/255）
与 JSON 蒙版完全一致；并复检 R3B-M 关键不变量（子区互斥、并集=总蒙版、⊆inner、禁区=0、
颈肩=0、单簇、L/R 严格镜像）。另复核 R3A 母版 `contentSha256ByDir` 6 组全部一致。

**主HTML 不是构建输入**：仅作范围保护——构建开始检查存在并记录当前 SHA 到终端日志，
全部计算与自检完成、正式落盘前再复核 SHA 未变化。不固定任何特定版本 SHA，不写入任何输出物。
工作区主HTML（412416e9…）与干净 Git 基线主HTML（44f94a01…）均可复现完全相同的产物。

## 输出 SHA-256（本轮最终，52 个生成物）

```
c1da15bb33b72322ff638c4d84ad8257a9223e18bdcd396728464c8e14434839  identity_sprites_r3bi.json
23ef2cbb2a45498eda85ea25c6ca2b882aa55804e5f8549e6f9ba75ae7586e4d  identity_sprites_r3bi_baked.js
36569ed70d3bd7e6a3e9eb2990647450dbecc16a5abd6ea1bac013857e222607  阶段R3B-I身份稿审核表.png
593db61cec58f566e04690e63e859a74c766b2bffd06b140fbb229178bf2b6eb  阶段R3B-I身份稿盲审图.png
ed7e0111de2cce87c18d2b42defb676b3dc630ce2a4869771d944dbcca00dcd0  sprites/SURF0_yy_L.png
b0b2d879faebd95959cd7efc81290d9817429cc797ce3677038837f91a5525cf  sprites/SURF0_yy_R.png
6e5f2bdab68b1110da238d511c73d3df5fa3f0c0ddf7eca37fb0c2d2713ea7c3  sprites/SURF0_dd_L.png
7a2cfc8620678acb8e79f637e779198c11353dfe0797d688b7f0b4ffe3f825d2  sprites/SURF0_dd_R.png
1627a68c31171ac8e0b76eff273509d3eb6ebe2db4b09d96666ffabb88538cfe  sprites/JUMP_AIR_yy_L.png
fee172eca1c93dd34259e7093bfa761ac147c4f569e0b7e4bc06be97dc4a141c  sprites/JUMP_AIR_yy_R.png
67e1249f44590d4345f0befa3128953e9414a079ea2cdefcd9a5b840fb1c7622  sprites/JUMP_AIR_dd_L.png
84c211376d7374ef71bab344265c2da5decd663bf8f8b31884bfd47b5bc44ed1  sprites/JUMP_AIR_dd_R.png
bffa4cf920093c1a47a2863902b1e1101ebf9a767906f75746c1636faf92ab3b  sprites/UW_NORMAL_yy_L.png
6a48d4c5cda416182684a4ea2f7b58b2a20a43787df98c0c8802bab6a6945b65  sprites/UW_NORMAL_yy_R.png
9f6a6f2befbb7b2d7238de3132ea01378313b939ce2579ab8be674f213862026  sprites/UW_NORMAL_dd_L.png
5260e81df8830489d3f38375f4504270846b0b9fcc992e7d90a8dffb9190d185  sprites/UW_NORMAL_dd_R.png
d467849f837fa39f5540a12f0475ba4eb7e0839585aa3c076ff479d171339fd1  diff/SURF0_yy_L_mask.png
874ae083e9527f8af2c44eaf9a3b216e2c8d48f30056a3aab717e3356e996053  diff/SURF0_yy_L_color.png
fb6fe16930d38828e6b932b31e63c04cabd50214324b3dbb6eb050c9b96e62ab  diff/SURF0_yy_L_outside.png
5b2e18a1bd29daf8d33dc292ae0fd8e0e49f74da1ef4ddd8f8300f3c5cb818b6  diff/SURF0_yy_R_mask.png
91782621709470aa37b51eb9325b614acd3cc6a57cbbfa17bb922951831ab371  diff/SURF0_yy_R_color.png
484b9dc2b6209ad359b21c64fe7b1e687b9d2e2f7a22ac542b180f68d6226592  diff/SURF0_yy_R_outside.png
3663a5a4d2119f5df38cbb392426d4db3dfc91849107c1a49c66b6c747338f64  diff/SURF0_dd_L_mask.png
f0e2ff59e100cd0fdffe8df4dc63f98f7c4d3e0d9c5b41d6ea783984d76be536  diff/SURF0_dd_L_color.png
fb6fe16930d38828e6b932b31e63c04cabd50214324b3dbb6eb050c9b96e62ab  diff/SURF0_dd_L_outside.png
b96823a0d83f1d6dd4d18e80825f1c65142a5aaa589c81c063a66e412d4c81c8  diff/SURF0_dd_R_mask.png
efd805bc4830b571b42ff09bf1b2757054361862df43dd87e216289c1453c14d  diff/SURF0_dd_R_color.png
484b9dc2b6209ad359b21c64fe7b1e687b9d2e2f7a22ac542b180f68d6226592  diff/SURF0_dd_R_outside.png
8c759d7a68165e1120f41d5a3475a28e475cf0e0ad6012078dec4beb39b65bb1  diff/JUMP_AIR_yy_L_mask.png
7b2db8fe4c6eceeb36413cfda2d7a401958dd6d08a5470c1a9fbfae6faf9ee1a  diff/JUMP_AIR_yy_L_color.png
4ee978a43c326c689f80066301f85eb78ce3a08821a746fb585d00ef4c85b8c7  diff/JUMP_AIR_yy_L_outside.png
27532b47419a6eb5486d1530e5f159cefee3bc1f382167ab6a3628b908597687  diff/JUMP_AIR_yy_R_mask.png
232d03016587bf8efff9e6441badad63db4b29eac66eb3aa5435b5189851266d  diff/JUMP_AIR_yy_R_color.png
869bc7b52dfaf1eeda845fd1a41ba27c0bc84213d066acf76bbcf42b27c36188  diff/JUMP_AIR_yy_R_outside.png
b9988fc24aca6b82e752a1095f5dfe70de5eab0b263ab8b4941586245b311460  diff/JUMP_AIR_dd_L_mask.png
031fd0ea3afee761317369170adc40fc50262a7fb1029504ae06bd4b3377fcf4  diff/JUMP_AIR_dd_L_color.png
4ee978a43c326c689f80066301f85eb78ce3a08821a746fb585d00ef4c85b8c7  diff/JUMP_AIR_dd_L_outside.png
2f42b324e787beabe335e5c9a0208ebab2a541e2bb4d5fc8394f990b3cddd145  diff/JUMP_AIR_dd_R_mask.png
4811516f4e960485c0c79b1442aec4c42ccdc87710c8387fb9d05927b9f586ab  diff/JUMP_AIR_dd_R_color.png
869bc7b52dfaf1eeda845fd1a41ba27c0bc84213d066acf76bbcf42b27c36188  diff/JUMP_AIR_dd_R_outside.png
522a4b790957c3aa64dc887597bd24b2450cc0ae59cdf45dac6339853ecef758  diff/UW_NORMAL_yy_L_mask.png
2c4c060809308dfed9a09a5f7abd0b38558f2086a186f4998533d6b5be4c2c07  diff/UW_NORMAL_yy_L_color.png
b552a591efc810125717a20876f84469bcdc2ba7f851221c955b1dae62f8bc3c  diff/UW_NORMAL_yy_L_outside.png
ddedd03c42c521f64a9907588f3af02446fa3bf19becc00d0e9af425d0f91453  diff/UW_NORMAL_yy_R_mask.png
b932c0c66b1272b234bfc4538fc5ed6cd989d667de7664ed15c652bd63940b5e  diff/UW_NORMAL_yy_R_color.png
b8f34fcbb61e714b9ecfe91292ee5803da15f7228426a1fe759b4b6ce34d25bb  diff/UW_NORMAL_yy_R_outside.png
137e39190288ae89921eb72cb70131ad31bebc1d5b32aa037711af8d6d1c3b57  diff/UW_NORMAL_dd_L_mask.png
d30087707c90b20cf453b0cad824cf7ac4c24367867f32814d2cd0bc940f37e9  diff/UW_NORMAL_dd_L_color.png
b552a591efc810125717a20876f84469bcdc2ba7f851221c955b1dae62f8bc3c  diff/UW_NORMAL_dd_L_outside.png
a635dbfed29a3a56b36b92706b1b22147d46f4c00f3e535504ec3675f05c81c2  diff/UW_NORMAL_dd_R_mask.png
4a60f83cfeecf69900bbf194d4a1e9d5ee19422285019a03147c984787f124e8  diff/UW_NORMAL_dd_R_color.png
b8f34fcbb61e714b9ecfe91292ee5803da15f7228426a1fe759b4b6ce34d25bb  diff/UW_NORMAL_dd_R_outside.png
```

注：`*_outside.png` 只取决于母版+蒙版（红色违规像素为零），同一姿态·向的 yy/dd 两张逐字节
相同（SURF0·L=fb6fe169…、SURF0·R=484b9dc2…、JUMP_AIR·L=4ee978a4…、JUMP_AIR·R=869bc7b5…、
UW_NORMAL·L=b552a591…、UW_NORMAL·R=b8f34fcb…），上方列表已分别如实列出。

## 可复现性验证（全部实测通过）

1. **双跑确定性**：工作区连续构建两次，52 个生成物 SHA-256 逐一比对完全一致（diff 无输出）。
2. **干净基线复现**：`git archive HEAD 679cb36` 提取最小输入（上表 11 个钉值文件 +
   R3B-M/masks 30 张 + 主HTML）到 /tmp/r3bi_clean，拷入本生成器，重建退出码 0；
   52 个产物与工作区**逐字节完全一致**（逐一 shasum 比对，无差异）。
   干净环境主HTML SHA=44f94a01…（与工作区 412416e9… 不同），日志确认其仅打印到终端。
3. **篡改 R3A 输入**：/tmp/r3bi_tamperA 中对 sprites_r3a_human_baked.js 追加 1 字节 →
   退出码 **1**（`R3B-I FAIL: sprites_r3a_human_baked.js SHA 不符…`），52 个既有产物 SHA 全部不变。
4. **篡改 R3B-M 输入**：/tmp/r3bi_tamperB 中对 identity_masks_r3bm.json 追加 1 字节 →
   退出码 **1**（`R3B-I FAIL: identity_masks_r3bm.json SHA 不符…`），52 个既有产物 SHA 全部不变。
5. `python3 -m py_compile build_identity_sprites_r3bi.py` PASS。
6. `node --check identity_sprites_r3bi_baked.js` PASS。
7. 重新 `json.load` 解析 JSON：meta 必备字段（schemaVersion/stage=R3B-I/artifactKind/applied=true/
   三组输入 SHA/表面身份调色板/水下映射）与 12 张稿必备字段（w/h/root/visibleBBox/rows/
   changedPixels 坐标与总数/四子区统计/outsideDiff=0/alphaDiff=0/forbiddenBodyDiff=0/
   colorsUsed/identityNote）齐全，changedPixelsTotal 与坐标数一致。
8. 重新读取 12 张 sprites PNG，逐像素与 JSON rows×调色板比对：**12/12 全部一致**。
9. `git diff --check` 无输出（退出码 0）。

## 自检输出（原文）

```
主HTML范围保护: 构建前SHA=412416e95bfe4c98…(仅日志, 不参与输出)
批准蒙版复核: JSON↔30张PNG一致, 子区互斥, ⊆inner, 禁区=0, 颈肩=0, 单簇, L/R镜像一致
SURF0/L: yy changed=60 子区={'hairOrCapMask': 48, 'eyesOrGlassesMask': 9, 'faceDetailMask': 2, 'mouthMask': 1} | dd changed=58 子区={'hairOrCapMask': 46, 'eyesOrGlassesMask': 9, 'faceDetailMask': 1, 'mouthMask': 2} | outside=0 alpha=0 禁区=0
SURF0/R: yy changed=60 子区={'hairOrCapMask': 48, 'eyesOrGlassesMask': 9, 'faceDetailMask': 2, 'mouthMask': 1} | dd changed=58 子区={'hairOrCapMask': 46, 'eyesOrGlassesMask': 9, 'faceDetailMask': 1, 'mouthMask': 2} | outside=0 alpha=0 禁区=0
JUMP_AIR/L: yy changed=106 子区={'hairOrCapMask': 85, 'eyesOrGlassesMask': 19, 'faceDetailMask': 0, 'mouthMask': 2} | dd changed=102 子区={'hairOrCapMask': 78, 'eyesOrGlassesMask': 19, 'faceDetailMask': 1, 'mouthMask': 4} | outside=0 alpha=0 禁区=0
JUMP_AIR/R: yy changed=106 子区={'hairOrCapMask': 85, 'eyesOrGlassesMask': 19, 'faceDetailMask': 0, 'mouthMask': 2} | dd changed=102 子区={'hairOrCapMask': 78, 'eyesOrGlassesMask': 19, 'faceDetailMask': 1, 'mouthMask': 4} | outside=0 alpha=0 禁区=0
UW_NORMAL/L: yy changed=21 子区={'hairOrCapMask': 8, 'eyesOrGlassesMask': 10, 'faceDetailMask': 0, 'mouthMask': 3} | dd changed=19 子区={'hairOrCapMask': 6, 'eyesOrGlassesMask': 10, 'faceDetailMask': 2, 'mouthMask': 1} | outside=0 alpha=0 禁区=0
UW_NORMAL/R: yy changed=21 子区={'hairOrCapMask': 8, 'eyesOrGlassesMask': 10, 'faceDetailMask': 0, 'mouthMask': 3} | dd changed=19 子区={'hairOrCapMask': 6, 'eyesOrGlassesMask': 10, 'faceDetailMask': 2, 'mouthMask': 1} | outside=0 alpha=0 禁区=0
ALL R3B-I CHECKS PASS
```
