# 阶段 R3B-I-P1 本人特征小范围验证 清单

- 阶段：R3B-I-P1（本人特征小范围验证，非批量制作）
- 基线：HEAD = 679cb36 `stage3b-m-identity-mask-approved`
- 范围：SURF0-L、JUMP_AIR-L × 阳阳/爸爸 = 4 张测试稿
- 生成器：`过程文件/Kimi开发/R3B-I-P1/build_likeness_sprites_r3bip1.py`
- 生成器 SHA-256：`4ec4b3c20c6e3ced5ebb0c9ffe2e7b4b4cea17a0a183d557e8867b99d6a7b04d`

## 1. 与 R3B-I 的关系

R3B-I 的 12 张身份稿已被用户判定视觉未通过，本轮仅将其作为对照展示输入
（`R3B-I/sprites/*.png`、`R3B-I/identity_sprites_r3bi.json`），
四张候选全部从获批 R3A 人体/动作母版重新逐像素生成，未在旧稿脸上小修小补。

本轮经用户明确授权，放弃"全图 alpha 必须不变"的旧限制，改为严格受限的
"头部肖像例外区域"（见第 3 节）。除此之外的全部 R3A 锁定项（root、画布尺寸、
颈部及以下、身体、动作姿势、visibleBBox 不扩大）保持不变。

## 2. 批准输入（SHA-256 钉值，生成器启动时校验，不符即非零退出）

| 文件 | SHA-256 |
|---|---|
| 过程文件/Kimi开发/sprites_r3a_human_baked.js | bbd40b05f6d7143826f7d554f04deb878a98bf503c09c6fd5bf00c1e612bf7f2 |
| 过程文件/Kimi开发/build_sprites_r3a.py | bffb7e445be037fe5262993393c91e5f33ada7ca5c6eee2a2a629854b075d1be |
| 过程文件/Kimi开发/avatar_paint.py | 615daea6e81acbc60d1e59bf5c83fd4582fd064c35b1d5aa425c1793d7b1194e |
| 过程文件/Kimi开发/阶段3A-R3A人体母版清单.md | f49af48471782e5edbbcc3f01bc90c90eefcd48fb48edb54fdb15fd509c31152 |
| 过程文件/Kimi开发/阶段3A-R3A人体母版验收记录.md | 6c0fe04e5aff1f7aaf6cbd01098f03bfb38cb99bfd4e43f732bee2adeda5e04a |
| 过程文件/Kimi开发/阶段3A-R3A构建复现记录.md | d480a7207fe28344d1e61ec7d1eba0ea85e3e895ddabad4a1b2c8ec3dfd6cec1 |

参考展示输入（非批准输入，不参与绘制）：`R3B-I/identity_sprites_r3bi.json`
及 4 张旧稿 PNG，其 SHA 记入 JSON 的 `inputsSha256` 字段。

隐私资料处理：概念图 `R3B-I-LikenessTest/阳阳爸爸头像方向参考-本地勿提交.png`
与根目录三张家庭照片仅由开发者在构建前人工只读观察，用于提炼特征；
生成器不读取、不复制、不引用它们，构建产物中不含其任何像素或编码。

## 3. 头部肖像例外区域定义

- 区域 = 该姿态 R3A 母版"头部可见包围盒"（y < 颈行 的所有不透明像素的包围盒）
  内的全部像素坐标（含盒内透明孔，允许填肉/耳/帽）。
- 颈行：SURF0 y=10；JUMP_AIR y=12。y ≥ 颈行 = 颈部及以下，禁改。
- 行级规则：y == 颈行-1（头底行）只允许换色，不允许 alpha 增减，
  以保证颈接面形状不变；alpha 变更只发生在 y ≤ 颈行-2。
- 区域逐像素写入 `masks/{POSE}_{char}_L_headregion.png`（4× 品红叠加图）
  与 JSON `sprites.*.headRegion` 坐标列表。
- 连通分量如实计数（4-邻域）。本轮区域为头部包围盒矩形，两姿态均为
  1 个连通分量；这是区域形状的如实结果，未使用"≥1"冒充"=1"的措辞。

实际区域：

| 姿态 | 头部包围盒 | 区域像素数 | 连通分量 |
|---|---|---|---|
| SURF0 | x0..19, y0..9 | 200 | 1 |
| JUMP_AIR | x11..35, y0..11 | 300 | 1 |

注意：JUMP_AIR 头部包围盒 x29..35 列在 y1..11 包含跳跃举臂/拳头像素
（它们位于颈行以上）。设计上这些列全部照抄母版原字符，未改动。

## 4. 身份设计

### 阳阳（yy）：儿童 + 蓝泳帽 + 推在帽上的护目镜

- 泳帽：帽顶区填两档批准蓝 C(#3C9CF0)/c(#1E5AA8)，O 勾边。
- 护目镜推在泳帽上（呼应概念图与泳池照）：帽下缘一条 W 镜框横带 +
  c 深色镜片 + O 瞳点，不遮挡下方眼睛。
- 眼睛：大眼窝 W 底 + O 双瞳 + 高光；位于帽上护目镜之下。
- 儿童比例：脸颊收圆（y8 行左右缘内收）、下巴短（下颌行仅换色收形）、
  小鼻（1px d）、小开口笑（O d O 三像素）。
- 禁止项核对：无第二组眼鼻嘴、无帽子长在脸上（帽与脸之间有明显镜框/肤色分界）、
  无缩小版成年人长下巴。

### 爸爸（dd）：成年 + 短黑发 + 高额头 + 深色粗框眼镜 + 亲切笑

- 不戴帽。短黑发用 O/D 两档（R3A 既有黑/深棕），发际线抬高，
  前额露出大面积 S 肤色 = 高额头。
- 深色粗框眼镜：O 镜框 + W 镜片 + 鼻梁 + 镜腿入鬓发；
  SURF0 为 y6-7 两行，JUMP_AIR 为 y6-7 两行，1× 下黑框白片对比可见。
- 嘴：露齿亲切笑（O 嘴廓 + W 齿线 + d/D 下沿阴影）。
- 无泳帽、无蓝色、无夸张第二张嘴。

## 5. 颜色

仅使用 R3A 表面调色板（O/D/d/s/S/W）+ 阳阳专用两档蓝 C/c。
爸爸稿不含 C/c。无新增颜色。本轮不做水下姿态，无水下颜色映射。

## 6. 产物清单与 SHA-256

| 文件 | SHA-256 |
|---|---|
| build_likeness_sprites_r3bip1.py | 4ec4b3c20c6e3ced5ebb0c9ffe2e7b4b4cea17a0a183d557e8867b99d6a7b04d |
| likeness_sprites_r3bip1.json | 25b0ef8761928277d9d1d860ced7f0dded9c9e1c790704f6150751c3cfc2c7df |
| blind_map.json | 43430cc6cb1803fedc60aa7045638806aa1348e7e7abbe155997159b9489fc1e |
| sprites/SURF0_yy_L.png | 289dd517ebe68f7810cb9d5d045906f7cf06332f8973db9939d92f83b3e8459f |
| sprites/SURF0_dd_L.png | 93d2cb92a6c17ac1a4ed1321b9cd9d34c9dc43c3a4530b8256879ef8580d81cf |
| sprites/JUMP_AIR_yy_L.png | 47af7c94a684512251d21e6b3c1791db8346f35a03099aa79f0ddc9c54a799e7 |
| sprites/JUMP_AIR_dd_L.png | 9c516a42069a90f83c2ce7045a7ca500c9e616c174196e489a81c3392ee32bdf |
| masks/SURF0_yy_L_headregion.png | 26236da99af1c14afa57f619863c79656169e5844fa8f8835e7d1938e15d23d2 |
| masks/SURF0_dd_L_headregion.png | 26236da99af1c14afa57f619863c79656169e5844fa8f8835e7d1938e15d23d2 |
| masks/JUMP_AIR_yy_L_headregion.png | 6b77e03ff7eb6aaac43609e313df3ece56c110822aa46700f49ae11fe0e6f0d5 |
| masks/JUMP_AIR_dd_L_headregion.png | 6b77e03ff7eb6aaac43609e313df3ece56c110822aa46700f49ae11fe0e6f0d5 |
| diff/SURF0_yy_L_inside.png | 3f58e0a8dd59b527092f7539f88cc0247475511e182b0d8a39546cfbd6fadbba |
| diff/SURF0_yy_L_outside.png | 725092c49557011fedd5ad9fe73f1b213fa7c2b09f22aad33bb2315a567f9a7a |
| diff/SURF0_dd_L_inside.png | eb6d4adda00a4d45f94635b857a9ac0cd9d356c62463a3088bdeadd6c46dd3fd |
| diff/SURF0_dd_L_outside.png | 725092c49557011fedd5ad9fe73f1b213fa7c2b09f22aad33bb2315a567f9a7a |
| diff/JUMP_AIR_yy_L_inside.png | 99d45fc18b2367922e587b9b36c3034736b91ceaa724e75b64e3aeaaec2f4d32 |
| diff/JUMP_AIR_yy_L_outside.png | a6fda3eb9bb80fce416832683c3d346d8f05e33e70f9343fb55483b667d244f0 |
| diff/JUMP_AIR_dd_L_inside.png | 3e4468c3bacdb1badee3a6b85fc4cc5347c1914adf4a667b639ac50727e5e413 |
| diff/JUMP_AIR_dd_L_outside.png | a6fda3eb9bb80fce416832683c3d346d8f05e33e70f9343fb55483b667d244f0 |
| 阶段R3B-I-P1本人特征对照表.png | 3f4d89e46ba2fa20dc4c7afb4bae67167b7cf84726fda1518605fc0effbecaee |
| 阶段R3B-I-P1盲审图.png | 75ec0326812cba57725607eb767da09e9a8f1f57d61351011845450bad2b30a6 |

（同一姿态 yy/dd 的蒙版相同、区域外差异证明图同为空图，故 SHA 相同，属预期。）

## 7. 审核图

- `阶段R3B-I-P1本人特征对照表.png`：每稿 9 栏（母版1× / 旧失败稿1× /
  新候选1× / 新候选3× / 新候选8× / 例外区域蒙版 / 区域内差异 /
  区域外差异=0 / 头颈接口8×），行内标注真实像素统计。
- `阶段R3B-I-P1盲审图.png`：#1–#4 固定匿名顺序，每张 1×/3×/8× 全身，
  不含姓名；编号答案见 `blind_map.json` 与验收记录。
- 所有放大均为一次最近邻，无平滑、无抗锯齿、无拉伸。
