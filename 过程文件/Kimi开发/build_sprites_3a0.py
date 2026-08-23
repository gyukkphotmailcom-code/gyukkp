#!/usr/bin/env python3
"""【已废弃／禁止集成】阶段3A-0 R2 历史生成器。

R2 后因人物内部结构和“双脸”视觉问题被撤销。此文件仅保留审计历史；不要用它覆盖
R3A 产物，不要把其 PASS 当作人体视觉通过。当前人体母版生成器为 build_sprites_r3a.py。

历史说明：阶段3A-0 R2 接手返修 — 完整人物精灵生成器与自检。

R2 接手返修要点（承接 Kimi 中断的 R1，并修复错误 UW 证据链）:
 1. 身体内部恢复原版画法: O 轮廓 / K 泳衣黑(渲染同 O, 语义区分) / S,s,d 皮肤 / W 白领·镜;
    队色 T 仅泳衣腰边 1~2px 点缀。证据: jp-action-c.gif(空中)、jp-action-e.gif(水面)、
    美版实机 f12490 单人横泳(水下)。旧 f15625 同框含两人，已明确作废。
 2. 独立 reference mask: 阶段3A0参考/mask_<姿态>.png + mask_<姿态>.json,
    由 --make-mask 从真实参考帧半自动分割+人工清理生成(该模式可读被 ignore 的原版源);
    默认模式只读 mask PNG 计算真实 XOR/union 与最大边界偏差, 如实打印。
 3. 逐像素 identityMask: 只含身份覆盖层像素(眼/嘴/眉 + 阳阳泳帽泳镜 / 爸爸发型眼镜),
    其余全部参与 XOR。
 4. 左右独立锚点 rootByDir + visibleBBoxByDir；root 像素或其 8 邻域必须有效。
    bbox 中心偏移是信息指标，不能为了追求中心对称而破坏脚底/身体中心语义锚。
 5. 真实水面遮挡: 阶段1截图.png NEAREST 1/3 -> 256x224, 分离 y72..101 波纹前景(泡沫色)
    导出 waterOcclusion; 生成 阶段3A0场景验收图.png (+8x 局部放大)。
 6. FACES 强制依赖: import avatar_paint.FACES 且校验文件 SHA-256, 不符即非零退出;
    身份覆盖层像素颜色与相对结构均由 FACES[who][dir]['正常'] 逐段复制而来。
 7. SURF/JUMP 的 R 向与 UW 的 canonical L 均为镜像候选(TBD, 无另一方向原版证据);
    身份层按方向取 FACES 对应母版(有依据差异)。

用法:
  python3 build_sprites_3a0.py                # 自检 + 烘焙 js + 审核表 + 场景验收图
  python3 build_sprites_3a0.py --make-mask    # 一次性: 生成独立 reference mask PNG+JSON
  python3 build_sprites_3a0.py --extract-refs # 一次性: 参考裁剪 + 实机帧裁剪 + 来源清单
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
REF_DIR = BASE / '阶段3A0参考'
OUT_JS = BASE / 'sprites_3a0_baked.js'
OUT_SHEET1 = BASE / '阶段3A0精灵审核表-1.png'
OUT_SHEET2 = BASE / '阶段3A0精灵审核表-2.png'
OUT_SCENE = BASE / '阶段3A0场景验收图.png'
OUT_SCENE_8X = BASE / '阶段3A0场景验收图-8x.png'
STAGE1_SCENE = BASE / '阶段1截图.png'
STAGE1_SHA256 = '3fc267af6974ad9b2838943071f9ac554d16bae5bc2f8d0a82564362cf6ca9ed'

AVATAR_PAINT = BASE / 'avatar_paint.py'
AVATAR_SHA256 = '615daea6e81acbc60d1e59bf5c83fd4582fd064c35b1d5aa425c1793d7b1194e'

# ---------------- 调色 ----------------
# '.' = 透明; O = 轮廓黑; K = 泳衣/内部暗线黑(渲染同 O, 语义区分); T = 队色点缀(按 TEAM)
PAL = {
    'O': '#000000', 'K': '#000000',
    'S': '#FCB88C', 's': '#D88A58', 'd': '#B06840',
    'W': '#FCFCFC',
    'C': '#3C9CF0', 'c': '#1E5AA8',
    'H': '#38241A', 'h': '#5C4030',
    'T': None,
}
TEAM = {'yy': '#3C9CF0', 'dd': '#F83800'}  # 阳阳蓝 / 爸爸红
TEAM_CN = {'yy': '阳阳', 'dd': '爸爸'}

# 水下四档水色(R2 口径): 最深 / 中 / 浅 / 白
UW_MAP = {
    'O': '#004058', 'K': '#004058', 'd': '#004058', 'c': '#004058', 'H': '#004058',
    's': '#3CBCFC', 'C': '#3CBCFC', 'h': '#3CBCFC', 'T': '#3CBCFC',
    'S': '#A4E4FC', 'W': '#FCFCFC',
}

POSES = ['SURF0', 'JUMP_AIR', 'UW_NORMAL']

# ---------------- 清单(manifest) ----------------
MANIFEST = {
    'SURF0': dict(
        cn='水面俯泳', w=31, h=21, root_desc='身体中心',
        mask_png='mask_SURF0.png', mask_json='mask_SURF0.json',
        sourceReference='日版官方宣传图 jp-action-e.gif 人物 abs x105-135/y88-108 朝左(单帧); '
                        '比例/场景对齐辅证: 美版实机帧 f12393(surf0_real_f12393.png)',
        mirrorNote='R向=镜像候选/TBD: 无另一方向原版证据(身份层除外: FACES含已批准双母版)'),
    'JUMP_AIR': dict(
        cn='空中飞扑', w=55, h=42, root_desc='脚底中心',
        mask_png='mask_JUMP_AIR.png', mask_json='mask_JUMP_AIR.json',
        sourceReference='日版官方宣传图 jp-action-c.gif 人物 abs x73-127/y35-76 朝左(单帧); '
                        '美版实机伸展空中帧多轮搜寻未获(仅见收团跳水帧, 姿态不同) -> TBD',
        mirrorNote='R向=镜像候选/TBD: 无另一方向原版证据(身份层除外: FACES含已批准双母版)'),
    'UW_NORMAL': dict(
        cn='横向水下', w=34, h=18, root_desc='身体中心',
        mask_png='mask_UW_NORMAL.png', mask_json='mask_UW_NORMAL.json',
        sourceReference='美版TAS实机视频 实机视频-USA-vjlUJSGGE3g.mp4 0基帧n=12490 '
                        '安全裁剪(129,107,163,125), 人物可见bbox abs x130-161/y108-123; '
                        '源朝右, canonical L=horizontal_flip (压缩源, 容差<=2px/<=15%)',
        mirrorNote='原版直接证据为R向; canonical L由原版R向水平镜像派生; '
                   '尚无独立L向原版轮廓证据(身份层除外: FACES含已批准双母版)'),
}

# 几何容差(回归护栏, 指令口径; 超限即 FAIL 并如实打印)
GEOM_TOL = {'SURF0': (10.0, 1), 'JUMP_AIR': (10.0, 1), 'UW_NORMAL': (15.0, 2)}

# ---------------- FACES 强制依赖 ----------------
def load_faces():
    if not AVATAR_PAINT.exists():
        sys.exit(f'错误: 缺少必需输入 avatar_paint.py ({AVATAR_PAINT})')
    sha = hashlib.sha256(AVATAR_PAINT.read_bytes()).hexdigest()
    if sha != AVATAR_SHA256:
        sys.exit(f'错误: avatar_paint.py SHA-256 不符\n  实际 {sha}\n  要求 {AVATAR_SHA256}')
    sys.path.insert(0, str(BASE))
    from avatar_paint import FACES
    return FACES

# ---------------- 段描述 -> 行 ----------------
def row_from_segments(w, segs):
    r = ['.'] * w
    for x, s in segs:
        for i, c in enumerate(s):
            assert x + i < w, f'段越界 x={x} len={len(s)} w={w}'
            assert r[x + i] == '.', f'段重叠 x={x+i}'
            r[x + i] = c
    return ''.join(r)

def build_rows(w, seg_rows, h):
    rows = [row_from_segments(w, segs) for segs in seg_rows]
    assert len(rows) == h, f'行数 {len(rows)} != {h}'
    return rows

def mirror_rows(rows):
    return [r[::-1] for r in rows]

# ---------------- 身体基础图(中性头, 不含身份像素) ----------------
# 逐像素内部结构依据原版参考: 黑发/白眼窝+黑嘴/白色高领/黑色泳衣/肤色四肢。
# 头区身份(帽/发/镜/眼/嘴)一律由 FACES 覆盖层程序合成, 基础图只画中性头皮/脸部肤色。
# SURF0 31x21: 手 x0-9(举过头顶的回臂手) | 头 x10-19 | 前伸臂 y11 | 黑泳衣 x3-14 y12-19 | 背/拖臂肤 x15-30
SURF0_BASE_SEGS = [
    [(2, 'OOOOOOOOOOOOOOOOO')],                                        # 0
    [(2, 'O'), (3, 'SdSSdS'), (9, 'O'), (10, 'ssssssss'), (18, 'O')],  # 1
    [(0, 'O'), (1, 'SSSSSSSS'), (9, 'O'), (10, 'sssssssss'), (19, 'O')],  # 2
    [(0, 'O'), (1, 'SdSSdSSS'), (9, 'O'), (10, 'sssssssss'), (19, 'O')],  # 3 手指暗缝
    [(0, 'O'), (1, 'SSSSSSSS'), (9, 'O'), (10, 'sssssssss'), (19, 'O')],  # 4
    [(0, 'O'), (1, 'SSSSSSSS'), (9, 'O'), (10, 'sssssssss'), (19, 'O')],  # 5
    [(0, 'O'), (1, 'SSSSSSSS'), (9, 'O'), (10, 'sssssssss'), (19, 'O')],  # 6
    [(0, 'O'), (1, 'SSSSSSSS'), (9, 'O'), (10, 'SSSSSSSS'), (18, 's'), (19, 'O')],  # 7 脸
    [(2, 'O'), (5, 'O'), (6, 'SSSSSSSSSSS'), (17, 's'), (18, 's'), (19, 'O')],  # 8 (x3-4为mask实测空洞, 对齐)
    [(5, 'O'), (6, 'SSSSSSSSSSS'), (17, 's'), (18, 'O')],              # 9 颏
    [(2, 'O'), (3, 'ss'), (5, 'SSSSSSSSSSSSS'), (18, 'ss'), (20, 'O')],  # 10 腕颈肩
    [(2, 'O'), (3, 'SSSSSSSSSSSSSSSSSSSS'), (23, 's'), (24, 'O')],     # 11 前伸臂(水线)
    [(2, 'O'), (3, 'KKKKKKKKKKK'), (14, 'O'), (15, 'SSSSSSSSSS'), (25, 's'), (26, 'O')],  # 12 泳衣起
    [(3, 'O'), (4, 'KKKKKKKKKK'), (14, 'O'), (15, 'SSSSSSSS'), (23, 's'), (24, 'O')],     # 13
    [(3, 'O'), (4, 'K' * 13), (17, 'S'), (18, 'KK'), (20, 'S' * 6), (26, 's'), (27, 'O'), (29, 'O')],  # 14 泳衣扩至x16(对齐jp-action-e) + x29拖臂尖
    [(3, 'O'), (4, 'K' * 13), (17, 'S'), (18, 'KK'), (20, 'S' * 6), (26, 's'), (27, 'O'), (29, 'O')],  # 15
    [(2, 'O'), (3, 'K' * 13), (16, 'S'), (17, 'K'), (18, 'S' * 8), (26, 's'), (27, 'O'), (28, 's'), (29, 'O')],  # 16 (x28连通桥)
    [(1, 'O'), (2, 'K' * 14), (16, 'S'), (17, 'KK'), (19, 'S' * 9), (28, 'O')],  # 17
    [(0, 'O'), (1, 'K' * 13), (14, 'SSS'), (17, 'KK'), (19, 'S' * 10), (29, 's'), (30, 'O')],  # 18
    [(2, 'O'), (3, 'KK'), (5, 'TT'), (7, 'K' * 4), (11, 'd'), (12, 'SSS'), (15, 'KKK'), (18, 'S' * 7), (25, 's'), (26, 'O')],  # 19 腰边T点缀
    [(3, 'O'), (4, 'K'), (5, 'S' * 7), (12, 'd'), (13, 'KK'), (15, 'O')],  # 20
]

# JUMP_AIR 55x42: 头 x11-33 y0-13(黑发/白眼窝/黑嘴由身份层覆盖) | 举臂 x35-48 y0-13
# 左臂 x0-13 y14-31(肤) | 右臂 x36-54 y19-32(肤) | 躯干黑泳衣 K x18-35 y14-32(胸到裆连续)
# 白毛巾/高领 W x13-33 y18-26 胸前U带 | 垂腿 x23-33 y33-39(肤) | 脚 x23-25 y40-41
# 轮廓逐行对齐独立 mask(mask_JUMP_AIR.png 行程); 内部 K/W/S 结构按 jp-action-c.gif 原版画法。
# root=脚底中心 L(24,41)/R(30,41)(语义锚点, 逐方向; bbox 横移为信息指标, 见自检)。
JUMP_BASE_SEGS = [
    [(13, 'O' * 21), (36, 'O' * 8)],                                   # 0 发顶+举手指顶
    [(11, 'OO'), (13, 's' * 20), (33, 'OO'), (35, 'S' * 9), (44, 'O')],  # 1
    [(11, 'O'), (12, 's' * 22), (34, 'O'), (35, 'S'), (36, 'SdSSdSSSSS'), (46, 'O')],  # 2 手指暗缝
    [(11, 'O'), (12, 's' * 22), (34, 'O'), (35, 'S'), (36, 'S' * 10), (46, 'O')],  # 3
    [(11, 'O'), (12, 's' * 22), (34, 'O'), (35, 'SS'), (37, 'S' * 11), (48, 'O')],  # 4
    [(11, 'O'), (12, 's' * 22), (34, 'O'), (35, 'SS'), (37, 'S' * 11), (48, 'O')],  # 5
    [(11, 'O'), (12, 's' * 22), (34, 'O'), (35, 'SS'), (37, 'S' * 11), (48, 'O')],  # 6
    [(11, 'O'), (12, 'S' * 22), (34, 'O'), (35, 'SS'), (37, 'S' * 9), (46, 'O')],  # 7 脸(中性)
    [(11, 'O'), (12, 'S' * 22), (34, 'O'), (35, 'SS'), (37, 'S' * 9), (46, 'O')],  # 8
    [(11, 'O'), (12, 'S' * 26), (38, 'SSSSSS'), (44, 'O')],            # 9
    [(11, 'O'), (12, 'S' * 28), (40, 'SS'), (42, 'O')],                # 10
    [(11, 'O'), (12, 'S' * 28), (40, 'SS'), (42, 'O')],                # 11
    [(9, 'OO'), (11, 'S' * 29), (40, 'O')],                            # 12
    [(9, 'OO'), (11, 'S' * 29), (40, 'O')],                            # 13
    [(4, 'OOOO'), (8, 'S' * 6), (14, 'S' * 4), (18, 'K' * 14), (32, 'S' * 6), (38, 'O')],  # 14 左臂起+肩上泳衣
    [(2, 'OO'), (4, 'S' * 10), (14, 'S' * 4), (18, 'K' * 14), (32, 'S' * 6), (38, 'O')],  # 15
    [(1, 'OO'), (3, 'S' * 11), (14, 'S' * 4), (18, 'K' * 14), (32, 'S' * 5), (37, 'O')],  # 16
    [(0, 'OO'), (2, 'S' * 12), (14, 'S' * 4), (18, 'K' * 14), (32, 'S' * 5), (37, 'O')],  # 17
    [(0, 'O'), (1, 'S' * 12), (13, 'WW'), (15, 'SSS'), (18, 'K' * 11), (29, 'WWW'), (32, 'S' * 5), (37, 'O')],  # 18 毛巾尾起
    [(0, 'O'), (1, 'S' * 12), (13, 'WWW'), (16, 'KK'), (18, 'K' * 13), (31, 'WW'), (33, 'KKK'), (36, 'S' * 9), (45, 'O'), (46, 'S'), (53, 'OO')],  # 19 右臂+右手尖
    [(0, 'O'), (1, 'S' * 12), (13, 'WWW'), (16, 'K' * 16), (32, 'WWW'), (35, 'K'), (36, 'S' * 10), (46, 'O' * 9)],  # 20
    [(0, 'O'), (1, 'S' * 11), (12, 'K'), (13, 'WWWW'), (17, 'K' * 12), (29, 'WWWW'), (33, 'KKK'), (36, 'S' * 17), (54, 'O')],  # 21
    [(0, 'O'), (1, 'S' * 11), (12, 'K'), (13, 'WWWWW'), (18, 'K' * 10), (28, 'WWWWWW'), (34, 'KK'), (36, 'S' * 17), (54, 'O')],  # 22
    [(0, 'O'), (1, 'S' * 11), (12, 'K'), (13, 'WWWWW'), (18, 'K' * 9), (27, 'WWWWWWW'), (34, 'KK'), (36, 'S' * 17), (54, 'O')],  # 23
    [(0, 'O'), (1, 'S' * 11), (12, 'KK'), (14, 'W' * 18), (32, 'KKK'), (35, 'K'), (36, 'S' * 17), (54, 'O')],  # 24 毛巾最宽
    [(0, 'O'), (1, 'S' * 11), (12, 'KKK'), (15, 'W' * 16), (31, 'KKKK'), (35, 'K'), (36, 'S' * 18), (54, 'O')],  # 25
    [(0, 'O'), (1, 'S' * 11), (12, 'K' * 6), (18, 'W' * 11), (29, 'K' * 6), (35, 'O'), (36, 'S' * 16), (52, 'O')],  # 26 毛巾尾收
    [(0, 'O' * 14), (23, 'K' * 12), (35, 'O'), (36, 'S' * 16), (52, 'O')],  # 27 左后肢尖收
    [(0, 'O' * 9), (23, 'K' * 12), (35, 'O'), (36, 'S' * 16), (52, 'O')],   # 28
    [(0, 'O' * 9), (23, 'K' * 12), (35, 'O'), (36, 'S' * 16), (52, 'O')],   # 29
    [(0, 'O' * 9), (23, 'K' * 12), (35, 'O'), (36, 'S' * 16), (52, 'O')],   # 30
    [(0, 'O' * 7), (23, 'K' * 12), (35, 'O'), (36, 'S' * 14), (50, 'O')],   # 31
    [(23, 'OOO'), (26, 'K' * 14), (40, 'O'), (41, 'S' * 9), (50, 'O')],     # 32 躯干底
    [(23, 'OOO'), (26, 'S' * 7), (33, 'O')],                           # 33 垂腿起
    [(23, 'OO'), (25, 'S' * 6), (31, 'O')],                            # 34
    [(23, 'OO'), (25, 'SSSdSS'), (31, 'O')],                           # 35 双腿暗缝
    [(23, 'OO'), (25, 'SSSdSS'), (31, 'O')],                           # 36
    [(23, 'OO'), (25, 'S' * 4), (29, 'O')],                            # 37
    [(23, 'OO'), (25, 'S' * 4), (29, 'O')],                            # 38
    [(23, 'OO'), (25, 'SS'), (27, 'O')],                               # 39
    [(23, 'O'), (24, 'S'), (25, 'O')],                                 # 40 脚(对齐 mask x23-25)
    [(23, 'OOO')],                                                     # 41 脚底(对齐 mask x23-25)
]

# UW_NORMAL 34x18: 由 f12490 单人原生裁剪经背景差分取得完整轮廓，再按原帧
# 水下四档色就近映射为 O/K/W/S/s。它是一体化横泳人体，不再复用旧 f15625 的
# 65x22 双人合体轮廓。身份层只替换头部内部颜色，不改变该轮廓。
UW_BASE_ROWS = [
    '..................................',
    '......OO.OOOOOOOOOOOOssssOO.......',
    '......OKOKKKKKKKKKKKKssssKKO......',
    '....OOKKKKKKKKKKKKKKKKKKKsKO......',
    '.....OKKKKKKSWWsKKKKKKKKKKKKOOOOO.',
    '.....OKKWWKKWWKWWKKKKKKKKKKsssKKO.',
    '....OOKWWWWKWWWWSKsssKssKKKKsssKO.',
    '......OWKSSsSSSSKssssssssKKKsssKO.',
    '......OWWSSssSWKsssssssssKKKsssKO.',
    '.....OKKSSssssKKsssssssssKKKsssKO.',
    '...OOssKsssssKsKsssssssssKKKsssKO.',
    '..OssssKsssKKKssKssssKssKKKKssKO..',
    '.OssssKKssKssKsssOOOOOOOOOOOOOO...',
    '.OsssssKKKssKsssO.................',
    '.OssssssKKOOOOOOO.................',
    '.OssssKOOO........................',
    '..OOOOO...........................',
    '..................................',
]

# ---------------- 锚点(rootByDir; R向 = 镜像 x) ----------------
# 语义锚点, 逐方向: SURF0/UW_NORMAL=身体中心; JUMP_AIR=脚底中心(mask 实测脚点 (24,41), R=(30,41))
ANCHOR_L = {'SURF0': (15, 10), 'JUMP_AIR': (24, 41), 'UW_NORMAL': (17, 9)}

def anchor(pose, w, d):
    x, y = ANCHOR_L[pose]
    return (w - 1 - x, y) if d == 'R' else (x, y)

# ---------------- 身份覆盖层(逐像素复制自已批准 FACES 母版) ----------------
# 段: (sy, sx, fy, fx, n) — L向: grid[sy][sx+i] = FACES[who]['left'][fy][fx+i]
#                           R向: grid[sy][W-1-sx-i] = FACES[who]['right'][fy][23-fx-i]
# 仅 '正常' 表情; 帽/发/镜/眼/嘴全部来自母版, 位置按姿态头区人工放置(证据见清单)。
IDENTITY_RUNS = {
    ('SURF0', 'yy'): [
        (1, 10, 4, 7, 8), (2, 10, 5, 7, 9), (3, 10, 5, 7, 9),
        (4, 10, 9, 7, 9), (5, 10, 9, 7, 9), (6, 10, 10, 8, 9),
        (7, 10, 6, 7, 5), (8, 10, 7, 7, 5),
        (9, 11, 19, 11, 3),
    ],
    ('SURF0', 'dd'): [
        (1, 10, 3, 8, 8), (2, 10, 2, 8, 9), (3, 10, 3, 7, 9),
        (4, 16, 4, 17, 3), (5, 16, 4, 17, 3),
        (6, 10, 10, 2, 5), (7, 10, 11, 4, 5),
        (9, 11, 17, 8, 3),
    ],
    ('JUMP_AIR', 'yy'): [
        (1, 13, 4, 7, 9), (1, 22, 5, 7, 9), (1, 31, 5, 7, 2),
        (2, 12, 5, 7, 9), (2, 21, 5, 7, 9), (2, 30, 5, 7, 4),
        (3, 12, 5, 7, 9), (3, 21, 5, 7, 9), (3, 30, 5, 7, 4),
        (4, 12, 9, 7, 9), (4, 21, 9, 7, 9), (4, 30, 9, 7, 4),
        (5, 12, 9, 7, 9), (5, 21, 9, 7, 9), (5, 30, 9, 7, 4),
        (6, 12, 10, 8, 9), (6, 21, 10, 8, 9), (6, 30, 10, 8, 4),
        (7, 12, 6, 7, 5), (8, 12, 7, 7, 5), (9, 12, 8, 7, 5),
        (11, 13, 19, 11, 3),
    ],
    ('JUMP_AIR', 'dd'): [
        (1, 13, 3, 8, 8), (1, 21, 2, 8, 9), (1, 30, 3, 8, 3),
        (2, 12, 2, 8, 9), (2, 21, 2, 8, 9), (2, 30, 2, 8, 4),
        (3, 12, 3, 7, 9), (3, 21, 3, 7, 9), (3, 30, 3, 7, 4),
        (4, 28, 4, 17, 4), (5, 29, 4, 17, 3), (6, 29, 4, 17, 3),
        (7, 12, 10, 2, 5), (8, 12, 11, 4, 5), (9, 12, 12, 4, 5),
        (11, 13, 17, 8, 6),
    ],
    ('UW_NORMAL', 'yy'): [
        (2, 7, 4, 8, 8), (3, 6, 5, 8, 8), (4, 6, 6, 8, 8),
        (5, 6, 7, 8, 8), (6, 6, 8, 8, 8), (7, 6, 9, 8, 8),
        (8, 7, 15, 8, 7), (9, 7, 16, 8, 7), (10, 8, 19, 11, 3),
    ],
    ('UW_NORMAL', 'dd'): [
        (2, 7, 2, 8, 8), (3, 6, 3, 8, 8), (4, 6, 4, 8, 8),
        (5, 6, 5, 8, 8), (6, 6, 6, 8, 8), (7, 6, 9, 8, 8),
        (8, 7, 10, 8, 7), (9, 7, 11, 8, 7), (10, 8, 17, 9, 5),
    ],
}

BASE_SEGS = {'SURF0': SURF0_BASE_SEGS, 'JUMP_AIR': JUMP_BASE_SEGS}

def build_base(pose):
    w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
    if pose == 'UW_NORMAL':
        assert len(UW_BASE_ROWS) == h and all(len(r) == w for r in UW_BASE_ROWS)
        return UW_BASE_ROWS[:]
    return build_rows(w, BASE_SEGS[pose], h)

def build_sprite(pose, who, d, faces):
    """返回 (rows, identityMask:set[(x,y)])。R向 = 基础行镜像 + 右母版镜像位覆盖。"""
    w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
    rows = build_base(pose)
    if d == 'R':
        rows = mirror_rows(rows)
    grid = [list(r) for r in rows]
    face = faces[who]['left' if d == 'L' else 'right']['正常']
    idm = set()
    for sy, sx, fy, fx, n in IDENTITY_RUNS[(pose, who)]:
        for i in range(n):
            c = face[fy][fx + i] if d == 'L' else face[fy][23 - fx - i]
            if c == '.':
                continue
            tx = sx + i if d == 'L' else w - 1 - sx - i
            assert 0 <= tx < w and 0 <= sy < h, f'身份段越界 {pose} {who} {d} ({tx},{sy})'
            assert grid[sy][tx] != '.', f'身份段落在透明区 {pose} {who} {d} ({tx},{sy})'
            grid[sy][tx] = c
            idm.add((tx, sy))
    # 覆盖色 ⊆ FACES 调色(共用+本人特有色) — 结构上由复制保证, 此处断言留档
    allowed = set('OSsdWCcHh')
    assert all(grid[y][x] in allowed for x, y in idm), '身份覆盖含非 FACES 色'
    return [''.join(r) for r in grid], idm

def sprite_pts(rows):
    return {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}

def render(rows, team, mapping=None):
    """mapping=None 用 PAL(队色 T 按 TEAM[team]); 否则用给定映射(如 UW_MAP)。"""
    w, h = len(rows[0]), len(rows)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '.':
                continue
            if mapping is not None:
                col = mapping[c]
            elif c == 'T':
                col = TEAM[team]
            else:
                col = PAL[c]
            rgb = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))
            px[x, y] = rgb + (255,)
    return im

# ---------------- 独立 reference mask 读写 ----------------
def mask_path(pose):
    return REF_DIR / MANIFEST[pose]['mask_png']

def mask_meta_path(pose):
    return REF_DIR / MANIFEST[pose]['mask_json']

def save_mask(pose, pts):
    w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
    im = Image.new('1', (w, h), 0)
    px = im.load()
    for x, y in pts:
        px[x, y] = 1
    im.save(mask_path(pose))

def load_mask(pose):
    w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
    p = mask_path(pose)
    jp = mask_meta_path(pose)
    if not p.exists() or not jp.exists():
        sys.exit(f'错误: 缺少独立 mask/JSON {p} / {jp} (先跑 --make-mask)')
    with Image.open(p) as raw:
        assert raw.mode == '1', f'{pose} mask 原始模式 {raw.mode} != 1（禁止静默阈值化）'
        assert raw.size == (w, h), f'{pose} mask 尺寸 {raw.size} != {(w, h)}'
        im = raw.copy()
    px = im.load()
    pts = {(x, y) for y in range(h) for x in range(w) if px[x, y]}
    assert pts, f'{pose} mask 为空'

    meta = json.loads(jp.read_text(encoding='utf-8'))
    spec = REFERENCE_SPECS[pose]
    required = {
        'schemaVersion', 'pose', 'width', 'height', 'sourceFile', 'sourceSha256',
        'sourceOriginalSize', 'frameIndex', 'frameBase', 'fps', 'maskCropBox',
        'sourceFacing', 'normalizedFacing', 'transform', 'recipeId', 'recipeVersion',
        'cleanupLog', 'pixels', 'visibleBBox', 'maskSha256',
        'referenceCropFile', 'referenceCropSha256',
    }
    missing = required - set(meta)
    assert not missing, f'{pose} mask JSON 缺字段 {sorted(missing)}'
    expected = {
        'schemaVersion': 2, 'pose': pose, 'width': w, 'height': h,
        'sourceFile': spec['sourceFile'], 'sourceSha256': spec['sourceSha256'],
        'sourceOriginalSize': list(spec['sourceOriginalSize']),
        'frameIndex': spec['frameIndex'], 'frameBase': 0, 'fps': spec['fps'],
        'maskCropBox': list(spec['maskCropBox']),
        'sourceFacing': spec['sourceFacing'], 'normalizedFacing': spec['normalizedFacing'],
        'transform': spec['transform'], 'recipeId': spec['recipeId'],
        'recipeVersion': spec['recipeVersion'], 'referenceCropFile': spec['referenceCropFile'],
    }
    for key, value in expected.items():
        assert meta[key] == value, f'{pose} mask JSON {key}={meta[key]!r} != {value!r}'
    assert isinstance(meta['cleanupLog'], list), f'{pose} cleanupLog 必须为列表'
    assert meta['pixels'] == len(pts), f'{pose} JSON pixels={meta["pixels"]} != {len(pts)}'
    assert meta['visibleBBox'] == list(visible_bbox(pts)), f'{pose} JSON visibleBBox 不符'
    actual_mask_sha = sha256_file(p)
    assert meta['maskSha256'] == actual_mask_sha, f'{pose} JSON maskSha256 不符'
    locked = MASK_SHA256_LOCKS.get(pose)
    if locked:
        assert actual_mask_sha == locked, f'{pose} mask SHA 锁不符 {actual_mask_sha} != {locked}'
    ref_crop = REF_DIR / meta['referenceCropFile']
    assert ref_crop.exists(), f'{pose} 缺参考原生裁剪 {ref_crop}'
    with Image.open(ref_crop) as ref_im:
        assert ref_im.size == (w, h), f'{pose} 参考裁剪尺寸 {ref_im.size} != {(w,h)}'
    actual_ref_sha = sha256_file(ref_crop)
    assert meta['referenceCropSha256'] == actual_ref_sha, f'{pose} referenceCrop SHA 不符'
    locked_ref = REFERENCE_CROP_SHA256_LOCKS.get(pose)
    if locked_ref:
        assert actual_ref_sha == locked_ref, f'{pose} 参考裁剪 SHA 锁不符'
    source = spec['sourcePath']
    if source.exists():
        assert sha256_file(source) == spec['sourceSha256'], f'{pose} 原始来源 SHA 不符'
    if pose == 'UW_NORMAL':
        assert meta.get('backgroundFrameIndex') == spec['backgroundFrameIndex']
        assert meta.get('diffThreshold') == spec['diffThreshold']
        for file_key, sha_key in (
            ('sourceCropFile', 'sourceCropSha256'),
            ('backgroundCropFile', 'backgroundCropSha256'),
        ):
            aux = REF_DIR / meta[file_key]
            assert aux.exists() and sha256_file(aux) == meta[sha_key], f'UW {file_key} SHA 不符'
            assert meta[sha_key] == UW_DIFF_CROP_SHA256_LOCKS[sha_key], \
                f'UW {sha_key} 代码锁不符'
    return pts

# ---------------- 几何统计 ----------------
def xor_stats(a, b):
    inter = len(a & b)
    union = len(a | b)
    xor = len(a ^ b)
    return xor, union, (100.0 * xor / union) if union else 0.0

def max_boundary_dev(a, b):
    """对称最大偏差: max( max_{p in a} dist(p,b), max_{q in b} dist(q,a) ), 欧氏距离。"""
    if not a or not b:
        return float('inf')
    def directed(src, dst):
        dl = list(dst)
        worst = 0.0
        for x, y in src:
            d2 = min((x - u) ** 2 + (y - v) ** 2 for u, v in dl)
            worst = max(worst, d2)
        return worst ** 0.5
    return max(directed(a, b), directed(b, a))

def components4(pts):
    rest = set(pts)
    n = 0
    while rest:
        n += 1
        stack = [rest.pop()]
        while stack:
            x, y = stack.pop()
            for q in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if q in rest:
                    rest.discard(q)
                    stack.append(q)
    return n

def visible_bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))

# ================= 一次性构建期模式(可读被 .gitignore 排除的原版源) =================
SRC_DIR = BASE.parent / '原版参考'
MP4_USA = SRC_DIR / '实机视频-USA-vjlUJSGGE3g.mp4'
GIF_E = SRC_DIR / '官方截图' / 'jp-action-e.gif'
GIF_C = SRC_DIR / '官方截图' / 'jp-action-c.gif'

REFERENCE_SPECS = {
    'SURF0': dict(
        sourcePath=GIF_E, sourceFile='原版参考/官方截图/jp-action-e.gif',
        sourceSha256='698d51036ec2fc82ac1c40fa4cdcd784dda5192bca95a7b378d575f449712f72',
        sourceOriginalSize=(256, 192), frameIndex=None, fps=None,
        maskCropBox=(105, 88, 136, 109), sourceFacing='L', normalizedFacing='L',
        transform='none', recipeId='gif-color-seed-explicit-cleanup', recipeVersion=2,
        referenceCropFile='surf0_mask_source.png'),
    'JUMP_AIR': dict(
        sourcePath=GIF_C, sourceFile='原版参考/官方截图/jp-action-c.gif',
        sourceSha256='75c2d446adaaa15a46e9bc8bcaf47a483dfb2502095dc581ed68e9b6680ba077',
        sourceOriginalSize=(256, 192), frameIndex=None, fps=None,
        maskCropBox=(73, 35, 128, 77), sourceFacing='L', normalizedFacing='L',
        transform='none', recipeId='gif-color-seed-explicit-cleanup', recipeVersion=2,
        referenceCropFile='jump_mask_source.png'),
    'UW_NORMAL': dict(
        sourcePath=MP4_USA, sourceFile='原版参考/实机视频-USA-vjlUJSGGE3g.mp4',
        sourceSha256='55f9a922a0ceef249f29f529416c0980476da29a89713cdfe194a89027b27e37',
        sourceOriginalSize=(256, 224), frameIndex=12490, fps=30,
        maskCropBox=(129, 107, 163, 125), sourceFacing='R', normalizedFacing='L',
        transform='horizontal_flip', recipeId='temporal-bg-diff-largest-4conn', recipeVersion=2,
        backgroundFrameIndex=12504, diffThreshold=25, referenceCropFile='uw_ref.png'),
}

# 由 --make-mask / --extract-refs 的确定性产物反向钉死；R2首次生成后填入。
MASK_SHA256_LOCKS = {
    'SURF0': 'f9c509b6e481b5f345e8b3463fc41851c9551ce3c1ee6c80a14e8a3b1512279f',
    'JUMP_AIR': 'a8664813fdc9c32f4a7fd87618b99b679667caaf605ba8e552a66ab8cc939409',
    'UW_NORMAL': 'd41391db8af762f0e25321030de6bc6bcb8a12f3ad69f6b0695aae082c44005d',
}
REFERENCE_CROP_SHA256_LOCKS = {
    'SURF0': 'e7665833b0f755785faab35442225789a0d3b0ba8b0995c7d0c4b416a07afa4c',
    'JUMP_AIR': '8ac663c4c78846ce8f20825517aca38d01573c0e24d9f62bbb6ad7d95f55b81a',
    'UW_NORMAL': 'c57df23e374b784e1138b66db8e7601f4f9e9bc7a48bc5b4ab19211c0320f74c',
}
UW_DIFF_CROP_SHA256_LOCKS = {
    'sourceCropSha256': '48db7259f6aab0bc117af1bb693bd4ecd0da390235a1ac99f31a8009a7b3b9dd',
    'backgroundCropSha256': '33a6133633c319ff2471bb15cdf78c1b13c5d8f68cfc1bda022319d2bf6f1a80',
}

def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def extract_frame(mp4, n, out_png):
    """用 imageio-ffmpeg 自带的 ffmpeg 精确抽帧(0基帧号)。"""
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [exe, '-y', '-i', str(mp4), '-vf', f'select=eq(n\\,{n})', '-frames:v', '1', str(out_png)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not Path(out_png).exists():
        sys.exit(f'抽帧失败 n={n}: {r.stderr.decode()[-400:]}')

def _neigh8(pts, p):
    x, y = p
    return [q for q in [(x+dx, y+dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)] if q in pts]

def _largest_comp(pts):
    rest = set(pts)
    best = set()
    while rest:
        stack = [rest.pop()]
        comp = {stack[0]}
        while stack:
            for q in _neigh8(rest, stack.pop()):
                rest.discard(q)
                comp.add(q)
                stack.append(q)
        if len(comp) > len(best):
            best = comp
    return best

def _components4_sets(pts):
    rest = set(pts)
    comps = []
    while rest:
        stack = [rest.pop()]
        comp = {stack[0]}
        while stack:
            x, y = stack.pop()
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in rest:
                    rest.remove(q)
                    comp.add(q)
                    stack.append(q)
        comps.append(comp)
    return sorted(comps, key=lambda c: (-len(c), min(c) if c else (0, 0)))

def _fill_holes(pts, w, h):
    bg = {(x, y) for y in range(h) for x in range(w)} - pts
    outside = set()
    stack = [(x, y) for x in range(w) for y in range(h)
             if (x in (0, w - 1) or y in (0, h - 1)) and (x, y) in bg]
    while stack:
        p = stack.pop()
        if p in outside or p not in bg:
            continue
        outside.add(p)
        stack += _neigh8(bg, p)
    holes = bg - outside
    return pts | holes, holes

def _rect_remove(pts, x0, y0, x1, y1):
    return {p for p in pts if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1)}

def _rect_fill(pts, x0, y0, x1, y1):
    return pts | {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}

def _majority_smooth(pts, w, h, iters=2, thr=5):
    for _ in range(iters):
        new = set(pts)
        for y in range(h):
            for x in range(w):
                n = sum((x+dx, y+dy) in pts for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0))
                if (x, y) in pts:
                    if n <= 1:
                        new.discard((x, y))
                elif n >= thr:
                    new.add((x, y))
        pts = new
    return pts

def mask_surf(px):
    """jp-action-e.gif 裁剪 (105,88,136,109): 肤/黑种子 + 2轮白吸附 + 人工清理。"""
    W, H = 31, 21
    seed, white = set(), set()
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            if (r > 150 and r > b + 40 and g < 205) or max(r, g, b) < 70:
                seed.add((x, y))
            elif r > 225 and g > 225 and b > 225:
                white.add((x, y))
    pts = set(seed)
    for _ in range(2):
        for q in list(white):
            if q not in pts and _neigh8(pts, q):
                pts.add(q)
    comp = _largest_comp(pts)
    log = []
    for p in sorted(comp):
        x, y = p
        r, g, b = px[x, y]
        if r > 225 and g > 225 and b > 225 and not (10 <= x <= 18 and 5 <= y <= 10):
            comp.discard(p)
            log.append(f'去水沫白点 ({x},{y}) [眼周x10-18 y5-10以外的高亮白判为水面反光]')
    comp, holes = _fill_holes(comp, W, H)
    log.append(f'填内部洞 {len(holes)}px: {sorted(holes)}')
    for box in [(5, 10, 5, 10), (17, 10, 18, 10), (20, 11, 20, 12), (17, 13, 19, 13),
                (12, 19, 13, 19), (12, 20, 15, 20)]:
        comp = _rect_fill(comp, *box)
        log.append(f'补AA断缝 {box} [原图抗锯齿造成的真实身体连通缝]')
    for p in [(19, 20), (30, 19)]:
        if p in comp:
            comp.discard(p)
            log.append(f'去孤立残点 {p} [与主体无4/8连通的水沫]')
    return comp, log

def mask_jump(px):
    """jp-action-c.gif 裁剪 (73,35,128,77): 排除跳台蓝, 肤/黑/白/暗种子 + 人工清理。"""
    W, H = 55, 42
    pts = set()
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            if (r, g, b) == (65, 0, 230):
                continue  # 跳台蓝
            if b > 150 and r < 120:
                continue  # 天空/水蓝
            if (r > 150 and r > b + 40 and g < 205) or max(r, g, b) < 70 \
               or (r > 225 and g > 225 and b > 225) or (max(r, g, b) < 150 and not (b > r + 30)):
                pts.add((x, y))
    comp = _largest_comp(pts)
    log = []
    for box in [(0, 32, 13, 41), (14, 27, 22, 41), (0, 0, 10, 1)]:
        n0 = len(comp)
        comp = _rect_remove(comp, *box)
        log.append(f'去跳台/梯子区 {box} 移除{n0 - len(comp)}px [对照原图确认为设施]')
    comp, holes = _fill_holes(comp, W, H)
    log.append(f'填内部洞 {len(holes)}px: {sorted(holes)}')
    n0 = len(comp)
    comp = _rect_remove(comp, 11, 28, 12, 31)
    log.append(f'去台沿残点 x11-12 y28-31 移除{n0 - len(comp)}px')
    return comp, log

def mask_uw(fg, bg):
    """f12490 单人帧减同景空背景 f12504；取最大4连通体后镜像为 canonical L。"""
    W, H = 34, 18
    threshold = REFERENCE_SPECS['UW_NORMAL']['diffThreshold']
    diff = set()
    for y in range(H):
        for x in range(W):
            a, b = fg.getpixel((x, y)), bg.getpixel((x, y))
            if max(abs(a[i] - b[i]) for i in range(3)) >= threshold:
                diff.add((x, y))
    comps = _components4_sets(diff)
    assert comps, 'UW 背景差分未得到任何像素'
    main = comps[0]
    discarded = [len(c) for c in comps[1:]]
    pts = {(W - 1 - x, y) for x, y in main}  # source R -> canonical L
    log = [
        f'f12490 - f12504 RGB最大通道差阈值>={threshold}',
        f'取最大4连通体 {len(main)}px；丢弃其余压缩/池壁噪点分量 {discarded}',
        '源朝右，水平镜像为 canonical L；未填洞、未平滑、未拉伸',
    ]
    return pts, log

def _write_mask_meta(pose, pts, cleanup_log, extra=None):
    spec = REFERENCE_SPECS[pose]
    save_mask(pose, pts)
    ref_crop = REF_DIR / spec['referenceCropFile']
    assert ref_crop.exists(), f'{pose} 缺参考裁剪 {ref_crop}'
    meta = dict(
        schemaVersion=2, pose=pose, width=MANIFEST[pose]['w'], height=MANIFEST[pose]['h'],
        sourceFile=spec['sourceFile'], sourceSha256=spec['sourceSha256'],
        sourceOriginalSize=list(spec['sourceOriginalSize']), frameIndex=spec['frameIndex'],
        frameBase=0, fps=spec['fps'], maskCropBox=list(spec['maskCropBox']),
        sourceFacing=spec['sourceFacing'], normalizedFacing=spec['normalizedFacing'],
        transform=spec['transform'], recipeId=spec['recipeId'], recipeVersion=spec['recipeVersion'],
        cleanupLog=cleanup_log, pixels=len(pts), visibleBBox=list(visible_bbox(pts)),
        maskSha256=sha256_file(mask_path(pose)), referenceCropFile=spec['referenceCropFile'],
        referenceCropSha256=sha256_file(ref_crop),
    )
    if extra:
        meta.update(extra)
    mask_meta_path(pose).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def make_mask_mode():
    REF_DIR.mkdir(exist_ok=True)
    gif_specs = [('SURF0', mask_surf), ('JUMP_AIR', mask_jump)]
    for pose, fn in gif_specs:
        spec = REFERENCE_SPECS[pose]
        src, box = spec['sourcePath'], spec['maskCropBox']
        assert sha256_file(src) == spec['sourceSha256'], f'{pose} 原件 SHA 不符'
        im = Image.open(src).convert('RGB')
        assert im.size == spec['sourceOriginalSize'], f'{pose} 原件尺寸不符'
        crop = im.crop(box)
        crop.save(REF_DIR / spec['referenceCropFile'])
        pts, log = fn(crop.load())
        _write_mask_meta(pose, pts, log, {
            'sourceVersion': '日版官方宣传图',
            'generation': '颜色种子+独立连通分量+显式人工清理；全部步骤见 cleanupLog',
            'evidenceLimit': '静态宣传图单帧，只证明姿态/轮廓，不证明时序',
        })
        print(f'[make-mask] {pose}: n={len(pts)} 清理{len(log)}条 -> {mask_path(pose).name}')

    spec = REFERENCE_SPECS['UW_NORMAL']
    assert sha256_file(MP4_USA) == spec['sourceSha256'], 'UW 原视频 SHA 不符'
    with tempfile.TemporaryDirectory(prefix='3a0-mask-') as td:
        td = Path(td)
        fg_path, bg_path = td / 'f12490.png', td / 'f12504.png'
        extract_frame(MP4_USA, spec['frameIndex'], fg_path)
        extract_frame(MP4_USA, spec['backgroundFrameIndex'], bg_path)
        fg_full, bg_full = Image.open(fg_path).convert('RGB'), Image.open(bg_path).convert('RGB')
        assert fg_full.size == bg_full.size == spec['sourceOriginalSize']
        source_r = fg_full.crop(spec['maskCropBox'])
        bg_r = bg_full.crop(spec['maskCropBox'])
        source_r.save(REF_DIR / 'uw_ref_source_R.png')
        bg_r.save(REF_DIR / 'uw_bg_f12504.png')
        source_l = source_r.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        source_l.save(REF_DIR / spec['referenceCropFile'])
        pts, log = mask_uw(source_r, bg_r)
    _write_mask_meta('UW_NORMAL', pts, log, {
        'sourceVersion': '美版TAS实机录制', 'backgroundFrameIndex': spec['backgroundFrameIndex'],
        'diffThreshold': spec['diffThreshold'], 'sourceCropFile': 'uw_ref_source_R.png',
        'sourceCropSha256': sha256_file(REF_DIR / 'uw_ref_source_R.png'),
        'backgroundCropFile': 'uw_bg_f12504.png',
        'backgroundCropSha256': sha256_file(REF_DIR / 'uw_bg_f12504.png'),
        'generation': '同景空背景逐像素差分 + 最大4连通体 + 明示水平镜像；无填洞/平滑/缩放',
        'evidenceLimit': '30fps压缩源；几何容差<=2px/<=15%；美版调色不外推日版精确色',
        'rejectedPriorEvidence': '0基f15625 crop(60,114,125,136)含两人接触，旧65x22 mask作废',
    })
    print(f'[make-mask] UW_NORMAL: n={len(pts)} 清理{len(log)}条 -> mask_UW_NORMAL.png')

def extract_refs_mode():
    """生成审核参考、精确mask裁剪、UW背景/辅证帧和来源清单。"""
    REF_DIR.mkdir(exist_ok=True)
    for pose, spec in REFERENCE_SPECS.items():
        assert spec['sourcePath'].exists(), f'缺来源 {spec["sourcePath"]}'
        assert sha256_file(spec['sourcePath']) == spec['sourceSha256'], f'{pose} 来源 SHA 不符'
    im = Image.open(GIF_E).convert('RGB')
    im.crop((96, 86, 142, 114)).save(REF_DIR / 'surf0_ref.png')
    im.crop(REFERENCE_SPECS['SURF0']['maskCropBox']).save(REF_DIR / 'surf0_mask_source.png')
    im = Image.open(GIF_C).convert('RGB')
    im.crop((66, 28, 136, 84)).save(REF_DIR / 'jump_ref.png')
    im.crop(REFERENCE_SPECS['JUMP_AIR']['maskCropBox']).save(REF_DIR / 'jump_mask_source.png')
    with tempfile.TemporaryDirectory(prefix='3a0-refs-') as td:
        td = Path(td)
        frames = [12490, 12493, 12504, 15600, 12393]
        paths = {}
        for n in frames:
            paths[n] = td / f'f{n}.png'
            extract_frame(MP4_USA, n, paths[n])
        fg = Image.open(paths[12490]).convert('RGB').crop((129, 107, 163, 125))
        fg.save(REF_DIR / 'uw_ref_source_R.png')
        fg.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(REF_DIR / 'uw_ref.png')
        Image.open(paths[12504]).convert('RGB').crop((129, 107, 163, 125)).save(
            REF_DIR / 'uw_bg_f12504.png')
        Image.open(paths[12493]).convert('RGB').crop((136, 107, 170, 125)).save(
            REF_DIR / 'uw_ref_aux_f12493_R.png')
        Image.open(paths[15600]).convert('RGB').crop((56, 142, 99, 163)).save(
            REF_DIR / 'uw_ref_aux_f15600_R.png')
        Image.open(paths[12393]).convert('RGB').crop((56, 70, 96, 98)).save(
            REF_DIR / 'surf0_real_f12393.png')
    sha_mp4 = sha256_file(MP4_USA)
    lines = [
        '# 阶段3A-0 参考裁剪来源清单',
        '',
        '由 `build_sprites_3a0.py --extract-refs` 一次性生成(构建期操作)。',
        '来源原件均被 .gitignore 排除, 不入库; 本目录裁剪图供审核表对照栏只读使用。',
        '',
        '| 文件 | 来源 | 帧 | 裁剪框(x0,y0,x1,y1) | 版本 | 证据限制 |',
        '| --- | --- | --- | --- | --- | --- |',
        f'| surf0_ref.png | 过程文件/原版参考/官方截图/jp-action-e.gif (SHA-256 {sha256_file(GIF_E)[:16]}…) | 整图(静态gif) | (96,86,142,114) | 日版官方宣传图 | 单帧, 只证姿态不证时序 |',
        f'| jump_ref.png | 过程文件/原版参考/官方截图/jp-action-c.gif (SHA-256 {sha256_file(GIF_C)[:16]}…) | 整图(静态gif) | (66,28,136,84) | 日版官方宣传图 | 单帧, 只证姿态不证时序 |',
        f'| uw_ref_source_R.png | 过程文件/原版参考/实机视频-USA-vjlUJSGGE3g.mp4 (SHA-256 {sha_mp4[:16]}…) | 0基 n=12490 (06:56.333) | (129,107,163,125) 34x18 | 美版TAS实机录制 | 单人、无遮挡；源朝右 |',
        f'| uw_ref.png | 同上 f12490 | 0基 n=12490 | 对 uw_ref_source_R.png 严格 horizontal_flip | canonical L | 与mask/新稿同为原生34x18，未拉伸 |',
        f'| uw_bg_f12504.png | 同上 | 0基 n=12504 (06:56.800) | (129,107,163,125) 34x18 | 同景空背景 | 供逐像素背景差分 |',
        f'| uw_ref_aux_f12493_R.png | 同上 | 0基 n=12493 (06:56.433) | (136,107,170,125) 34x18 | 同一单人横泳序列 | 辅证另一相位，不参与主mask |',
        f'| uw_ref_aux_f15600_R.png | 同上 | 0基 n=15600 (08:40.000) | (56,142,99,163) 43x21 | 另一干净单人实例 | 交叉验证，不参与主mask |',
        f'| surf0_real_f12393.png | 过程文件/原版参考/实机视频-USA-vjlUJSGGE3g.mp4 (SHA-256 {sha_mp4[:16]}…) | n=12393 (约06:53.1, 0基) | (56,70,96,98) | 美版TAS实机录制 | 水面俯泳无接触帧, 仅作比例/场景对齐辅证; 压缩源 |',
        '| mask_SURF0.png/.json | jp-action-e.gif 同上单帧裁剪(105,88,136,109) 半自动分割 | - | - | - | 见 json cleanupLog |',
        '| mask_JUMP_AIR.png/.json | jp-action-c.gif 同上单帧裁剪(73,35,128,77) 半自动分割 | - | - | - | 见 json cleanupLog |',
        '| mask_UW_NORMAL.png/.json | f12490减同景空背景f12504，阈值25，最大4连通体，再R→L镜像 | - | (129,107,163,125) | 美版 | 369px；见JSON cleanupLog/完整SHA |',
        '',
        '**作废证据：0基 f15625 的旧裁剪 (60,114,125,136) 同时包含两名接触角色，旧65x22 mask/身体不得再用于3A-1。**',
        '',
        'TBD: JUMP_AIR 美版实机伸展空中帧多轮搜寻未获(仅见 f15012-15030 收团跳水帧, 姿态不同), 现仅以日版 gif 为姿态证据。',
    ]
    (REF_DIR / '来源清单.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('[extract-refs] 审核参考/精确mask裁剪/UW背景与辅证/来源清单 已生成')

# ================= 水面遮挡 / 场景验收图 =================
SCENE_W, SCENE_H = 256, 224
FOAM_Y0, FOAM_Y1 = 72, 101
FOAM_COLORS = {(0xF3, 0xFE, 0xFC), (0xB6, 0xE7, 0xF4)}  # 泡沫白 / 浅波纹
UW_LINE_Y = 102  # y>=102 走 UW_MAP

def load_scene_bg():
    """阶段1截图 768x672 NEAREST 1/3 -> 256x224。"""
    assert sha256_file(STAGE1_SCENE) == STAGE1_SHA256, '阶段1截图 SHA-256 不符'
    im = Image.open(STAGE1_SCENE).convert('RGB')
    assert im.size == (768, 672), f'阶段1截图尺寸 {im.size} != (768,672)'
    return im.resize((SCENE_W, SCENE_H), Image.NEAREST)

def foam_pixels(bg):
    px = bg.load()
    return {(x, y) for y in range(FOAM_Y0, FOAM_Y1 + 1) for x in range(SCENE_W)
            if px[x, y][:3] in FOAM_COLORS}

def hex_rows(pts, w, h):
    """点集 -> 每行 hex 串(MSB=x0)。w 需 8 的倍数则整字节, 否则补零位。"""
    out = []
    nbytes = (w + 7) // 8
    for y in range(h):
        val = 0
        bits = []
        row = [1 if (x, y) in pts else 0 for x in range(w)]
        row += [0] * (nbytes * 8 - w)
        for i in range(0, nbytes * 8, 8):
            byte = 0
            for b in range(8):
                byte = (byte << 1) | row[i + b]
            bits.append(f'{byte:02x}')
        out.append(''.join(bits))
    return out

def decode_hex_rows(rows, w):
    pts = set()
    for y, row_hex in enumerate(rows):
        raw = bytes.fromhex(row_hex)
        for x in range(w):
            if raw[x // 8] & (1 << (7 - (x % 8))):
                pts.add((x, y))
    return pts

def draw_sprite_scene(canvas, rows, team, top_left, uw_all=False):
    """uw_all: 全部 UW_MAP; 否则世界 y>=UW_LINE_Y 的行用 UW_MAP。"""
    px = canvas.load()
    ox, oy = top_left
    for y, r in enumerate(rows):
        wy = oy + y
        for x, c in enumerate(r):
            if c == '.':
                continue
            if uw_all or wy >= UW_LINE_Y:
                col = UW_MAP[c]
            elif c == 'T':
                col = TEAM[team]
            else:
                col = PAL[c]
            rgb = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))
            px[ox + x, wy] = rgb

def scene_mode(faces, sprites, out_png, out_8x):
    bg = load_scene_bg()
    canvas = bg.copy()
    # 水下: 爸爸L root(70,130) / 阳阳R root(185,145)
    for who, d, root_w in [('dd', 'L', (70, 130)), ('yy', 'R', (185, 145))]:
        rows, _ = sprites[('UW_NORMAL', who, d)]
        ax, ay = anchor('UW_NORMAL', MANIFEST['UW_NORMAL']['w'], d)
        draw_sprite_scene(canvas, rows, who, (root_w[0] - ax, root_w[1] - ay), uw_all=True)
    # 水面: 阳阳L 横跨x44-74 / 爸爸R 横跨x174-204, root 世界 y=92
    for who, d, x0 in [('yy', 'L', 44), ('dd', 'R', 174)]:
        rows, _ = sprites[('SURF0', who, d)]
        _, ay = anchor('SURF0', 31, d)
        draw_sprite_scene(canvas, rows, who, (x0, 92 - ay), uw_all=False)
    # 泡沫前景覆盖(y72..101)
    px = canvas.load()
    bpx = bg.load()
    for x, y in foam_pixels(bg):
        px[x, y] = bpx[x, y]
    canvas.save(out_png)
    # 8x 局部: 水面块(阳阳) + 水下块(爸爸)
    surf_crop = canvas.crop((36, 64, 90, 112)).resize((54 * 8, 48 * 8), Image.NEAREST)
    uw_crop = canvas.crop((32, 110, 108, 144)).resize((76 * 8, 34 * 8), Image.NEAREST)
    W = max(surf_crop.width, uw_crop.width)
    sheet = Image.new('RGB', (W, surf_crop.height + uw_crop.height + 8), (24, 24, 32))
    sheet.paste(surf_crop, (0, 0))
    sheet.paste(uw_crop, (0, surf_crop.height + 8))
    sheet.save(out_8x)
    print(f'[scene] {Path(out_png).name} + {Path(out_8x).name}')

# ================= 烘焙 JS =================
def bake_js(faces, sprites, masks_stats, bg, out_path=OUT_JS):
    foam = foam_pixels(bg)
    foam_local = {(x, y - FOAM_Y0) for x, y in foam}
    foam_rows = hex_rows(foam_local, SCENE_W, FOAM_Y1 - FOAM_Y0 + 1)
    decoded = decode_hex_rows(foam_rows, SCENE_W)
    assert decoded == foam_local, 'waterOcclusion hex roundtrip 不一致'
    assert len(foam_rows) == 30 and sum(bool(int(r, 16)) for r in foam_rows) == 29
    assert len(decoded) == len(foam) == 3942, f'waterOcclusion 像素数 {len(decoded)} != 3942'
    data = {
        'meta': {
            'stage': '3A-0-R2',
            'generatedBy': 'build_sprites_3a0.py',
            'avatarPaintSha256': AVATAR_SHA256,
            'stage1SceneSha256': STAGE1_SHA256,
            'poses': POSES,
            'directions': ['L', 'R'],
            'persons': {'yy': TEAM_CN['yy'], 'dd': TEAM_CN['dd']},
        },
        'pal': {k: v for k, v in PAL.items() if v},
        'team': TEAM,
        'uwMap': UW_MAP,
        'poses': {},
        'waterOcclusion': {
            'y0': FOAM_Y0, 'y1': FOAM_Y1, 'uwLineY': UW_LINE_Y,
            'width': SCENE_W, 'bitOrder': 'MSB=x0', 'rows': foam_rows,
            'pixelCount': len(decoded), 'nonZeroRows': sum(bool(int(r, 16)) for r in foam_rows),
            'note': '阶段1截图 NEAREST 1/3 后 y72..101 泡沫色(#F3FEFC/#B6E7F4)前景像素; '
                    'SURF0 绘制时该层覆盖人物, 世界y>=102 的行改用 uwMap',
        },
    }
    for pose in POSES:
        w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
        entry = {
            'w': w, 'h': h, 'cn': MANIFEST[pose]['cn'],
            'sourceReference': MANIFEST[pose]['sourceReference'],
            'mirrorNote': MANIFEST[pose]['mirrorNote'],
            'maskSha256': sha256_file(mask_path(pose)),
            'maskJson': MANIFEST[pose]['mask_json'],
            'maskJsonSha256': sha256_file(mask_meta_path(pose)),
            'stats': masks_stats[pose],
            'rootByDir': {d: list(anchor(pose, w, d)) for d in ('L', 'R')},
            'visibleBBoxByDir': {}, 'rows': {'yy': {}, 'dd': {}},
            'identityMask': {'yy': {}, 'dd': {}},
        }
        for who in ('yy', 'dd'):
            for d in ('L', 'R'):
                rows, idm = sprites[(pose, who, d)]
                entry['rows'][who][d] = rows
                entry['identityMask'][who][d] = hex_rows(idm, w, h)
                if who == 'yy':
                    bb = visible_bbox(sprite_pts(rows))
                    entry['visibleBBoxByDir'][d] = list(bb)
        data['poses'][pose] = entry
    js = '// 阶段3A-0 R2 人物精灵(自动生成, 请勿手改; 重新生成: python3 build_sprites_3a0.py)\n'
    js += 'const SPRITES_3A0 = ' + json.dumps(data, ensure_ascii=False, indent=1) + ';\n'
    js += "if (typeof module !== 'undefined') module.exports = SPRITES_3A0;\n"
    out_path = Path(out_path)
    out_path.write_text(js, encoding='utf-8')
    print(f'[bake] {out_path.name} {len(js.encode("utf-8"))}B')

# ================= 自检 =================
CHARSET = set(PAL) | {'.'}

def selfcheck(faces, sprites):
    fails = []
    report = []

    def log(line):
        report.append(line)
        print(line)

    log('== 自检: 12张精灵 尺寸/字符集/连通性/锚点 ==')
    mask_stats = {}
    for pose in POSES:
        w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
        mpts = load_mask(pose)
        bbox_ref = visible_bbox(mpts)
        for who in ('yy', 'dd'):
            for d in ('L', 'R'):
                rows, idm = sprites[(pose, who, d)]
                key = f'{pose}/{who}/{d}'
                if len(rows) != h or any(len(r) != w for r in rows):
                    fails.append(f'{key} 尺寸错误')
                bad = {c for r in rows for c in r} - CHARSET
                if bad:
                    fails.append(f'{key} 非法字符 {bad}')
                pts = sprite_pts(rows)
                ncomp = components4(pts)
                log(f'{key}: 尺寸{w}x{h} 像素{len(pts)} 4连通域={ncomp}'
                    + ('' if ncomp == 1 else '  <-- FAIL'))
                if ncomp != 1:
                    fails.append(f'{key} 4连通域={ncomp}')
                # alpha 检查(渲染后 alpha 只能 0/255)
                im = render(rows, who)
                alphas = {a for *_, a in im.getdata()}
                if alphas - {0, 255}:
                    fails.append(f'{key} alpha 含非0/255: {sorted(alphas)[:5]}')
        # 几何: L稿(去身份) vs 真实mask(同样排除身份区); R稿镜像后 vs mask
        for d in ('L', 'R'):
            rows, idm = sprites[(pose, 'yy', d)]
            idm_c = {(w - 1 - x, y) for x, y in idm} if d == 'R' else idm
            pts = sprite_pts(rows)
            if d == 'R':
                pts = {(w - 1 - x, y) for x, y in pts}
            pts -= idm_c
            mpts_eff = mpts - idm_c
            xor, union, pct = xor_stats(pts, mpts_eff)
            dev = max_boundary_dev(pts, mpts_eff)
            tol_pct, tol_px = GEOM_TOL[pose]
            ok = pct <= tol_pct and dev <= tol_px
            log(f'{pose}/{d}(去身份, mask侧同排) vs mask: XOR={xor}/{union}={pct:.1f}% '
                f'最大边界偏差={dev:.2f}px 容差({tol_pct}%,{tol_px}px) '
                + ('PASS' if ok else 'EXCEED <-- FAIL'))
            if not ok:
                fails.append(f'{pose}/{d} 几何超容差: XOR {pct:.1f}% / 偏差 {dev:.2f}px')
            if d == 'L':
                mask_stats[pose] = dict(maskPixels=len(mpts), maskBBox=list(bbox_ref),
                                        xorL=xor, unionL=union, xorPctL=round(pct, 2),
                                        maxDevL=round(dev, 2))
        # identityMask 比例 + 左右稿差异统计
        for who in ('yy', 'dd'):
            rl, idl = sprites[(pose, who, 'L')]
            rr, idr = sprites[(pose, who, 'R')]
            nl, nr = len(sprite_pts(rl)), len(sprite_pts(rr))
            log(f'{pose}/{who}: identityMask L={len(idl)}/{nl}={100*len(idl)/nl:.1f}% '
                f'R={len(idr)}/{nr}={100*len(idr)/nr:.1f}%')
        # 左右稿身份内外差异(同向 yy vs dd)
        for d in ('L', 'R'):
            ry, idy = sprites[(pose, 'yy', d)]
            rd, idd = sprites[(pose, 'dd', d)]
            idu = {(x, y) for y in range(h) for x in range(w)
                   if (x, y) in idy or (x, y) in idd}
            din = dout = 0
            for y in range(h):
                for x in range(w):
                    if ry[y][x] != rd[y][x]:
                        if (x, y) in idu:
                            din += 1
                        else:
                            dout += 1
            log(f'{pose}/{d}: yy vs dd 差异 身份区内={din} 身份区外={dout}'
                + ('' if dout == 0 else '  <-- FAIL(区外应一致)'))
            if dout != 0:
                fails.append(f'{pose}/{d} 身份区外存在双人差异 {dout}px')
        # 锚点: root 像素或其8邻域有效 + 左右世界连续性
        for d in ('L', 'R'):
            rows, _ = sprites[(pose, 'yy', d)]
            pts = sprite_pts(rows)
            ax, ay = anchor(pose, w, d)
            ok_root = (ax, ay) in pts or any(
                (ax + dx, ay + dy) in pts
                for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            log(f'{pose}/{d}: root=({ax},{ay}) root或其8邻域有效={ok_root}'
                + ('' if ok_root else '  <-- FAIL'))
            if not ok_root:
                fails.append(f'{pose}/{d} root 落空')
        # 世界一致性: 同一世界 root 坐标下 L/R 的 root 落点一致(不横跳) + 定义镜像一致
        rl, _ = sprites[(pose, 'yy', 'L')]
        rr, _ = sprites[(pose, 'yy', 'R')]
        axl, ayl = anchor(pose, w, 'L')
        axr, ayr = anchor(pose, w, 'R')
        world = (128, 100)  # 任意世界锚点
        wl = (world[0] - axl + axl, world[1] - ayl + ayl)  # 按 root 摆放后 root 的世界坐标
        wr = (world[0] - axr + axr, world[1] - ayr + ayr)
        ok_same = wl == wr == world
        ok_mirror = (axr == w - 1 - axl and ayr == ayl)
        log(f'{pose}: 同世界root下 L/R root落点=({wl[0]},{wl[1]})/({wr[0]},{wr[1]}) 一致={ok_same} '
            f'镜像定义一致={ok_mirror}'
            + ('' if ok_same and ok_mirror else '  <-- FAIL'))
        if not (ok_same and ok_mirror):
            fails.append(f'{pose} root 世界落点/镜像定义不一致')
        # 信息指标: bbox 中心横移(不设 FAIL)
        bl, br = visible_bbox(sprite_pts(rl)), visible_bbox(sprite_pts(rr))
        cl = (bl[0] + bl[2]) / 2 - axl
        cr = (br[0] + br[2]) / 2 - axr
        shift = abs(cl - cr)
        note = ''
        if shift > 2:
            note = (' (信息指标: 姿态本身左右不对称 + root 为语义锚点而非 bbox 中心, '
                    '切换方向时 bbox 围绕语义锚点翻转所致, 不改稿)')
        log(f'{pose}: [信息] 同世界root下 bbox中心横移={shift:.2f}px{note}')
    if fails:
        log('== 自检失败 ==')
        for f in fails:
            log('FAIL: ' + f)
    else:
        log('== 自检全部通过 ==')
    return fails, mask_stats

# ================= 审核表 =================
FONT_CANDIDATES = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
]

def get_font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def xor_image(pose, sprites):
    """绿=一致 红=精灵多 蓝=mask多 黄=身份区。"""
    w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
    rows, idm = sprites[(pose, 'yy', 'L')]
    pts = sprite_pts(rows)
    mpts = load_mask(pose)
    im = Image.new('RGB', (w, h), (250, 250, 250))
    px = im.load()
    for x, y in pts & mpts:
        px[x, y] = (120, 200, 120)
    for x, y in pts - mpts:
        px[x, y] = (230, 60, 60)
    for x, y in mpts - pts:
        px[x, y] = (60, 100, 230)
    for x, y in idm:
        px[x, y] = (250, 200, 40)
    return im

def anchor_image(rows, team, pose, direction, mapping=None):
    w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
    im = render(rows, team, mapping=mapping).convert('RGB')
    dr = ImageDraw.Draw(im)
    ax, ay = anchor(pose, w, direction)
    bb = visible_bbox(sprite_pts(rows))
    dr.rectangle([bb[0], bb[1], bb[2], bb[3]], outline=(255, 255, 255))
    dr.line([(ax - 2, ay), (ax + 2, ay)], fill=(255, 0, 0))
    dr.line([(ax, ay - 2), (ax, ay + 2)], fill=(255, 0, 0))
    return im

def _flatten_for_audit(im):
    if im.mode != 'RGBA':
        return im.convert('RGB')
    bg = Image.new('RGB', im.size, (48, 48, 56))
    px = bg.load()
    for y in range(im.height):
        for x in range(im.width):
            if (x + y) % 2:
                px[x, y] = (62, 62, 72)
    bg.paste(im, (0, 0), im)
    return bg

def paste_exact_panel(canvas, dr, im, box, title, font):
    """只允许原生1× + 单次NEAREST 8×；绝不fit、插值或二次缩放。"""
    x0, y0, x1, y1 = box
    dr.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(190, 190, 198), fill=(236, 236, 240))
    dr.text((x0 + 6, y0 + 5), title, font=font, fill=(24, 24, 28))
    native = _flatten_for_audit(im)
    big = native.resize((native.width * 8, native.height * 8), Image.Resampling.NEAREST)
    assert big.size == (native.width * 8, native.height * 8)
    assert big.width <= x1 - x0 - 12 and big.height <= y1 - y0 - 42, (
        f'{title} 8x超出审核格 {big.size} / {(x1-x0, y1-y0)}')
    canvas.paste(native, (x0 + 6, y0 + 24))  # 严格1×
    bx = x0 + (x1 - x0 - big.width) // 2
    by = y1 - big.height - 6
    canvas.paste(big, (bx, by))              # 严格8×

def make_sheet(out_png, poses, sprites, faces, stats_lines):
    font = get_font(15)
    font_s = get_font(12)
    cellw, cellh, labelw, pad = 470, 430, 150, 8
    cols = ['REF exact', 'MASK', 'BODY neutral', 'YY-L', 'YY-R',
            'DAD-L', 'DAD-R', 'XOR/IDENTITY', 'ANCHOR-L', 'ANCHOR-R']
    W = labelw + cellw * len(cols) + pad
    rowh = cellh + 30
    stat_h = 30 * len(stats_lines) + 16
    H = 54 + rowh * len(poses) + stat_h + pad
    canvas = Image.new('RGB', (W, H), (245, 245, 248))
    dr = ImageDraw.Draw(canvas)
    dr.text((pad, 8), f'阶段3A-0 R2 精灵审核表 — {" / ".join(MANIFEST[p]["cn"] for p in poses)}',
            font=font, fill=(0, 0, 0))
    dr.text((pad, 28), '每格左上=严格原生1x；主体=仅一次NEAREST 8x。禁止fit/拉伸/二次缩放。',
            font=font_s, fill=(50, 50, 55))
    for ci, cname in enumerate(cols):
        dr.text((labelw + ci * cellw + 6, 46), cname, font=font_s, fill=(40, 40, 40))
    for ri, pose in enumerate(poses):
        y0 = 66 + ri * rowh
        dr.text((6, y0 + cellh // 2), f'{pose}\n{MANIFEST[pose]["cn"]}\n'
                f'{MANIFEST[pose]["w"]}×{MANIFEST[pose]["h"]}', font=font_s, fill=(0, 0, 0))
        w, h = MANIFEST[pose]['w'], MANIFEST[pose]['h']
        ref = Image.open(REF_DIR / REFERENCE_SPECS[pose]['referenceCropFile']).convert('RGB')
        assert ref.size == (w, h), f'{pose} 原生参考尺寸 {ref.size} != {(w,h)}'
        mim = Image.new('RGB', (w, h), (250, 250, 250))
        mpx = mim.load()
        for x, y in load_mask(pose):
            mpx[x, y] = (30, 30, 30)
        mapping = UW_MAP if pose == 'UW_NORMAL' else None
        base = render(build_base(pose), 'yy', mapping=mapping)
        yyL, _ = sprites[(pose, 'yy', 'L')]
        yyR, _ = sprites[(pose, 'yy', 'R')]
        ddL, _ = sprites[(pose, 'dd', 'L')]
        ddR, _ = sprites[(pose, 'dd', 'R')]
        panels = [
            ref, mim, base,
            render(yyL, 'yy', mapping=mapping), render(yyR, 'yy', mapping=mapping),
            render(ddL, 'dd', mapping=mapping), render(ddR, 'dd', mapping=mapping),
            xor_image(pose, sprites),
            anchor_image(yyL, 'yy', pose, 'L', mapping),
            anchor_image(yyR, 'yy', pose, 'R', mapping),
        ]
        titles = ['原版原生裁剪', '独立1-bit轮廓', '去身份一体身体', '阳阳 L', '阳阳 R',
                  '爸爸 L', '爸爸 R', '绿同/红多/蓝少/黄身份', 'L root+bbox', 'R root+bbox']
        for ci, (im, title) in enumerate(zip(panels, titles)):
            x0 = labelw + ci * cellw
            paste_exact_panel(canvas, dr, im, (x0 + 2, y0 + 2, x0 + cellw - 6, y0 + cellh - 6),
                              title, font_s)
    sy = 66 + rowh * len(poses) + 6
    for line in stats_lines:
        dr.text((pad, sy), line, font=font_s, fill=(0, 0, 0))
        sy += 30
    canvas.save(out_png)
    print(f'[sheet] {Path(out_png).name} {W}x{H}')

# ================= 主流程 =================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--make-mask', action='store_true')
    ap.add_argument('--extract-refs', action='store_true')
    args = ap.parse_args()
    if args.make_mask:
        make_mask_mode()
        return
    if args.extract_refs:
        extract_refs_mode()
        return
    faces = load_faces()
    sprites = {}
    for pose in POSES:
        for who in ('yy', 'dd'):
            for d in ('L', 'R'):
                sprites[(pose, who, d)] = build_sprite(pose, who, d, faces)
    fails, mask_stats = selfcheck(faces, sprites)
    if fails:
        print('[abort] 自检失败；未覆盖任何正式 JS/PNG 产物')
        sys.exit(1)
    bg = load_scene_bg()
    def stat_line(pose):
        s = mask_stats[pose]
        return (f'{pose}: mask={s["maskPixels"]}px bbox={s["maskBBox"]} '
                f'XOR(L,去身份)={s["xorL"]}/{s["unionL"]}={s["xorPctL"]}% '
                f'最大边界偏差={s["maxDevL"]}px')

    node_bin = shutil.which('node')
    if not node_bin:
        sys.exit('错误: 找不到 node，无法执行生成 JS 的语法门')
    outputs = [OUT_JS, OUT_SCENE, OUT_SCENE_8X, OUT_SHEET1, OUT_SHEET2]
    with tempfile.TemporaryDirectory(prefix='3a0-build-', dir=BASE) as td:
        td = Path(td)
        tmp = {p: td / p.name for p in outputs}
        bake_js(faces, sprites, mask_stats, bg, tmp[OUT_JS])
        node = subprocess.run([node_bin, '--check', str(tmp[OUT_JS])], capture_output=True)
        print('[node --check]', 'OK' if node.returncode == 0 else node.stderr.decode()[:300])
        if node.returncode != 0:
            sys.exit('错误: node --check 失败；未覆盖正式产物')
        scene_mode(faces, sprites, str(tmp[OUT_SCENE]), str(tmp[OUT_SCENE_8X]))
        make_sheet(str(tmp[OUT_SHEET1]), ['SURF0', 'UW_NORMAL'], sprites, faces,
                   [stat_line(p) for p in ('SURF0', 'UW_NORMAL')])
        make_sheet(str(tmp[OUT_SHEET2]), ['JUMP_AIR'], sprites, faces, [stat_line('JUMP_AIR')])
        for final in outputs:
            os.replace(tmp[final], final)
    print('[done] 全部产物已生成')

if __name__ == '__main__':
    main()
