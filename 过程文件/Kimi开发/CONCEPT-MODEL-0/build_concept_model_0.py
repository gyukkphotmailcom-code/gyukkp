#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONCEPT-MODEL-0：概念角色标准模型锁定门（确定性构建器）

- 人物形象唯一来源：用户确认的两张本地概念参考图（仅人工观察，本脚本不读取）。
- 本阶段只制作人物标准稿：头部四向、正/侧面全身、标尺、调色板、结构拆解、
  身高对照、盲审表。不制作任何游戏动作，不接入游戏。
- CONCEPT-1A 旧稿为失败对照，本脚本不复用其任何人物画法，全新绘制。
- 只使用 Pillow 作为构建期工具；不联网；无随机数；整数坐标；alpha 仅 0/255。
- 输出仅写入本脚本所在目录（过程文件/Kimi开发/CONCEPT-MODEL-0/）。
"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SPRITES = HERE / "sprites"

# ---------------------------------------------------------------- 固定调色板
# 光源固定：左上方。暖色皮肤两人共用（与概念图一致）。
OUT      = (40, 28, 20, 255)    # 硬描边：暖深棕黑
SKIN     = (246, 178, 108, 255) # 肤色主色
SKIN_L   = (254, 206, 150, 255) # 肤色高光
SKIN_SH  = (218, 140, 80, 255)  # 肤影
SKIN_D   = (192, 114, 62, 255)  # 深肤影（下颌/右侧）
CAP      = (40, 100, 196, 255)  # 泳帽主蓝
CAP_L    = (98, 160, 232, 255)  # 泳帽浅蓝分区
CAP_LL   = (158, 204, 248, 255) # 泳帽顶高光带
CAP_D    = (20, 56, 128, 255)   # 泳帽深蓝边缘
GOG_F    = (238, 244, 250, 255) # 泳镜框（白）
GOG_FSH  = (172, 190, 210, 255) # 泳镜框阴影
GOG_L    = (14, 34, 80, 255)    # 泳镜镜片（深藏青）
SUIT     = (36, 96, 186, 255)   # 阳阳蓝色泳装
SUIT_D   = (20, 58, 126, 255)   # 泳装阴影
SUIT_L   = (80, 140, 220, 255)  # 泳装高光
HAIR     = (22, 20, 24, 255)    # 爸爸黑发
HAIR_L   = (58, 54, 60, 255)    # 黑发高光/质感
HAIR_SH  = (10, 9, 12, 255)     # 黑发深影
GLS      = (16, 14, 18, 255)    # 黑框眼镜
GLS_L    = (216, 232, 244, 255) # 镜片
SUITD    = (30, 32, 44, 255)    # 爸爸深色泳装
SUITD_L  = (58, 62, 80, 255)    # 爸爸泳装高光
WHT      = (255, 255, 255, 255)
INK      = (26, 20, 16, 255)    # 瞳孔（近黑暖棕）
BROW     = (58, 40, 30, 255)    # 眉毛
MOUTH    = (150, 52, 44, 255)   # 口腔
MOUTH_D  = (98, 30, 28, 255)    # 口腔深处/嘴角
TEETH    = WHT                  # 牙齿

PALETTE = {
    "OUT": OUT, "SKIN": SKIN, "SKIN_L": SKIN_L, "SKIN_SH": SKIN_SH, "SKIN_D": SKIN_D,
    "CAP": CAP, "CAP_L": CAP_L, "CAP_LL": CAP_LL, "CAP_D": CAP_D,
    "GOG_F": GOG_F, "GOG_FSH": GOG_FSH, "GOG_L": GOG_L,
    "SUIT": SUIT, "SUIT_D": SUIT_D, "SUIT_L": SUIT_L,
    "HAIR": HAIR, "HAIR_L": HAIR_L, "HAIR_SH": HAIR_SH,
    "GLS": GLS, "GLS_L": GLS_L, "SUITD": SUITD, "SUITD_L": SUITD_L,
    "WHT": WHT, "INK": INK, "BROW": BROW, "MOUTH": MOUTH, "MOUTH_D": MOUTH_D,
    "TEETH": TEETH,
}

# ---------------------------------------------------------------- 基础助手
def canvas(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))

def D(img):
    return ImageDraw.Draw(img)

def rect(img, x0, y0, x1, y1, c):
    D(img).rectangle([x0, y0, x1, y1], fill=c)

def ell(img, x0, y0, x1, y1, c):
    D(img).ellipse([x0, y0, x1, y1], fill=c)

def line(img, pts, c, w=1):
    D(img).line(pts, fill=c, width=w, joint="curve")

def pxs(img, coords, c):
    d = D(img)
    for x, y in coords:
        d.point((x, y), fill=c)

def outline(img, col=OUT):
    """不透明像素的 4 邻接外缘 1px 硬描边（仅外轮廓）。"""
    w, h = img.size
    src = img.load()
    mark = []
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if nx < 0 or ny < 0 or nx >= w or ny >= h or not src[nx, ny][3]:
                        mark.append((x, y))
                        break
    d = D(img)
    for x, y in mark:
        d.point((x, y), fill=col)

def opaque_bbox(img):
    return img.getbbox()

def mirror_fix(img, fixes):
    """整图左右镜像后，按固定左上光源修正高光。
    fixes: list of dict(cx,cy,base) —— 镜像前高光像素；镜像后擦除错位高光，
    并在结构新左上角原位重画（高光仍在左上侧）。"""
    W = img.size[0]
    out = img.transpose(Image.FLIP_LEFT_RIGHT)
    d = D(out)
    for e in fixes:
        old_x = W - 1 - e["cx"]
        d.point((old_x, e["cy"]), fill=e["base"])   # 擦除镜像到错侧的旧高光
        d.point((e["cx"], e["cy"]), fill=WHT)       # 高光回到结构左侧
    return out

# ---------------------------------------------------------------- 3×5 像素字
FONT = {
 "0":["111","101","101","101","111"],"1":["010","110","010","010","111"],
 "2":["111","001","111","100","111"],"3":["111","001","111","001","111"],
 "4":["101","101","111","001","001"],"5":["111","100","111","001","111"],
 "6":["111","100","111","101","111"],"7":["111","001","001","010","010"],
 "8":["111","101","111","101","111"],"9":["111","101","111","001","111"],
 "A":["010","101","111","101","101"],"B":["110","101","110","101","110"],
 "C":["011","100","100","100","011"],"D":["110","101","101","101","110"],
 "E":["111","100","110","100","111"],"F":["111","100","110","100","100"],
 "G":["011","100","101","101","011"],"H":["101","101","111","101","101"],
 "I":["111","010","010","010","111"],"J":["001","001","001","101","010"],
 "K":["101","101","110","101","101"],"L":["100","100","100","100","111"],
 "M":["101","111","111","101","101"],"N":["101","111","111","111","101"],
 "O":["010","101","101","101","010"],"P":["110","101","110","100","100"],
 "Q":["010","101","101","110","011"],"R":["110","101","110","101","101"],
 "S":["011","100","010","001","110"],"T":["111","010","010","010","010"],
 "U":["101","101","101","101","111"],"V":["101","101","101","101","010"],
 "W":["101","101","111","111","101"],"X":["101","101","010","101","101"],
 "Y":["101","101","010","010","010"],"Z":["111","001","010","100","111"],
 ":":["000","010","000","010","000"],"/":["001","001","010","100","100"],
 "-":["000","000","111","000","000"]," ":["000","000","000","000","000"],
 ".":["000","000","000","000","010"],"!":["010","010","010","000","010"],
 "#":["101","111","101","111","101"],"X2":["101","010","101","000","000"],
}

def text(img, x, y, s, c, scale=1):
    d = D(img)
    cx = x
    for ch in s:
        g = FONT.get(ch.upper(), FONT[" "])
        for gy, row in enumerate(g):
            for gx, v in enumerate(row):
                if v == "1":
                    if scale == 1:
                        d.point((cx + gx, y + gy), fill=c)
                    else:
                        d.rectangle([cx + gx * scale, y + gy * scale,
                                     cx + (gx + 1) * scale - 1, y + (gy + 1) * scale - 1], fill=c)
        cx += 4 * scale

def text_w(s, scale=1):
    return len(s) * 4 * scale - scale

def zoom(img, k):
    return img.resize((img.size[0] * k, img.size[1] * k), Image.NEAREST)

# ================================================================ 阳阳头部
# 概念特征：圆短儿童脸；大眼黑瞳+左上高光；小鼻小嘴；可见双耳；
# 蓝泳帽深浅蓝分区+顶部高光带；白色镜带横过帽前；双镜片泳镜（白框藏青镜片）。

def head_yy_front():
    img = canvas(28, 28)
    # 双耳
    rect(img, 0, 15, 2, 18, SKIN); pxs(img, [(1, 16)], SKIN_SH)
    rect(img, 25, 15, 27, 18, SKIN); pxs(img, [(26, 16)], SKIN_SH)
    # 脸（圆短）
    ell(img, 2, 9, 25, 26, SKIN)
    rect(img, 2, 12, 25, 21, SKIN)
    # 右下侧肤影（左上光源）
    pxs(img, [(24, 13), (24, 15), (24, 17), (24, 19), (23, 21), (22, 23),
              (18, 25), (20, 25), (22, 24)], SKIN_SH)
    pxs(img, [(24, 21), (23, 23)], SKIN_D)
    # 泳帽：主体 + 深浅蓝分区
    ell(img, 3, 0, 24, 12, CAP)
    rect(img, 3, 5, 24, 11, CAP)
    rect(img, 11, 0, 16, 4, CAP_L)              # 顶部浅蓝分区
    rect(img, 12, 0, 15, 1, CAP_LL)             # 顶部高光带
    line(img, [(5, 2), (5, 8)], CAP_D, 1)       # 左分区线
    line(img, [(22, 2), (22, 8)], CAP_D, 1)     # 右分区线
    line(img, [(4, 10), (23, 10)], CAP_D, 1)    # 帽檐深色边
    # 泳镜（帽上）：白色镜带横贯 + 双镜片白框藏青面
    rect(img, 3, 7, 24, 8, GOG_F)               # 镜带
    pxs(img, [(23, 8), (24, 8)], GOG_FSH)
    rect(img, 5, 2, 11, 8, GOG_F)               # 左镜框
    rect(img, 6, 3, 10, 7, GOG_L)               # 左镜片
    rect(img, 16, 2, 22, 8, GOG_F)              # 右镜框
    rect(img, 17, 3, 21, 7, GOG_L)              # 右镜片
    rect(img, 11, 4, 16, 5, GOG_F)              # 镜桥
    pxs(img, [(6, 3), (7, 3), (6, 4)], WHT)     # 左镜片高光（左上）
    pxs(img, [(17, 3), (18, 3), (17, 4)], WHT)  # 右镜片高光（左上）
    # 眉
    line(img, [(5, 12), (8, 12)], BROW, 1)
    line(img, [(19, 12), (22, 12)], BROW, 1)
    # 大眼：白睛 + 黑瞳 + 左上高光
    rect(img, 5, 14, 9, 18, WHT)
    rect(img, 6, 15, 8, 18, INK); pxs(img, [(6, 15)], WHT)
    rect(img, 18, 14, 22, 18, WHT)
    rect(img, 19, 15, 21, 18, INK); pxs(img, [(19, 15)], WHT)
    # 小鼻
    pxs(img, [(13, 20), (14, 20)], SKIN_SH)
    # 小嘴微笑（上排牙 + 口腔）
    rect(img, 10, 22, 17, 24, MOUTH)
    rect(img, 10, 22, 17, 22, TEETH)
    pxs(img, [(9, 21), (18, 21)], MOUTH_D)      # 嘴角上扬
    outline(img)
    return img

def head_yy_side():
    """阳阳左侧脸（朝左）。"""
    img = canvas(28, 28)
    # 耳（靠后侧）
    rect(img, 20, 15, 22, 18, SKIN); pxs(img, [(21, 16)], SKIN_SH)
    # 脸（侧视轮廓：额-鼻-唇-下巴）
    ell(img, 3, 9, 24, 26, SKIN)
    rect(img, 5, 12, 24, 21, SKIN)
    pxs(img, [(23, 13), (23, 15), (23, 17), (23, 19), (22, 21), (21, 23),
              (17, 25), (19, 25)], SKIN_SH)
    pxs(img, [(23, 21), (22, 23)], SKIN_D)
    # 泳帽包颅
    ell(img, 2, 0, 26, 13, CAP)
    rect(img, 3, 5, 26, 11, CAP)
    rect(img, 11, 0, 17, 4, CAP_L)
    rect(img, 12, 0, 16, 1, CAP_LL)
    line(img, [(5, 2), (5, 8)], CAP_D, 1)
    line(img, [(24, 3), (24, 10)], CAP_D, 1)
    line(img, [(4, 10), (24, 10)], CAP_D, 1)
    rect(img, 22, 10, 26, 14, CAP)              # 帽后沿包覆
    line(img, [(22, 13), (25, 13)], CAP_D, 1)
    # 泳镜（侧视：帽前单镜片 + 绕头镜带）
    rect(img, 3, 7, 25, 8, GOG_F)               # 镜带绕头
    rect(img, 2, 2, 9, 8, GOG_F)                # 侧视镜框
    rect(img, 3, 3, 8, 7, GOG_L)
    pxs(img, [(3, 3), (4, 3), (3, 4)], WHT)
    # 眉
    line(img, [(4, 12), (8, 12)], BROW, 1)
    # 大眼（侧视仍偏大）
    rect(img, 4, 14, 9, 18, WHT)
    rect(img, 5, 15, 8, 18, INK); pxs(img, [(5, 15)], WHT)
    # 小鼻（凸点）
    pxs(img, [(2, 19), (3, 19), (3, 20)], SKIN)
    pxs(img, [(2, 20)], SKIN_SH)
    # 小嘴
    rect(img, 5, 22, 10, 24, MOUTH)
    rect(img, 5, 22, 10, 22, TEETH)
    pxs(img, [(10, 21)], MOUTH_D)
    outline(img)
    fixes = [dict(cx=5, cy=15, base=INK), dict(cx=3, cy=3, base=GOG_L),
             dict(cx=4, cy=3, base=GOG_L), dict(cx=3, cy=4, base=GOG_L)]
    return img, fixes

def head_yy_34():
    """阳阳斜侧脸（3/4，朝左）。"""
    img = canvas(28, 28)
    rect(img, 0, 15, 2, 18, SKIN); pxs(img, [(1, 16)], SKIN_SH)   # 近侧耳
    rect(img, 23, 14, 25, 17, SKIN); pxs(img, [(24, 15)], SKIN_SH) # 远侧耳（略小前移）
    ell(img, 2, 9, 25, 26, SKIN)
    rect(img, 2, 12, 25, 21, SKIN)
    pxs(img, [(24, 13), (24, 15), (24, 17), (23, 19), (22, 21), (21, 23),
              (17, 25), (19, 25)], SKIN_SH)
    pxs(img, [(24, 19), (23, 21)], SKIN_D)
    ell(img, 3, 0, 24, 12, CAP)
    rect(img, 3, 5, 24, 11, CAP)
    rect(img, 10, 0, 15, 4, CAP_L)
    rect(img, 11, 0, 14, 1, CAP_LL)
    line(img, [(5, 2), (5, 8)], CAP_D, 1)
    line(img, [(22, 2), (22, 8)], CAP_D, 1)
    line(img, [(4, 10), (23, 10)], CAP_D, 1)
    rect(img, 3, 7, 24, 8, GOG_F)
    rect(img, 4, 2, 11, 8, GOG_F)               # 近侧镜片（完整）
    rect(img, 5, 3, 10, 7, GOG_L)
    rect(img, 16, 2, 21, 8, GOG_F)              # 远侧镜片（压缩）
    rect(img, 17, 3, 20, 7, GOG_L)
    rect(img, 11, 4, 16, 5, GOG_F)
    pxs(img, [(5, 3), (6, 3), (5, 4)], WHT)
    pxs(img, [(17, 3)], WHT)
    line(img, [(5, 12), (8, 12)], BROW, 1)
    line(img, [(18, 12), (21, 12)], BROW, 1)
    rect(img, 5, 14, 9, 18, WHT)                # 近侧眼（完整）
    rect(img, 6, 15, 8, 18, INK); pxs(img, [(6, 15)], WHT)
    rect(img, 17, 14, 20, 18, WHT)              # 远侧眼（压缩）
    rect(img, 18, 15, 20, 18, INK); pxs(img, [(18, 15)], WHT)
    # 鼻（微侧：带一点鼻梁影）
    pxs(img, [(13, 20), (14, 20)], SKIN_SH)
    pxs(img, [(14, 19)], SKIN_L)
    # 嘴（微侧：右角略收）
    rect(img, 10, 22, 16, 24, MOUTH)
    rect(img, 10, 22, 16, 22, TEETH)
    pxs(img, [(9, 21), (17, 21)], MOUTH_D)
    outline(img)
    return img

# ================================================================ 阳阳全身
def body_yy_front():
    """阳阳正面站姿全身：68px 高（头约27 + 身41），头身比约 1:2.5。"""
    img = canvas(48, 68)
    head = head_yy_front()
    img.alpha_composite(head, (10, 0))
    # 颈
    rect(img, 21, 26, 26, 31, SKIN)
    line(img, [(21, 29), (26, 29)], SKIN_SH, 1)
    # 肩
    ell(img, 10, 30, 37, 39, SKIN)
    # 蓝色泳装（圆角躯干，右侧阴影）
    rect(img, 15, 33, 32, 48, SUIT)
    ell(img, 15, 32, 32, 40, SUIT)
    rect(img, 15, 44, 32, 50, SUIT)
    line(img, [(31, 34), (31, 49)], SUIT_D, 1)
    line(img, [(29, 49), (31, 49)], SUIT_D, 1)
    pxs(img, [(16, 34), (17, 34)], SUIT_L)
    # 手臂（圆润柱状 + 圆手）
    line(img, [(13, 35), (11, 47)], SKIN, 5)
    ell(img, 8, 47, 14, 53, SKIN)
    line(img, [(34, 35), (36, 47)], SKIN, 5)
    ell(img, 33, 47, 39, 53, SKIN)
    pxs(img, [(37, 48), (38, 49)], SKIN_SH)
    # 腿（裸露、短、圆润）
    rect(img, 17, 50, 22, 60, SKIN)
    rect(img, 25, 50, 30, 60, SKIN)
    line(img, [(22, 51), (22, 59)], SKIN_SH, 1)
    line(img, [(30, 51), (30, 59)], SKIN_SH, 1)
    # 脚（圆润）
    ell(img, 15, 60, 23, 64, SKIN)
    ell(img, 24, 60, 32, 64, SKIN)
    pxs(img, [(21, 62), (30, 62)], SKIN_SH)
    outline(img)
    return img

def body_yy_side():
    """阳阳侧面站姿全身（朝左）。"""
    img = canvas(36, 68)
    head, _ = head_yy_side()
    img.alpha_composite(head, (4, 0))
    # 颈
    rect(img, 13, 26, 18, 31, SKIN)
    # 躯干（侧视：胸-腹-臀曲线）
    ell(img, 12, 30, 26, 44, SUIT)
    rect(img, 12, 33, 26, 49, SUIT)
    ell(img, 13, 44, 26, 52, SUIT)
    line(img, [(25, 33), (25, 48)], SUIT_D, 1)
    pxs(img, [(13, 33), (14, 33)], SUIT_L)
    # 近侧手臂（垂放）
    line(img, [(16, 33), (14, 46)], SKIN, 5)
    ell(img, 11, 46, 17, 52, SKIN)
    # 远侧手臂（暗影露一点）
    line(img, [(21, 34), (20, 44)], SKIN_SH, 4)
    # 腿（侧视前后关系）
    rect(img, 19, 50, 24, 60, SKIN_SH)          # 远腿
    rect(img, 14, 50, 19, 60, SKIN)             # 近腿
    ell(img, 19, 60, 27, 64, SKIN_SH)           # 远脚
    ell(img, 11, 60, 20, 64, SKIN)              # 近脚（朝左）
    pxs(img, [(12, 62)], SKIN_SH)
    outline(img)
    return img

# ================================================================ 爸爸头部
# 概念特征：成年脸略长；短黑发高额头、两侧剃短渐变（禁锅盖/头盔/平顶）；
# 黑色粗框眼镜包住眼睛+镜腿到耳；露齿亲切笑；五官关系按概念图。

def hair_fade(img, x, y0, y1):
    """鬓角剃短渐变：紧贴发缘的短茬（上密下疏），不成散落点。"""
    for i, y in enumerate(range(y0, y1 + 1)):
        if i <= 2:
            pxs(img, [(x, y), (x + 1, y)], HAIR if i == 0 else HAIR_L)
        elif i % 2 == 1:
            pxs(img, [(x, y)], HAIR_L)

def head_dd_front():
    img = canvas(30, 30)
    # 双耳
    rect(img, 0, 16, 2, 20, SKIN); pxs(img, [(1, 17)], SKIN_SH)
    rect(img, 27, 16, 29, 20, SKIN); pxs(img, [(28, 17)], SKIN_SH)
    # 脸（成年略长，下巴到 y28）
    ell(img, 3, 7, 26, 28, SKIN)
    rect(img, 3, 11, 26, 23, SKIN)
    pxs(img, [(25, 13), (25, 15), (25, 18), (24, 21), (23, 24), (21, 26),
              (18, 27)], SKIN_SH)
    pxs(img, [(25, 20), (24, 23)], SKIN_D)
    # 短黑发：顶部质感 + 高发际线 + 两侧剃短渐变
    ell(img, 2, 0, 27, 8, HAIR)
    rect(img, 2, 3, 27, 6, HAIR)
    pxs(img, [(6, 1), (10, 1), (14, 1), (18, 1), (22, 1),
              (8, 2), (16, 2), (20, 2)], HAIR_L)          # 顶部发束质感
    # 发际线（连续高额头线，非散落点；两个微凹点避免头盔感）
    line(img, [(5, 7), (24, 7)], HAIR, 1)
    pxs(img, [(8, 8), (14, 8), (20, 8)], HAIR)
    pxs(img, [(3, 6), (26, 6)], HAIR)
    hair_fade(img, 2, 6, 10)
    hair_fade(img, 26, 6, 10)
    # 粗眉
    rect(img, 5, 10, 9, 11, HAIR)
    rect(img, 20, 10, 24, 11, HAIR)
    # 黑色粗框眼镜（框 2px，包住眼睛；镜腿到耳）
    rect(img, 4, 13, 13, 20, GLS)
    rect(img, 6, 15, 11, 18, GLS_L)
    rect(img, 16, 13, 25, 20, GLS)
    rect(img, 18, 15, 23, 18, GLS_L)
    rect(img, 13, 15, 16, 16, GLS)              # 镜桥
    line(img, [(4, 15), (1, 15)], GLS, 1)       # 左镜腿
    line(img, [(25, 15), (28, 15)], GLS, 1)     # 右镜腿
    # 眼（镜片后，瞳孔小于镜片，镜片可见）
    rect(img, 7, 16, 10, 18, INK); pxs(img, [(7, 16)], WHT)
    rect(img, 19, 16, 22, 18, INK); pxs(img, [(19, 16)], WHT)
    pxs(img, [(23, 16)], GLS_L)                 # 右镜片反光
    # 鼻（小鼻梁 + 鼻孔点）
    line(img, [(15, 19), (15, 21)], SKIN_SH, 1)
    pxs(img, [(13, 22), (16, 22)], SKIN_SH)
    # 露齿亲切笑（单排上牙 + 深色口腔 + 嘴角上扬）
    rect(img, 9, 24, 20, 26, MOUTH)
    rect(img, 9, 24, 20, 24, TEETH)
    pxs(img, [(8, 23), (21, 23)], MOUTH_D)      # 嘴角上扬
    pxs(img, [(10, 27), (19, 27)], SKIN_SH)     # 下唇影
    outline(img)
    return img

def head_dd_side():
    """爸爸左侧脸（朝左）：镜框侧面 + 镜腿到耳，鬓角渐变可见。"""
    img = canvas(30, 30)
    rect(img, 22, 16, 25, 20, SKIN); pxs(img, [(23, 17)], SKIN_SH)  # 耳
    ell(img, 3, 7, 26, 28, SKIN)
    rect(img, 5, 11, 26, 23, SKIN)
    pxs(img, [(25, 13), (25, 16), (24, 20), (23, 23), (21, 25), (18, 27)], SKIN_SH)
    pxs(img, [(25, 19), (24, 22)], SKIN_D)
    # 发：顶部 + 后脑 + 侧部剃短区（上实心、下缘碎茬，不成散落点）
    ell(img, 2, 0, 27, 8, HAIR)
    rect(img, 2, 3, 27, 6, HAIR)
    rect(img, 24, 5, 27, 12, HAIR)              # 后脑发
    rect(img, 10, 5, 24, 8, HAIR)               # 侧部短发区（实心）
    pxs(img, [(6, 1), (10, 1), (14, 1), (18, 1), (22, 1), (8, 2), (16, 2)], HAIR_L)
    pxs(img, [(4, 7), (6, 7), (8, 7)], HAIR)    # 前发际线
    # 侧区下缘碎茬（贴发缘）
    pxs(img, [(11, 9), (13, 9), (15, 9), (17, 9), (19, 9), (21, 9), (23, 9)], HAIR_L)
    pxs(img, [(12, 10), (16, 10), (20, 10), (23, 10)], HAIR_L)
    pxs(img, [(14, 11), (18, 11), (22, 11)], HAIR_L)
    # 眉
    rect(img, 5, 10, 9, 11, HAIR)
    # 眼镜侧视：前框 + 长镜腿到耳
    rect(img, 3, 13, 10, 20, GLS)
    rect(img, 5, 15, 8, 18, GLS_L)
    line(img, [(10, 15), (24, 15)], GLS, 1)     # 镜腿
    # 眼（镜后，侧视；瞳孔小于镜片）
    rect(img, 5, 16, 7, 18, INK); pxs(img, [(5, 16)], WHT)
    # 鼻（成人凸鼻）
    pxs(img, [(2, 20), (3, 20), (3, 21), (4, 21)], SKIN)
    pxs(img, [(2, 21)], SKIN_SH)
    # 露齿笑（侧视）
    rect(img, 5, 24, 11, 26, MOUTH)
    rect(img, 5, 24, 11, 24, TEETH)
    pxs(img, [(11, 23)], MOUTH_D)
    pxs(img, [(6, 27), (10, 27)], SKIN_SH)
    outline(img)
    fixes = [dict(cx=5, cy=16, base=INK)]
    return img, fixes

def head_dd_34():
    """爸爸斜侧脸（3/4，朝左）：近侧镜框完整、远侧压缩。"""
    img = canvas(30, 30)
    rect(img, 0, 16, 2, 20, SKIN); pxs(img, [(1, 17)], SKIN_SH)
    rect(img, 25, 15, 27, 19, SKIN); pxs(img, [(26, 16)], SKIN_SH)
    ell(img, 3, 7, 26, 28, SKIN)
    rect(img, 3, 11, 26, 23, SKIN)
    pxs(img, [(25, 13), (25, 16), (24, 20), (23, 23), (21, 25), (18, 27)], SKIN_SH)
    pxs(img, [(25, 19), (24, 22)], SKIN_D)
    ell(img, 2, 0, 26, 8, HAIR)
    rect(img, 2, 3, 26, 6, HAIR)
    pxs(img, [(6, 1), (10, 1), (14, 1), (18, 1), (21, 1), (8, 2), (15, 2)], HAIR_L)
    # 发际线（连续）+ 两侧剃短渐变
    line(img, [(4, 7), (23, 7)], HAIR, 1)
    pxs(img, [(7, 8), (13, 8), (19, 8)], HAIR)
    hair_fade(img, 2, 6, 10)
    hair_fade(img, 23, 6, 10)
    rect(img, 5, 10, 9, 11, HAIR)
    rect(img, 19, 10, 23, 11, HAIR)
    # 眼镜：近侧完整框、远侧压缩框
    rect(img, 4, 13, 13, 20, GLS)
    rect(img, 6, 15, 11, 18, GLS_L)
    rect(img, 16, 13, 23, 20, GLS)
    rect(img, 18, 15, 21, 18, GLS_L)
    rect(img, 13, 15, 16, 16, GLS)
    line(img, [(4, 15), (1, 15)], GLS, 1)
    line(img, [(23, 15), (26, 15)], GLS, 1)
    rect(img, 7, 16, 10, 18, INK); pxs(img, [(7, 16)], WHT)
    rect(img, 18, 16, 21, 18, INK); pxs(img, [(18, 16)], WHT)
    line(img, [(15, 19), (15, 21)], SKIN_SH, 1)
    pxs(img, [(13, 22)], SKIN_SH)
    rect(img, 9, 24, 18, 26, MOUTH)
    rect(img, 9, 24, 18, 24, TEETH)
    pxs(img, [(8, 23), (19, 23)], MOUTH_D)
    pxs(img, [(10, 27), (17, 27)], SKIN_SH)
    outline(img)
    return img

# ================================================================ 爸爸全身
def body_dd_front():
    """爸爸正面站姿全身：80px 高（头约29 + 身51），头身比约 1:2.8。"""
    img = canvas(52, 80)
    head = head_dd_front()
    img.alpha_composite(head, (11, 0))
    # 颈
    rect(img, 23, 28, 28, 34, SKIN)
    line(img, [(23, 32), (28, 32)], SKIN_SH, 1)
    # 肩（宽于阳阳）
    ell(img, 9, 33, 43, 43, SKIN)
    # 深色背心泳装：肩带 + 躯干
    rect(img, 17, 34, 22, 39, SUITD)            # 左肩带
    rect(img, 30, 34, 35, 39, SUITD)            # 右肩带
    rect(img, 16, 39, 36, 56, SUITD)
    ell(img, 16, 37, 36, 45, SUITD)
    rect(img, 16, 50, 36, 58, SUITD)
    line(img, [(35, 40), (35, 57)], SUITD_L, 1) # 右侧受光边
    pxs(img, [(17, 40), (18, 40)], SUITD_L)
    # 手臂（成年粗圆润 + 圆手）
    line(img, [(12, 38), (10, 52)], SKIN, 6)
    ell(img, 7, 52, 14, 59, SKIN)
    line(img, [(40, 38), (42, 52)], SKIN, 6)
    ell(img, 38, 52, 45, 59, SKIN)
    pxs(img, [(43, 53), (44, 54)], SKIN_SH)
    # 腿（更长更粗）
    rect(img, 18, 58, 25, 72, SKIN)
    rect(img, 27, 58, 34, 72, SKIN)
    line(img, [(25, 59), (25, 71)], SKIN_SH, 1)
    line(img, [(34, 59), (34, 71)], SKIN_SH, 1)
    # 脚
    ell(img, 16, 72, 26, 77, SKIN)
    ell(img, 27, 72, 37, 77, SKIN)
    pxs(img, [(24, 74), (35, 74)], SKIN_SH)
    outline(img)
    return img

def body_dd_side():
    """爸爸侧面站姿全身（朝左）。"""
    img = canvas(40, 80)
    head, _ = head_dd_side()
    img.alpha_composite(head, (4, 0))
    rect(img, 15, 28, 20, 34, SKIN)
    # 躯干侧视
    ell(img, 13, 33, 29, 48, SUITD)
    rect(img, 13, 36, 29, 55, SUITD)
    ell(img, 14, 49, 29, 58, SUITD)
    line(img, [(28, 36), (28, 54)], SUITD_L, 1)
    # 近侧手臂
    line(img, [(17, 37), (15, 51)], SKIN, 6)
    ell(img, 12, 51, 19, 58, SKIN)
    # 远侧手臂
    line(img, [(23, 38), (22, 49)], SKIN_SH, 4)
    # 腿
    rect(img, 21, 56, 27, 72, SKIN_SH)
    rect(img, 15, 56, 21, 72, SKIN)
    ell(img, 21, 72, 30, 77, SKIN_SH)
    ell(img, 12, 72, 22, 77, SKIN)
    pxs(img, [(13, 74)], SKIN_SH)
    outline(img)
    return img

# ================================================================ 组装
def build_all():
    """返回 {key: Image}；key 如 yy_head_front / dd_body_side。"""
    out = {}
    out["yy_head_front"] = head_yy_front()
    side, fixes = head_yy_side()
    out["yy_head_L"] = side
    out["yy_head_R"] = mirror_fix(side, fixes)
    out["yy_head_34"] = head_yy_34()
    out["yy_body_front"] = body_yy_front()
    out["yy_body_side"] = body_yy_side()
    out["dd_head_front"] = head_dd_front()
    dside, dfixes = head_dd_side()
    out["dd_head_L"] = dside
    out["dd_head_R"] = mirror_fix(dside, dfixes)
    out["dd_head_34"] = head_dd_34()
    out["dd_body_front"] = body_dd_front()
    out["dd_body_side"] = body_dd_side()
    return out

HEAD_KEYS = ["head_front", "head_L", "head_R", "head_34"]
BODY_KEYS = ["body_front", "body_side"]
HEAD_LABELS = ["FRONT", "SIDE-L", "SIDE-R", "3-4"]

# ================================================================ 审核图
BG = (158, 166, 178, 255)
LABEL = (25, 30, 45, 255)
SUBLABEL = (52, 62, 82, 255)
ACCENT = (168, 88, 16, 255)

def on_color(w, h, c=BG):
    return Image.new("RGBA", (w, h), c)

def sheet_model(char, A):
    """单角色标准模型表：四向头 1x+3x；正/侧全身 1x+3x。"""
    heads = [A[f"{char}_head_front"], A[f"{char}_head_L"],
             A[f"{char}_head_R"], A[f"{char}_head_34"]]
    bf = A[f"{char}_body_front"]; bs = A[f"{char}_body_side"]
    bx = 380
    W = bx + bf.size[0] + 40 + bf.size[0] * 3 + bs.size[0] + 40 + bs.size[0] * 3 + 20
    H = 40 + max(84, bf.size[1] * 3) + 20
    s = on_color(W, H)
    text(s, 8, 8, ("YY" if char == "yy" else "DAD") + " STANDARD MODEL", LABEL)
    for i, h in enumerate(heads):
        x = 8 + i * 76
        paste_x = x
        D(s).rectangle([paste_x, 26, paste_x + h.size[0] + 1, 26 + h.size[1] + 1],
                       outline=SUBLABEL)
        s.alpha_composite(h, (paste_x + 1, 27))
        text(s, paste_x, 60, HEAD_LABELS[i], SUBLABEL)
        z3 = zoom(h, 3)
        D(s).rectangle([paste_x, 70, paste_x + z3.size[0] + 1, 70 + z3.size[1] + 1],
                       outline=SUBLABEL)
        s.alpha_composite(z3, (paste_x + 1, 71))
    text(s, bx, 8, "BODY FRONT / SIDE 1X+3X", SUBLABEL)
    D(s).rectangle([bx, 26, bx + bf.size[0] + 1, 26 + bf.size[1] + 1], outline=SUBLABEL)
    s.alpha_composite(bf, (bx + 1, 27))
    x = bx + bf.size[0] + 40
    z3 = zoom(bf, 3)
    D(s).rectangle([x, 26, x + z3.size[0] + 1, 26 + z3.size[1] + 1], outline=SUBLABEL)
    s.alpha_composite(z3, (x + 1, 27))
    x += z3.size[0] + 40
    D(s).rectangle([x, 26, x + bs.size[0] + 1, 26 + bs.size[1] + 1], outline=SUBLABEL)
    s.alpha_composite(bs, (x + 1, 27))
    x += bs.size[0] + 40
    z3 = zoom(bs, 3)
    D(s).rectangle([x, 26, x + z3.size[0] + 1, 26 + z3.size[1] + 1], outline=SUBLABEL)
    s.alpha_composite(z3, (x + 1, 27))
    return s

def sheet_ratio(A):
    """头身比例标尺：头高为单位堆叠。"""
    s = on_color(400, 120)
    text(s, 8, 8, "HEAD-TO-BODY RATIO", LABEL)
    for i, char in enumerate(("yy", "dd")):
        body = A[f"{char}_body_front"]
        head = A[f"{char}_head_front"]
        hb = opaque_bbox(head)
        hh = hb[3] - hb[1]
        bb = opaque_bbox(body)
        bh = bb[3] - bb[1]
        x0 = 30 + i * 190
        s.alpha_composite(body, (x0, 30))
        ratio = bh / hh
        # 标尺：以头高为单位堆叠方框
        rx = x0 + body.size[0] + 16
        for k in range(3):
            y0 = 30 + bh - (k + 1) * hh
            D(s).rectangle([rx, y0, rx + 14, y0 + hh - 1],
                           outline=ACCENT if k < int(round(ratio)) else SUBLABEL)
        text(s, rx + 20, 30 + bh - hh, "1 HEAD", SUBLABEL)
        text(s, x0, 30 + bh + 6, ("YY " if char == "yy" else "DAD ") +
             f"{bh}px = {ratio:.2f} HEAD", LABEL)
    return s

def sheet_palette():
    s = on_color(560, 30 + 14 * 18 + 10)
    text(s, 8, 8, "FIXED PALETTE", LABEL)
    items = list(PALETTE.items())
    for i, (name, c) in enumerate(items):
        x = 8 + (i // 14) * 280
        y = 30 + (i % 14) * 18
        rect(s, x, y, x + 15, y + 15, c)
        D(s).rectangle([x, y, x + 15, y + 15], outline=LABEL)
        text(s, x + 22, y + 5, name, LABEL)
        text(s, x + 130, y + 5, "#%02X%02X%02X" % c[:3], SUBLABEL)
    return s

def sheet_structure(A):
    """结构拆解：阳阳帽/镜；爸爸发/镜。各部件 1x+4x。"""
    s = on_color(720, 260)
    text(s, 8, 8, "STRUCTURE BREAKDOWN", LABEL)
    # 阳阳：帽+泳镜组装（取自头部上部）与镜片单元
    text(s, 8, 22, "YY CAP+GOGGLES", SUBLABEL)
    capzone = A["yy_head_front"].crop((2, 0, 26, 13))
    s.alpha_composite(capzone, (8, 32))
    z4 = zoom(capzone, 4)
    s.alpha_composite(z4, (8, 52))
    labels = ["CAP", "PANEL", "STRAP", "LENS", "BRIDGE"]
    for i, lb in enumerate(labels):
        text(s, 130, 56 + i * 18, lb, LABEL)
    # 指向线（帽/分区/镜带/镜片/镜桥 → 放大图对应行）
    for i, yy in enumerate([58, 66, 82, 96, 106]):
        line(s, [(118, 56 + i * 18 + 2), (124, yy)], SUBLABEL, 1)
    # 爸爸：发+眼镜组装与部件
    text(s, 380, 22, "DAD HAIR+GLASSES", SUBLABEL)
    hairzone = A["dd_head_front"].crop((1, 0, 29, 22))
    s.alpha_composite(hairzone, (380, 32))
    z4 = zoom(hairzone, 4)
    s.alpha_composite(z4, (380, 62))
    labels = ["HAIR", "FADE", "FRAME", "LENS", "TEMPLE"]
    for i, lb in enumerate(labels):
        text(s, 510, 66 + i * 18, lb, LABEL)
    for i, yy in enumerate([70, 96, 110, 118, 100]):
        line(s, [(498, 66 + i * 18 + 2), (504, yy)], SUBLABEL, 1)
    return s

def sheet_height(A):
    """同尺度身高对照：同一基线 + 10px 刻度尺。"""
    yy = A["yy_body_front"]; dd = A["dd_body_front"]
    yy_bb = opaque_bbox(yy); dd_bb = opaque_bbox(dd)
    yy_h = yy_bb[3] - yy_bb[1]; dd_h = dd_bb[3] - dd_bb[1]
    H = 30 + 80 + 18
    s = on_color(260, H)
    text(s, 8, 8, "HEIGHT COMPARE (SAME SCALE)", LABEL)
    base = 30 + 80
    # 刻度尺
    for y in range(30, base + 1, 10):
        line(s, [(8, y), (14, y)], LABEL, 1)
        text(s, 16, y - 2, str(base - y), SUBLABEL)
    line(s, [(8, 30), (8, base)], LABEL, 1)
    s.alpha_composite(yy, (60, base - yy_h))
    s.alpha_composite(dd, (160, base - dd_h))
    line(s, [(50, base - yy_h), (150, base - yy_h)], ACCENT, 1)   # 阳阳头顶线
    line(s, [(150, base - dd_h), (250, base - dd_h)], ACCENT, 1)  # 爸爸头顶线
    line(s, [(20, base), (250, base)], LABEL, 1)
    text(s, 60, base + 6, f"YY {yy_h}PX", LABEL)
    text(s, 160, base + 6, f"DAD {dd_h}PX", LABEL)
    return s

def to_gray(img):
    """隐藏队色：所有不透明像素转 8 级灰度（保留结构与明暗）。"""
    g = canvas(*img.size)
    src = img.load()
    dst = g.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, gg, b, a = src[x, y]
            if a:
                l = (r * 299 + gg * 587 + b * 114) // 1000
                l = (l // 32) * 32 + 16
                dst[x, y] = (l, l, l, 255)
    return g

def sheet_blind(A):
    """身份盲审：8 头（1x+4x）+ 4 全身（1x+3x），匿名编号，灰度去队色。"""
    entries = []
    for char in ("yy", "dd"):
        for k in HEAD_KEYS:
            entries.append((f"{char}_{k}", A[f"{char}_{k}"]))
        for k in BODY_KEYS:
            entries.append((f"{char}_{k}", A[f"{char}_{k}"]))
    order = [7, 2, 10, 4, 0, 9, 5, 11, 3, 8, 1, 6]
    head_idx = [i for i, ei in enumerate(order) if "head" in entries[ei][0]]
    body_idx = [i for i, ei in enumerate(order) if "body" in entries[ei][0]]
    # 头部区：8 项 × (1x + 4x)
    hw, hh = 150, 210
    hcols = 4
    hrows = 2
    # 全身区：4 项 × (1x + 3x)
    bw = 200
    W = 20 + max(hw * hcols, bw * 4)
    H = 30 + hh * hrows + 40 + (80 * 3 + 80)
    s = on_color(W, H)
    text(s, 8, 8, "BLIND IDENTITY REVIEW (GRAYSCALE)", LABEL)
    text(s, 8, 20, "HEADS 1X+4X", SUBLABEL)
    for j, i in enumerate(head_idx):
        key, img = entries[order[i]]
        g = to_gray(img)
        cx = 20 + (j % hcols) * hw
        cy = 32 + (j // hcols) * hh
        text(s, cx, cy, "#%02d" % (i + 1), ACCENT)
        s.alpha_composite(g, (cx + 4, cy + 12))
        z4 = zoom(g, 4)
        s.alpha_composite(z4, (cx + 4, cy + 56))
    yb = 32 + hh * hrows + 10
    text(s, 8, yb, "BODIES 1X+3X", SUBLABEL)
    for j, i in enumerate(body_idx):
        key, img = entries[order[i]]
        g = to_gray(img)
        cx = 20 + j * bw
        text(s, cx, yb + 12, "#%02d" % (i + 1), ACCENT)
        s.alpha_composite(g, (cx + 4, yb + 24))
        z3 = zoom(g, 3)
        s.alpha_composite(z3, (cx + 4, yb + 116))
    return s, order, [k for k, _ in entries]

# ================================================================ 主流程
EXPECTED_HTML_SHA = "412416e95bfe4c98f4b039dc4a24fd9b28c2c23989254f22ee494d2e7bcde306"
ROOT = HERE.parent.parent.parent
HTML = ROOT / "阳阳水泳大乱斗-原版复刻.html"

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def save_png(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    img.save(tmp, format="PNG")
    tmp.replace(path)

def check_alpha(img):
    bad = set()
    for px in img.getdata():
        if px[3] not in (0, 255):
            bad.add(px[3])
    return sorted(bad)

def main():
    SPRITES.mkdir(parents=True, exist_ok=True)
    A = build_all()
    manifest = {
        "schemaVersion": 1,
        "stage": "CONCEPT-MODEL-0",
        "artifactKind": "concept-character-standard-model",
        "applied": False,
        "note": "人物标准模型锁定门；不含任何游戏动作；未接入游戏",
        "identitySource": "本地两张概念参考图（仅人工观察，未作为构建输入）",
        "actionSource": "本阶段无动作；动作唯一来源为FC原版（后续CONCEPT-ACTION-0）",
        "palette": {k: list(v) for k, v in PALETTE.items()},
        "sprites": [],
        "sheets": [],
        "checks": {},
    }
    # 保存 12 张标准稿
    for key in sorted(A.keys()):
        img = A[key]
        bad = check_alpha(img)
        if bad:
            raise SystemExit(f"alpha非0/255: {key} {bad}")
        save_png(img, SPRITES / f"{key}.png")
        bb = opaque_bbox(img)
        manifest["sprites"].append({
            "file": f"sprites/{key}.png", "key": key,
            "canvas": list(img.size),
            "opaqueBBox": list(bb),
            "opaqueSize": [bb[2] - bb[0], bb[3] - bb[1]],
            "sha256": sha256_bytes((SPRITES / f"{key}.png").read_bytes()),
        })
    # 机器检查：头部与身高门槛
    fails = []
    for char, need in (("yy", 24), ("dd", 28)):
        for k in HEAD_KEYS:
            s = next(x for x in manifest["sprites"] if x["key"] == f"{char}_{k}")
            if s["opaqueSize"][0] < need - 2 or s["opaqueSize"][1] < need - 2:
                fails.append((s["key"], s["opaqueSize"]))
    manifest["checks"]["headMinSize"] = {
        "rule": "yy头>=约24px, dd头>=约28px（容差2px）", "fail": fails, "pass": not fails}
    fails = []
    for char, lo, hi in (("yy", 60, 72), ("dd", 70, 84)):
        for k in BODY_KEYS:
            s = next(x for x in manifest["sprites"] if x["key"] == f"{char}_{k}")
            h = s["opaqueSize"][1]
            if not (lo - 2 <= h <= hi + 2):
                fails.append((s["key"], h))
    manifest["checks"]["bodyHeight"] = {
        "rule": "yy全身60-72px, dd全身70-84px（容差2px）", "fail": fails, "pass": not fails}
    # 头身比
    ratios = {}
    for char in ("yy", "dd"):
        hb = opaque_bbox(A[f"{char}_head_front"])
        bb = opaque_bbox(A[f"{char}_body_front"])
        ratios[char] = round((bb[3] - bb[1]) / (hb[3] - hb[1]), 2)
    manifest["checks"]["headBodyRatio"] = {
        "rule": "总高/头高 约2.5-3", "ratio": ratios,
        "pass": all(2.3 <= r <= 3.2 for r in ratios.values())}
    # HTML 未改动
    html_sha = sha256_bytes(HTML.read_bytes())
    manifest["checks"]["mainHtmlUnchanged"] = {
        "pass": html_sha == EXPECTED_HTML_SHA, "sha256": html_sha}
    if html_sha != EXPECTED_HTML_SHA:
        raise SystemExit("主HTML SHA 变化，立即停止")
    # 审核图
    sheets = {
        "阳阳标准模型表.png": sheet_model("yy", A),
        "爸爸标准模型表.png": sheet_model("dd", A),
        "头身比例标尺.png": sheet_ratio(A),
        "固定调色板.png": sheet_palette(),
        "结构拆解.png": sheet_structure(A),
        "身高对照.png": sheet_height(A),
    }
    blind, order, keys = sheet_blind(A)
    sheets["身份盲审表.png"] = blind
    for name, img in sheets.items():
        bad = check_alpha(img)
        if bad:
            raise SystemExit(f"alpha非0/255: {name} {bad}")
        save_png(img, HERE / name)
        manifest["sheets"].append({"file": name, "size": list(img.size),
                                   "sha256": sha256_bytes((HERE / name).read_bytes())})
    manifest["blindAnswer"] = {"order": order, "keyOfIndex": keys,
                               "note": "#NN 对应 entries[order[NN-1]]；盲审图为灰度去队色版"}
    with open(HERE / "concept_model_0_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    print("sprites:", len(manifest["sprites"]))
    print("checks:", json.dumps({k: v.get("pass") for k, v in manifest["checks"].items()}))
    print("blind order:", order)

if __name__ == "__main__":
    main()
