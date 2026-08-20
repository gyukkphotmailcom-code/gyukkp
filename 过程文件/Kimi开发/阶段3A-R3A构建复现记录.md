# 阶段3A R3A 构建复现记录

> 状态：R3A 原版人体母版已冻结并通过人工“先像完整的人”视觉门。这里只批准
> `SURF0 / JUMP_AIR / UW_NORMAL` 三张原版人体母版及其构建链；不批准阳阳/爸爸身份层、
> 动画时序或主程序集成。

## 标准命令

```bash
python3 -B 过程文件/Kimi开发/build_sprites_r3a.py --make-subjects
python3 -B 过程文件/Kimi开发/build_sprites_r3a.py
```

若本地存在被 Git 忽略的官方截图，可额外验证官方水下参考的确定性提取：

```bash
python3 -B 过程文件/Kimi开发/build_sprites_r3a.py --extract-official-uw
```

默认构建只依赖 Python、Pillow、Node 语法检查，以及下列本地跟踪候选文件；不依赖
`avatar_paint.py`、真人照片、原版视频、主 HTML、旧 `build_sprites.py`、旧
`build_sprites_3a.py` 或旧 `build_sprites_3a0.py`。官方 GIF 只用于重新提取已锁定的
水下派生基准，不是默认构建依赖。

## 最小输入

```text
过程文件/Kimi开发/build_sprites_r3a.py
过程文件/Kimi开发/阶段3A0参考/
  surf0_mask_source.png
  jump_mask_source.png
  uw_official_b_source_R.png
  mask_SURF0.png
  mask_SURF0.json
  mask_JUMP_AIR.png
  mask_JUMP_AIR.json
  mask_UW_OFFICIAL_B_R.png
  mask_UW_OFFICIAL_B_R.json
  subject_R3A_SURF0.png
  subject_R3A_SURF0.json
  subject_R3A_JUMP_AIR.png
  subject_R3A_JUMP_AIR.json
  subject_R3A_UW_NORMAL.png
  subject_R3A_UW_NORMAL.json
```

## 冻结版本与正式输出

```text
bffb7e445be037fe5262993393c91e5f33ada7ca5c6eee2a2a629854b075d1be  build_sprites_r3a.py
bbd40b05f6d7143826f7d554f04deb878a98bf503c09c6fd5bf00c1e612bf7f2  sprites_r3a_human_baked.js
1069f4f055f26dcd9a8a3dbee8fe5f71ab7cb889c21ef82d2ece5dba041156e2  阶段3A-R3A人体母版审核表.png
2b3fd17060e925dcb4065baf2158358de827eea197e5cb728d7e581a3d8cf86e  阶段3A-R3A人体盲审图.png
```

三份 subject JSON：

```text
616130086e6ba8fbe9f5d5b2be7b6dc08075dbe8abcf6351c72c90704f1b3d2e  subject_R3A_SURF0.json
9be8e1ea555368bcc5dcfe303dfadfa3f7733ee0ae0796983a86f127cf750f66  subject_R3A_JUMP_AIR.json
dcfa9242d17b39efdb6ea4ede963af69d47740bb269869059f6ab84302c084e0  subject_R3A_UW_NORMAL.json
```

人体母版逐行哈希前缀：

```text
SURF0     98528e47f7cc
JUMP_AIR  e67df72aecbc
UW_NORMAL 775145f84f4c
```

## 官方水下参考提取

水下母版改用官方 `jp-action-b.gif` 的静态合成图，不再使用会读成胶囊的美版视频
`f12490`，也不再使用包含两人的 `f15625`。锁定派生文件：

```text
88f085a4a6d3bd59b30d23bd4fb173dfe541abb99ed4b40304f0dbf76574ded8  uw_official_b_source_R.png
a67aefa4fca9b202376d605017514d025debac9f41ed92927d1c9bc6a77ad56e  mask_UW_OFFICIAL_B_R.png
665ac4cb18a6780d8b699592fb62242d0c58cc3036ea55c7885ad1b3a47d1363  mask_UW_OFFICIAL_B_R.json
```

连续执行两次 `--extract-official-uw`，以上三个 SHA-256 均不变。该 mask 是从整屏静态
合成图推导的“可见人物区域”，不是 ROM 原生 alpha；方向只记为 R 候选，实际运动方向
仍为 TBD，不据此宣称动画时序或方向已经标定。

## 独立最小目录复现

在全新目录 `/private/tmp/yy-r3a-final.CsgGCf` 仅复制“最小输入”，先执行
`--make-subjects`，再执行
默认构建，退出码为 0。三项正式输出与项目目录逐字节一致，SHA-256 即“冻结版本与正式
输出”中的三项产物哈希。

## 故障输入不覆盖正式产物

在已成功构建的最小目录中完成了两项独立负向测试：

1. 把 `subject_R3A_SURF0.json` 的 `sourceFile` 改为 `wrong.png`，构建退出 1：

   ```text
   [FAIL] SURF0 subject JSON完整合同不一致: ['sourceFile']
   ```

2. 恢复 subject 后，把 `mask_UW_OFFICIAL_B_R.json` 的 `recipeVersion` 从 1 改为 99，
   构建退出 1：

   ```text
   [FAIL] UW_NORMAL legacy mask JSON缺失或SHA不符
   ```

两次失败前后，JS、审核表、盲审图三项正式输出 SHA-256 均保持为冻结值，证明输入或
自检失败不会覆盖上一代正式产物。

## 已通过自动门

- 三个 source、历史 mask、subject 的模式、尺寸、像素数、bbox、4 连通和 SHA 均锁定；
- 三份历史 mask JSON 的完整 SHA、原件 SHA、裁剪框、方向候选及提取参数均锁定；
- subject JSON 必须与代码生成的完整对象逐字段相等，任一来源或 recipe 字段漂移即失败；
- subject 与代码内显式 derivation 完全一致，禁止 `fill_holes` 和隐式矩形补画；
- L 母版逐像素等于锁定参考分类结果，R 母版是确定性镜像候选；
- alpha 与 subject XOR 为 0，负空间坐标与 SHA 锁定；
- root 或其 8 邻域必须落在有效人物像素；
- JS 通过 `node --check`，且不包含阳阳、爸爸、FACES、team 或可编辑 identity mask；
- 产物先写同目录临时文件，全部自检与 Node 检查通过后才逐文件原子替换；
- 主 HTML 未引用 `SPRITES_R3A_HUMAN` 或 `sprites_r3a`，R3A 尚未接入运行时。

## 人工视觉门结论

- `SURF0`：1×可读为单一水面泳者，没有第二张脸；通过。
- `JUMP_AIR`：1×可读为完整飞扑人物，头、躯干、双臂与腿脚明确；通过。
- `UW_NORMAL`：换用官方静态参考后，1×/3×均先读作单一水下小人，不再是胶囊；通过。

这只证明三张原版人体母版“先像一个完整的人”。`reviewHeadRoi` 仅供后续人工定位头部，
不是允许修改的 identity mask。R3B 必须另行定义极小、逐像素审核的身份修改区，再制作
阳阳/爸爸版本。

## 尚未证明

- 宣传 GIF/静态整屏合成图不是 ROM 无损 CHR 数据，不能宣称 ROM 调色索引 100% 一致；
- R 向尚无每个姿态的独立原版帧；
- 三张静态母版不能证明动作帧序、节奏或过渡；
- 尚未制作阳阳/爸爸身份层，也未接入主程序；
- R3B 身份层和后续逐帧动画必须分别重新审核，不能继承本轮视觉通过结论。
