# CONCEPT-MODEL-0 模型清单

- 阶段：CONCEPT-MODEL-0（概念角色标准模型锁定门）
- 分支：concept-style-game　基线 HEAD：0a1bd61（wip-fc-route-before-concept-fork）
- 生成器：`过程文件/Kimi开发/CONCEPT-MODEL-0/build_concept_model_0.py`（确定性，无随机数、无网络、无外部图像输入）
- 人物形象唯一来源：两张本地概念参考图（仅人工观察）；动作来源：本阶段无动作
- 产物性质：标准模型候选，applied=false，未接入任何游戏
- CONCEPT-1A 旧稿画法一律未复用，本阶段全部重新绘制
- 画风：现代 Q 版像素，1px 暖深棕硬描边，平涂+少量像素高光/阴影，alpha 仅 0/255，无抗锯齿
- 光源固定：左上

## 1. 标准稿（12 张，透明 PNG，1x 原生）

| 文件 | 内容 | 画布 | 不透明尺寸 | SHA-256（前16位） |
|---|---|---|---|---|
| sprites/yy_head_front.png | 阳阳正面头 | 28×28 | 28×27 | e36c33952629c57b |
| sprites/yy_head_L.png | 阳阳左侧头 | 28×28 | 25×27 | 90b17d464a60998c |
| sprites/yy_head_R.png | 阳阳右侧头（镜像+高光修正） | 28×28 | 25×27 | 76f6582abf32676e |
| sprites/yy_head_34.png | 阳阳斜侧头 | 28×28 | 26×27 | b29ceeb86e95949b |
| sprites/yy_body_front.png | 阳阳正面全身 | 48×68 | 32×65 | a789d065a85b65da |
| sprites/yy_body_side.png | 阳阳侧面全身 | 36×68 | 25×65 | 8dce08dfa371c80b |
| sprites/dd_head_front.png | 爸爸正面头 | 30×30 | 30×29 | cb2c6ea5404cd470 |
| sprites/dd_head_L.png | 爸爸左侧头 | 30×30 | 26×29 | a7aaa311077494f1 |
| sprites/dd_head_R.png | 爸爸右侧头（镜像+高光修正） | 30×30 | 26×29 | 919a125eb611309f |
| sprites/dd_head_34.png | 爸爸斜侧头 | 30×30 | 28×29 | 6d6810e88848ec97 |
| sprites/dd_body_front.png | 爸爸正面全身 | 52×80 | 39×78 | 77edb3fdbbcbaca8 |
| sprites/dd_body_side.png | 爸爸侧面全身 | 40×80 | 26×78 | c132ee3ec75bdcc6 |

- 头部：阳阳不透明 25–28×27，爸爸 26–30×29，满足路线草案门槛（yy≥约24，dd≥约28）。
- 全身：阳阳 65px、爸爸 78px；头身比 yy=2.41、dd=2.69（总高/头高）。
- 完整 SHA-256 见 `concept_model_0_manifest.json`。

## 2. 审核图（7 张）

| 文件 | 尺寸 | 内容 |
|---|---|---|
| 阳阳标准模型表.png | 816×264 | 四向头 1x+3x；正/侧全身 1x+3x |
| 爸爸标准模型表.png | 848×300 | 同上 |
| 头身比例标尺.png | 400×120 | 以头高为单位的堆叠标尺与实测比值 |
| 固定调色板.png | 560×292 | 28 色色板（名称+HEX） |
| 结构拆解.png | 720×260 | 阳阳帽/分区/镜带/镜片/镜桥；爸爸发/渐变/框/片/镜腿 |
| 身高对照.png | 260×128 | 同基线 10px 刻度实测身高对照 |
| 身份盲审表.png | 820×810 | 12 项匿名灰度稿（8 头 1x+4x，4 全身 1x+3x），隐藏姓名与队色 |

所有放大均为单次最近邻，无平滑。

## 3. 数据文件

- `concept_model_0_manifest.json`：schemaVersion=1，stage=CONCEPT-MODEL-0，applied=false；固定调色板、每稿画布/不透明区/SHA-256、机器检查、盲审答案。
