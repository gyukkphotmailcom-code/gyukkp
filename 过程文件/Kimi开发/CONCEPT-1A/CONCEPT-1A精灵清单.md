# CONCEPT-1A 精灵清单

- 阶段：CONCEPT-1A（角色身份与静态动作美术门）
- 分支：concept-style-game　基线 HEAD：0a1bd619dfb6a845505e1945877fe5e08e78f121
- 生成器：`过程文件/Kimi开发/CONCEPT-1A/build_concept_1a.py`（确定性，无随机数、无网络、无外部图像输入）
- 产物性质：静态关键帧美术候选，applied=false，未接入任何游戏
- 画风：现代 Q 版像素，1–2px 深色硬描边，平涂色块+少量像素高光，alpha 仅 0/255，无抗锯齿
- 设计身高：阳阳约 66px，爸爸约 78px（路线草案候选区间 yy 60–72 / dd 70–84 内）

## 1. 精灵（18 张，均为透明 PNG）

| 文件 | 角色 | 姿态 | 方向 | 单元格 | 头部 | 调色 | SHA-256 |
|---|---|---|---|---|---|---|---|
| sprites/yy_SURF_SWIM_L.png | 阳阳 | SURF_SWIM | L | 112×56 | 25×27 | 表面 | d0ffc9b9504a1364dfafcb41869828515b9e4570c43b95c461d1052dbc58ea09 |
| sprites/yy_SURF_SWIM_R.png | 阳阳 | SURF_SWIM | R | 112×56 | 25×27 | 表面 | 2a793330356c22beb8297564caaf794ce23f61144fcb2be9b8a25d200d06ca68 |
| sprites/yy_JUMP_L.png | 阳阳 | JUMP | L | 96×96 | 25×27 | 表面 | d24e4358febfd3076f2657f5711141c0a171f07031f5835f84d7f0b5ce7903be |
| sprites/yy_UW_SWIM_L.png | 阳阳 | UW_SWIM | L | 128×56 | 25×27 | 水下 | 7d77b5aa14280d4a5f7892d4cce1f8976d750d042aa3a771ba8bba6089099bdb |
| sprites/yy_UW_SWIM_R.png | 阳阳 | UW_SWIM | R | 128×56 | 25×27 | 水下 | dad8e92c5b4393d52d272463e326a8e451064799218579004a366f05ee0a5a98 |
| sprites/yy_ATTACK_L.png | 阳阳 | ATTACK | L | 112×72 | 25×27 | 水下 | 0b00e079a3f140c08f3f80e06cb89f37cccc61cefd09f300dd1dc28dc6fb8416 |
| sprites/yy_ATTACK_R.png | 阳阳 | ATTACK | R | 112×72 | 25×27 | 水下 | 006e24f602e8ad82fce24643345357eab735eb65d79c55f5e2e2ef0a54beb4c0 |
| sprites/yy_HIT_L.png | 阳阳 | HIT | L | 96×96 | 25×27 | 水下 | 1b1acb9d700974fc80e31fd43c48317bd3ececee2c583258c6be541c11d2e38b |
| sprites/yy_BREATH_L.png | 阳阳 | BREATH | L | 96×96 | 28×27 | 表面 | 126fde05433998c24bd30f6ab1172578ff4d28905512765e799f843445a21524 |
| sprites/dd_SURF_SWIM_L.png | 爸爸 | SURF_SWIM | L | 128×64 | 28×29 | 表面 | d223f966c49156f869d754aebc31f8ffbbf4977f07babf86ed1242bc47a71759 |
| sprites/dd_SURF_SWIM_R.png | 爸爸 | SURF_SWIM | R | 128×64 | 28×29 | 表面 | 4059f3d8cc3da96340ddfcc6523d6459e44bb7a94ddfec0b1ca37d84a813a95e |
| sprites/dd_JUMP_L.png | 爸爸 | JUMP | L | 96×96 | 28×29 | 表面 | 97db1b7c08f31a2a9692326cbc21a96f1f0838e7323a69a20673e57d77738189 |
| sprites/dd_UW_SWIM_L.png | 爸爸 | UW_SWIM | L | 128×64 | 28×29 | 水下 | 1b8b8449d9d29c7ec509a60ea2cc1d73312f342b080297971bae413f91b62a00 |
| sprites/dd_UW_SWIM_R.png | 爸爸 | UW_SWIM | R | 128×64 | 28×29 | 水下 | 73e8a34b8da5d4636d4b0d9a970cb025e899ac43a8ad3a7c0cd2db9063828c21 |
| sprites/dd_ATTACK_L.png | 爸爸 | ATTACK | L | 128×80 | 28×29 | 水下 | cd54de2932747f0b031b419be391fe251a34a2550376718131831ee4e95f4727 |
| sprites/dd_ATTACK_R.png | 爸爸 | ATTACK | R | 128×80 | 28×29 | 水下 | b38d60f7ad8b50cddbbd61c1d8e44ae94da50d78e349af5a3603d24df4c83a74 |
| sprites/dd_HIT_L.png | 爸爸 | HIT | L | 96×96 | 28×29 | 水下 | a5550c0c902528a374f0621776969e9cdefa082527fab95e649df71c37abaa5d |
| sprites/dd_BREATH_L.png | 爸爸 | BREATH | L | 96×96 | 30×29 | 表面 | 644395eabd608830727ed6491241e25b379046d784e418a18b3e18d83f0c416d |

说明：

- 头部尺寸均满足路线草案门槛（阳阳≥约24×24，爸爸≥约28×28）。
- JUMP / HIT / BREATH 只画朝左一个代表方向；SURF_SWIM / UW_SWIM / ATTACK 提供 L/R 双向。R 向由整图最近邻镜像生成，泳镜/眼镜/瞳孔高光按固定左上光源逐点修正（生成器内 hi 锚点机制），不依赖运行时镜像。
- 水下姿态（UW_SWIM / ATTACK / HIT）整体经 manifest.underwaterMapping 青蓝映射，未引入映射外新颜色。

## 2. 审核图（5 张）

| 文件 | 尺寸 | SHA-256 |
|---|---|---|
| 阳阳静态动作表.png | 490×1290 | 69343cb5b4fbf5c64a72dfee7728f80c8878bfa9b14d4375463126136fe2dc3f |
| 爸爸静态动作表.png | 520×1290 | f1c4894502c71daafa77e84a0364690c4a234f3d0a18922f8503323c99e7be69 |
| 双角色1x盲审表.png | 1280×2790 | b488d013c2123513f801186b7432ed97fb0a977200b0930c2cdbb2b7461da3c6 |
| 双角色放大验收表.png | 640×3750 | 34e1aeb69934fcb3f3ae64e840df1287b7766bc7a27c668ce2470fd74baa1161 |
| 游戏观感静态小样.png | 512×448 | 48b869c1efe762ee9cbbfd23cc30e7a5de1f1d428c9e8903af13f83f84fb807d |

- 动作表：每姿态 [1x L | 1x R(若有) | 2x L]。
- 盲审表：18 张匿名编号 #01–#18，每张 1x+3x，无姓名；编号→身份映射见验收记录附录（盲审用，评审前勿看）。
- 放大验收表：每角色每姿态 3x 全图 + 真实头部区域 8x 最近邻裁切。
- 场景小样：512×448（256×224 逻辑 ×2 最近邻），阳阳水面 SURF_SWIM_R、爸爸水下 UW_SWIM_L，含 HUD 比例参照，已标注“STATIC MOCKUP / NOT IN-GAME”。

## 3. 数据文件

- `concept_1a_manifest.json`：schemaVersion=1，stage=CONCEPT-1A，applied=false；含双调色板、水下颜色映射、每精灵 cell/head/sha256、机器检查结果、盲审答案。
