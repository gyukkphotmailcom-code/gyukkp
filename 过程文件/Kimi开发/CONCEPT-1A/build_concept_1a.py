#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONCEPT-1A：概念画风版角色身份与静态动作美术门（确定性构建器）

- 只使用 Pillow 作为构建期工具；不联网；不读取任何隐私参考图/照片/视频。
- 所有像素逐点绘制，整数坐标，alpha 只有 0/255，无抗锯齿。
- 相同输入重复构建 → 相同文件 SHA-256。
- 输出仅写入本脚本所在目录（过程文件/Kimi开发/CONCEPT-1A/）。
"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SPRITES = HERE / "sprites"

# ---------------------------------------------------------------- 调色板
# 表面（水上）调色板
OUT     = (26, 24, 44, 255)     # 硬描边：深藏青
SKIN    = (244, 186, 136, 255)  # 阳阳肤色
SKIN_SH = (222, 148, 98, 255)   # 阳阳肤影
SKIND   = (236, 168, 118, 255)  # 爸爸肤色（略深）
SKIND_SH= (200, 128, 82, 255)   # 爸爸肤影
CAP     = (47, 125, 225, 255)   # 泳帽蓝
CAP_L   = (111, 179, 255, 255)  # 泳帽亮蓝
CAP_D   = (30, 90, 168, 255)    # 泳帽深蓝
GOG_F   = (232, 244, 255, 255)  # 泳镜框
GOG_L   = (23, 59, 116, 255)    # 泳镜片
SUIT    = (43, 111, 212, 255)   # 阳阳蓝色泳装
SUIT_D  = (28, 78, 158, 255)    # 泳装阴影
HAIR    = (34, 28, 32, 255)     # 爸爸黑发
HAIR_L  = (62, 52, 58, 255)     # 黑发高光
GLS     = (16, 16, 24, 255)     # 黑框眼镜
GLS_L   = (176, 208, 224, 255)  # 镜片
SUITD   = (44, 44, 56, 255)     # 爸爸深色泳装
SUITD_L = (66, 66, 82, 255)
WHT     = (255, 255, 255, 255)
INK     = (20, 20, 30, 255)     # 瞳孔
BROW    = (62, 42, 32, 255)     # 眉毛
MOUTH   = (128, 58, 48, 255)    # 嘴
MOUTH_D = (86, 34, 30, 255)
WAT     = (110, 190, 236, 255)  # 水面
WAT_L   = (214, 242, 255, 255)  # 水花亮
WAT_D   = (62, 142, 200, 255)   # 水面暗

# 水下专用调色（显式映射，写入 manifest）
UW_MAP = {
    SKIN:    (150, 196, 204, 255),
    SKIN_SH: (108, 158, 172, 255),
    SKIND:   (140, 184, 194, 255),
    SKIND_SH:(100, 146, 160, 255),
    CAP:     (36, 104, 168, 255),
    CAP_L:   (82, 152, 206, 255),
    CAP_D:   (22, 70, 124, 255),
    GOG_F:   (190, 226, 238, 255),
    GOG_L:   (18, 48, 96, 255),
    SUIT:    (32, 88, 158, 255),
    SUIT_D:  (20, 60, 116, 255),
    HAIR:    (24, 28, 40, 255),
    HAIR_L:  (44, 54, 68, 255),
    GLS:     (12, 16, 24, 255),
    GLS_L:   (118, 166, 190, 255),
    SUITD:   (30, 34, 48, 255),
    SUITD_L: (46, 52, 70, 255),
    OUT:     (14, 18, 36, 255),
    MOUTH:   (96, 60, 64, 255),
    MOUTH_D: (64, 38, 44, 255),
    BROW:    (46, 40, 44, 255),
    INK:     (14, 16, 26, 255),
}
BUBBLE  = (200, 238, 250, 255)  # 气泡

def uw(c):
    return UW_MAP.get(c, c)

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

# ---------------------------------------------------------------- 头部构建
def head_yy_side(uwmode=False):
    """阳阳侧脸（朝左），含蓝泳帽+帽上泳镜。返回 (img, 细节锚点dict)"""
    S = uw if uwmode else (lambda c: c)
    img = canvas(28, 28)
    # 脸（圆短儿童脸）
    ell(img, 2, 8, 22, 26, S(SKIN))
    rect(img, 2, 14, 22, 22, S(SKIN))
    # 泳帽（覆盖头顶与后脑）
    ell(img, 3, 0, 26, 15, S(CAP))
    rect(img, 3, 6, 26, 12, S(CAP))
    rect(img, 22, 10, 26, 16, S(CAP))          # 帽沿包到后脑
    line(img, [(7, 2), (20, 2)], S(CAP_L), 1)  # 帽顶高光
    line(img, [(5, 4), (5, 9)], S(CAP_L), 1)   # 帽侧条纹亮
    line(img, [(24, 4), (24, 12)], S(CAP_D), 1)
    # 帽上泳镜（侧视：前后两个镜片圆）
    ell(img, 5, 3, 12, 10, S(GOG_F)); ell(img, 6, 4, 11, 9, S(GOG_L))
    ell(img, 12, 3, 19, 10, S(GOG_F)); ell(img, 13, 4, 18, 9, S(GOG_L))
    rect(img, 11, 5, 13, 6, S(GOG_F))          # 镜桥
    # 眼（大眼儿童）
    rect(img, 5, 15, 10, 20, WHT)
    rect(img, 6, 16, 9, 20, S(INK))
    # 眉
    line(img, [(5, 13), (9, 13)], S(BROW), 1)
    # 鼻（小）
    pxs(img, [(2, 19), (3, 19)], S(SKIN_SH))
    # 嘴（小开口笑）
    rect(img, 5, 22, 9, 24, S(MOUTH))
    rect(img, 5, 22, 9, 22, WHT)
    # 耳
    rect(img, 21, 15, 23, 18, S(SKIN))
    pxs(img, [(22, 16)], S(SKIN_SH))
    anchors = {"eye_hi": [(6, 16)], "gog_hi": [(7, 5), (14, 5)]}
    return img, anchors

def head_dd_side(uwmode=False):
    """爸爸侧脸（朝左），短黑发+黑粗框眼镜。30×30"""
    S = uw if uwmode else (lambda c: c)
    img = canvas(30, 30)
    # 脸（成年略长）
    ell(img, 2, 9, 25, 28, S(SKIND))
    rect(img, 2, 15, 25, 24, S(SKIND))
    # 短黑发（高发际线）
    ell(img, 3, 0, 29, 13, S(HAIR))
    rect(img, 3, 5, 29, 9, S(HAIR))
    rect(img, 26, 8, 29, 15, S(HAIR))          # 后脑发
    line(img, [(8, 1), (20, 1)], S(HAIR_L), 1)
    # 黑粗框眼镜（侧视：包住可见眼 + 镜腿到耳）
    rect(img, 4, 14, 15, 21, S(GLS))
    rect(img, 5, 15, 14, 20, S(GLS_L))
    line(img, [(15, 16), (26, 16)], S(GLS), 2)  # 镜腿
    # 眼（镜片后）
    rect(img, 7, 16, 11, 20, WHT)
    rect(img, 8, 17, 10, 20, S(INK))
    # 眉
    line(img, [(6, 12), (11, 12)], S(HAIR), 1)
    # 鼻
    pxs(img, [(2, 20), (3, 20), (3, 21)], S(SKIND_SH))
    # 嘴（露齿亲切笑）
    rect(img, 5, 24, 12, 26, S(MOUTH))
    rect(img, 5, 24, 12, 24, WHT)
    pxs(img, [(4, 23), (13, 23)], S(MOUTH_D))   # 嘴角上扬
    # 耳
    rect(img, 24, 16, 26, 19, S(SKIND))
    pxs(img, [(25, 17)], S(SKIND_SH))
    anchors = {"eye_hi": [(8, 17)], "gog_hi": [(6, 15)]}
    return img, anchors

def head_yy_front(uwmode=False, gasp=False):
    """阳阳正面/微仰脸（BREATH/HIT 用），28×28"""
    S = uw if uwmode else (lambda c: c)
    img = canvas(28, 28)
    ell(img, 2, 8, 25, 26, S(SKIN))
    rect(img, 2, 14, 25, 22, S(SKIN))
    ell(img, 3, 0, 25, 14, S(CAP))
    rect(img, 3, 6, 25, 11, S(CAP))
    line(img, [(8, 2), (19, 2)], S(CAP_L), 1)
    # 帽上泳镜（正视双圆）
    ell(img, 4, 2, 11, 9, S(GOG_F)); ell(img, 5, 3, 10, 8, S(GOG_L))
    ell(img, 16, 2, 23, 9, S(GOG_F)); ell(img, 17, 3, 22, 8, S(GOG_L))
    rect(img, 11, 4, 16, 5, S(GOG_F))
    # 双眼（大眼）
    rect(img, 5, 14, 9, 19, WHT); rect(img, 6, 15, 8, 19, S(INK))
    rect(img, 17, 14, 21, 19, WHT); rect(img, 18, 15, 20, 19, S(INK))
    line(img, [(5, 12), (9, 12)], S(BROW), 1)
    line(img, [(17, 12), (21, 12)], S(BROW), 1)
    # 鼻
    pxs(img, [(13, 19), (14, 19)], S(SKIN_SH))
    # 嘴
    if gasp:
        rect(img, 11, 22, 16, 25, S(MOUTH_D))   # 换气大口
        rect(img, 11, 22, 16, 22, WHT)
    else:
        rect(img, 10, 22, 16, 24, S(MOUTH))
        rect(img, 10, 22, 16, 22, WHT)
    # 双耳
    rect(img, 0, 14, 2, 17, S(SKIN)); rect(img, 25, 14, 27, 17, S(SKIN))
    anchors = {"eye_hi": [(6, 15), (18, 15)], "gog_hi": [(6, 4), (18, 4)]}
    return img, anchors

def head_dd_front(uwmode=False, gasp=False):
    """爸爸正面（BREATH/HIT 用），30×30"""
    S = uw if uwmode else (lambda c: c)
    img = canvas(30, 30)
    ell(img, 2, 9, 27, 28, S(SKIND))
    rect(img, 2, 15, 27, 24, S(SKIND))
    ell(img, 3, 0, 27, 12, S(HAIR))
    rect(img, 3, 5, 27, 8, S(HAIR))
    line(img, [(9, 1), (21, 1)], S(HAIR_L), 1)
    # 黑粗框眼镜（正视双方框+镜桥）
    rect(img, 3, 13, 12, 20, S(GLS)); rect(img, 4, 14, 11, 19, S(GLS_L))
    rect(img, 17, 13, 26, 20, S(GLS)); rect(img, 18, 14, 25, 19, S(GLS_L))
    rect(img, 12, 15, 17, 16, S(GLS))
    # 眼
    rect(img, 6, 15, 9, 19, WHT); rect(img, 7, 16, 9, 19, S(INK))
    rect(img, 20, 15, 23, 19, WHT); rect(img, 21, 16, 23, 19, S(INK))
    line(img, [(5, 11), (10, 11)], S(HAIR), 1)
    line(img, [(19, 11), (24, 11)], S(HAIR), 1)
    pxs(img, [(13, 20), (14, 20), (15, 20)], S(SKIND_SH))
    if gasp:
        rect(img, 11, 24, 18, 27, S(MOUTH_D))
        rect(img, 11, 24, 18, 24, WHT)
    else:
        rect(img, 9, 24, 19, 26, S(MOUTH))
        rect(img, 9, 24, 19, 24, WHT)
        pxs(img, [(8, 23), (20, 23)], S(MOUTH_D))
    rect(img, 0, 15, 2, 18, S(SKIND)); rect(img, 27, 15, 29, 18, S(SKIND))
    anchors = {"eye_hi": [(7, 16), (21, 16)], "gog_hi": [(5, 14), (19, 14)]}
    return img, anchors


# ---------------------------------------------------------------- 姿态构建
# 每个姿态函数在单元格内朝左绘制角色层与水花层。
# 返回 (char_layer, fx_layer, hi_list)；hi_list 项为 dict(cx,cy,sw,ox,oy,base)，
# 用于 L/R 高光自适应：R 向整图镜像后，擦除镜像旧高光并在结构左上角重画。

def pal_for(char, uwmode):
    if char == "yy":
        p = dict(skin=SKIN, sh=SKIN_SH, suit=SUIT, suitd=SUIT_D)
    else:
        p = dict(skin=SKIND, sh=SKIND_SH, suit=SUITD, suitd=SUITD_L)
    if uwmode:
        p = {k: uw(v) for k, v in p.items()}
    return p

def head_for(char, view, uwmode, gasp=False, hit=False, goggles_down=False):
    S = uw if uwmode else (lambda c: c)
    if char == "yy":
        if view == "side":
            img, _ = head_yy_side(uwmode)
            if goggles_down:
                S = uw if uwmode else (lambda c: c)
                # 帽上泳镜抹除（用帽色回填），泳镜下移到眼前
                rect(img, 5, 3, 19, 10, S(CAP))
                line(img, [(7, 2), (20, 2)], S(CAP_L), 1)
                ell(img, 3, 13, 12, 22, S(GOG_F))
                ell(img, 4, 14, 11, 21, S(GOG_L))
                line(img, [(12, 16), (26, 15)], S(GOG_F), 1)   # 镜带绕头
                rect(img, 5, 16, 8, 19, S(INK))                # 镜片后眼瞳
                line(img, [(5, 13), (9, 13)], S(BROW), 1)
                hi = [dict(cx=4, cy=14, sw=8, ox=1, oy=1, base=S(GOG_L))]
            else:
                hi = [dict(cx=5, cy=15, sw=6, ox=1, oy=1, base=S(INK)),
                      dict(cx=5, cy=3, sw=8, ox=2, oy=2, base=S(GOG_L)),
                      dict(cx=12, cy=3, sw=8, ox=2, oy=2, base=S(GOG_L))]
        else:
            img, _ = head_yy_front(uwmode, gasp=gasp)
            hi = [dict(cx=5, cy=14, sw=5, ox=1, oy=1, base=S(INK)),
                  dict(cx=17, cy=14, sw=5, ox=1, oy=1, base=S(INK)),
                  dict(cx=4, cy=2, sw=8, ox=2, oy=2, base=S(GOG_L)),
                  dict(cx=16, cy=2, sw=8, ox=2, oy=2, base=S(GOG_L))]
    else:
        if view == "side":
            img, _ = head_dd_side(uwmode)
            hi = [dict(cx=7, cy=16, sw=5, ox=1, oy=1, base=S(INK)),
                  dict(cx=5, cy=15, sw=10, ox=1, oy=1, base=S(GLS_L))]
        else:
            img, _ = head_dd_front(uwmode, gasp=gasp)
            hi = [dict(cx=6, cy=15, sw=4, ox=1, oy=1, base=S(INK)),
                  dict(cx=20, cy=15, sw=4, ox=1, oy=1, base=S(INK)),
                  dict(cx=4, cy=14, sw=8, ox=1, oy=1, base=S(GLS_L)),
                  dict(cx=18, cy=14, sw=8, ox=1, oy=1, base=S(GLS_L))]
    if hit:
        # 受击表情：眼变 ><，嘴变小 gasp（覆盖原眼/嘴区域）
        S = uw if uwmode else (lambda c: c)
        if view == "side":
            if char == "yy":
                rect(img, 5, 15, 10, 20, S(SKIN))
                line(img, [(5, 15), (9, 19)], S(INK), 1)
                line(img, [(9, 15), (5, 19)], S(INK), 1)
                rect(img, 5, 22, 9, 24, S(MOUTH_D))
                hi = [h for h in hi if h["base"] != S(INK)]
            else:
                rect(img, 7, 16, 11, 20, S(GLS_L))
                line(img, [(7, 16), (10, 19)], S(INK), 1)
                line(img, [(10, 16), (7, 19)], S(INK), 1)
                rect(img, 5, 24, 12, 26, S(MOUTH_D))
                hi = [h for h in hi if h["base"] != S(INK)]
        else:
            if char == "yy":
                rect(img, 5, 14, 9, 19, S(SKIN)); rect(img, 17, 14, 21, 19, S(SKIN))
                line(img, [(5, 14), (9, 18)], S(INK), 1); line(img, [(9, 14), (5, 18)], S(INK), 1)
                line(img, [(17, 14), (21, 18)], S(INK), 1); line(img, [(21, 14), (17, 18)], S(INK), 1)
                rect(img, 10, 22, 16, 24, S(MOUTH_D))
            else:
                rect(img, 6, 15, 9, 19, S(GLS_L)); rect(img, 20, 15, 23, 19, S(GLS_L))
                line(img, [(6, 15), (9, 18)], S(INK), 1); line(img, [(9, 15), (6, 18)], S(INK), 1)
                line(img, [(20, 15), (23, 18)], S(INK), 1); line(img, [(23, 15), (20, 18)], S(INK), 1)
                rect(img, 9, 24, 19, 26, S(MOUTH_D))
            hi = [h for h in hi if h["base"] != S(INK)]
    return img, hi

def paste(dst, src, x, y):
    dst.alpha_composite(src, (x, y))

# ---- 姿态 1：SURF_SWIM 水面游泳（侧视，头出水）----
def pose_surf(char):
    w, h = (112, 56) if char == "yy" else (128, 64)
    cl = canvas(w, h)          # 角色层
    fx = canvas(w, h)          # 水花层
    p = pal_for(char, False)
    hx, hy = (10, 0) if char == "yy" else (12, 0)
    head, hi = head_for(char, "side", False)
    # 前臂前伸（朝左）
    if char == "yy":
        line(cl, [(24, 33), (8, 29)], p["skin"], 5)
        ell(cl, 2, 26, 9, 32, p["skin"])
        line(cl, [(26, 37), (40, 40)], p["sh"], 4)          # 远臂（水面下暗影）
        ell(cl, 20, 28, 36, 42, p["skin"])                  # 肩
        rect(cl, 24, 24, 32, 34, p["skin"])                 # 颈部连接
        ell(cl, 26, 29, 70, 41, p["suit"])                  # 躯干
        rect(cl, 30, 29, 66, 41, p["suit"])
        line(cl, [(30, 40), (64, 40)], p["suitd"], 1)
        line(cl, [(66, 34), (88, 37)], p["skin"], 6)        # 大腿
        line(cl, [(88, 37), (99, 43)], p["skin"], 5)        # 小腿
        line(cl, [(99, 43), (105, 40)], p["skin"], 4)       # 脚
        line(cl, [(66, 31), (86, 33)], p["sh"], 5)          # 远腿
        line(cl, [(86, 33), (95, 38)], p["sh"], 4)
        splash = [(4, 34), (8, 33), (12, 35), (16, 34), (6, 36), (14, 37), (2, 37),
                  (10, 31), (18, 32), (98, 34), (102, 33), (106, 35), (108, 37),
                  (100, 31), (104, 30), (110, 33)]
        drops = [(7, 27), (15, 29), (103, 26), (107, 29)]
    else:
        line(cl, [(28, 37), (8, 32)], p["skin"], 6)
        ell(cl, 2, 28, 10, 36, p["skin"])
        line(cl, [(30, 42), (46, 46)], p["sh"], 4)
        ell(cl, 24, 32, 42, 48, p["skin"])
        rect(cl, 28, 26, 36, 38, p["skin"])                 # 颈部连接
        ell(cl, 30, 33, 80, 47, p["suit"])
        rect(cl, 34, 33, 76, 47, p["suit"])
        line(cl, [(34, 46), (74, 46)], p["suitd"], 1)
        line(cl, [(76, 39), (100, 42)], p["skin"], 7)
        line(cl, [(100, 42), (113, 49)], p["skin"], 5)
        line(cl, [(113, 49), (120, 46)], p["skin"], 4)
        line(cl, [(76, 35), (98, 37)], p["sh"], 5)
        line(cl, [(98, 37), (108, 43)], p["sh"], 4)
        splash = [(4, 39), (9, 38), (14, 40), (20, 39), (7, 42), (16, 43), (2, 42),
                  (12, 36), (22, 36), (112, 40), (117, 39), (121, 41), (124, 43),
                  (114, 36), (119, 35), (125, 38)]
        drops = [(8, 30), (18, 32), (118, 31), (122, 34)]
    # 水花与水面
    rect(fx, 0, h - 10, w - 1, h - 6, WAT)
    line(fx, [(0, h - 10), (w - 1, h - 10)], WAT_L, 1)
    pxs(fx, splash, WAT_L)
    pxs(fx, drops, WHT)
    line(fx, [(6, h - 8), (30, h - 8)], WAT_D, 1)
    line(fx, [(w - 30, h - 7), (w - 8, h - 7)], WAT_D, 1)
    return cl, fx, head, hi, (hx, hy)

# ---- 姿态 2：JUMP 团身跳跃 ----
def pose_jump(char):
    w = h = 96
    cl = canvas(w, h)
    fx = canvas(w, h)
    p = pal_for(char, False)
    if char == "yy":
        hx, hy = 16, 2
        line(cl, [(34, 40), (62, 30)], p["skin"], 5)        # 手臂后摆
        ell(cl, 60, 26, 68, 34, p["skin"])
        line(cl, [(34, 44), (58, 38)], p["sh"], 4)          # 远臂
        ell(cl, 30, 34, 44, 50, p["skin"])                  # 肩
        rect(cl, 34, 26, 42, 40, p["skin"])                 # 颈部连接
        ell(cl, 32, 34, 62, 64, p["suit"])                  # 躯干（团身）
        rect(cl, 34, 40, 60, 60, p["suit"])
        ell(cl, 36, 52, 58, 66, p["suitd"])
        line(cl, [(44, 60), (66, 54)], p["skin"], 8)        # 大腿收起
        line(cl, [(66, 54), (56, 70)], p["skin"], 6)        # 小腿
        line(cl, [(50, 70), (60, 74)], p["skin"], 4)        # 脚
        line(cl, [(40, 62), (60, 58)], p["sh"], 6)          # 远腿
        line(cl, [(60, 58), (52, 72)], p["sh"], 5)
        drops = [(20, 84), (30, 88), (48, 86), (66, 82)]
    else:
        hx, hy = 18, 0
        line(cl, [(40, 42), (70, 30)], p["skin"], 6)
        ell(cl, 68, 26, 77, 35, p["skin"])
        line(cl, [(40, 47), (64, 40)], p["sh"], 4)
        ell(cl, 36, 36, 52, 54, p["skin"])
        rect(cl, 36, 26, 44, 42, p["skin"])                 # 颈部连接
        ell(cl, 38, 36, 70, 70, p["suit"])
        rect(cl, 40, 43, 68, 66, p["suit"])
        ell(cl, 42, 56, 66, 72, p["suitd"])
        line(cl, [(50, 66), (74, 59)], p["skin"], 9)
        line(cl, [(74, 59), (63, 77)], p["skin"], 6)
        line(cl, [(57, 77), (67, 82)], p["skin"], 4)
        line(cl, [(46, 68), (68, 63)], p["sh"], 6)
        line(cl, [(68, 63), (59, 79)], p["sh"], 5)
        drops = [(22, 88), (36, 91), (56, 90), (74, 86)]
    head, hi = head_for(char, "side", False)
    pxs(fx, drops, WAT_L)
    return cl, fx, head, hi, (hx, hy)

# ---- 姿态 3：UW_SWIM 水下水平游泳 ----
def pose_uwswim(char):
    w, h = (128, 56) if char == "yy" else (128, 64)
    cl = canvas(w, h)
    fx = canvas(w, h)
    p = pal_for(char, True)
    hx, hy = (12, 8) if char == "yy" else (12, 10)
    head, hi = head_for(char, "side", True, goggles_down=(char == "yy"))
    if char == "yy":
        line(cl, [(34, 30), (10, 23)], p["skin"], 5)        # 双臂前伸并拢
        ell(cl, 4, 19, 12, 26, p["skin"])
        line(cl, [(34, 33), (12, 27)], p["sh"], 4)
        ell(cl, 28, 25, 42, 39, p["skin"])                  # 肩
        rect(cl, 32, 25, 62, 37, p["suit"])                 # 躯干
        ell(cl, 30, 24, 66, 38, p["suit"])
        line(cl, [(34, 36), (60, 36)], p["suitd"], 1)
        line(cl, [(60, 29), (90, 30)], p["skin"], 6)        # 并拢打腿
        line(cl, [(90, 30), (112, 27)], p["skin"], 5)
        line(cl, [(112, 25), (120, 27)], p["skin"], 3)      # 绷脚
        line(cl, [(60, 33), (90, 34)], p["sh"], 5)
        line(cl, [(90, 34), (110, 32)], p["sh"], 4)
        bubbles = [(46, 12, 2), (54, 7, 1), (62, 3, 1), (52, 16, 1)]
    else:
        line(cl, [(40, 34), (10, 26)], p["skin"], 6)
        ell(cl, 4, 21, 13, 30, p["skin"])
        line(cl, [(40, 38), (14, 31)], p["sh"], 4)
        ell(cl, 34, 29, 50, 45, p["skin"])
        rect(cl, 38, 29, 72, 43, p["suit"])
        ell(cl, 36, 28, 76, 44, p["suit"])
        line(cl, [(40, 42), (70, 42)], p["suitd"], 1)
        line(cl, [(70, 33), (102, 34)], p["skin"], 7)
        line(cl, [(102, 34), (122, 31)], p["skin"], 5)
        line(cl, [(122, 29), (126, 31)], p["skin"], 3)
        line(cl, [(70, 38), (100, 39)], p["sh"], 5)
        line(cl, [(100, 39), (118, 37)], p["sh"], 4)
        bubbles = [(54, 14, 2), (63, 8, 1), (71, 4, 1), (60, 19, 1)]
    for bx, by, br in bubbles:
        D(fx).ellipse([bx - br, by - br, bx + br, by + br], outline=BUBBLE, width=1)
    return cl, fx, head, hi, (hx, hy)

# ---- 姿态 4：ATTACK 水下普通攻击（前冲拳）----
def pose_attack(char):
    w, h = (112, 72) if char == "yy" else (128, 80)
    cl = canvas(w, h)
    fx = canvas(w, h)
    p = pal_for(char, True)
    hx, hy = (18, 8) if char == "yy" else (20, 8)
    head, hi = head_for(char, "side", True, goggles_down=(char == "yy"))
    if char == "yy":
        line(cl, [(36, 32), (14, 30)], p["skin"], 5)        # 冲拳臂
        ell(cl, 4, 25, 14, 35, p["skin"])                   # 拳
        pxs(cl, [(6, 27), (10, 27)], p["sh"])
        line(cl, [(38, 38), (50, 46)], p["skin"], 5)        # 后臂收回
        ell(cl, 48, 43, 56, 51, p["skin"])
        ell(cl, 32, 30, 46, 44, p["skin"])                  # 肩
        rect(cl, 36, 29, 66, 45, p["suit"])
        ell(cl, 34, 28, 70, 46, p["suit"])
        line(cl, [(62, 40), (88, 48)], p["skin"], 6)        # 后腿后蹬
        line(cl, [(88, 48), (100, 43)], p["skin"], 5)
        line(cl, [(48, 44), (60, 56)], p["skin"], 6)        # 前腿屈膝
        line(cl, [(60, 56), (50, 64)], p["skin"], 5)
        line(cl, [(46, 62), (54, 66)], p["skin"], 3)
        line(cl, [(64, 36), (88, 42)], p["sh"], 5)          # 远腿
        speed = [(16, 22, 24, 22), (18, 40, 26, 40), (20, 18, 26, 18)]
        bubbles = [(56, 14, 1), (64, 9, 1), (48, 19, 1)]
    else:
        line(cl, [(42, 36), (14, 34)], p["skin"], 6)
        ell(cl, 4, 28, 16, 40, p["skin"])
        pxs(cl, [(7, 31), (11, 31)], p["sh"])
        line(cl, [(44, 43), (58, 52)], p["skin"], 5)
        ell(cl, 56, 49, 65, 58, p["skin"])
        ell(cl, 38, 34, 54, 50, p["skin"])
        rect(cl, 42, 33, 76, 51, p["suit"])
        ell(cl, 40, 32, 80, 52, p["suit"])
        line(cl, [(72, 45), (100, 54)], p["skin"], 7)
        line(cl, [(100, 54), (114, 48)], p["skin"], 5)
        line(cl, [(56, 50), (69, 64)], p["skin"], 6)
        line(cl, [(69, 64), (58, 73)], p["skin"], 5)
        line(cl, [(54, 71), (63, 75)], p["skin"], 3)
        line(cl, [(74, 40), (100, 47)], p["sh"], 5)
        speed = [(18, 25, 27, 25), (20, 46, 29, 46), (22, 20, 29, 20)]
        bubbles = [(64, 15, 1), (73, 10, 1), (56, 21, 1)]
    for x0, y0, x1, y1 in speed:
        line(fx, [(x0, y0), (x1, y1)], BUBBLE, 1)
    for bx, by, br in bubbles:
        D(fx).ellipse([bx - br, by - br, bx + br, by + br], outline=BUBBLE, width=1)
    return cl, fx, head, hi, (hx, hy)

# ---- 姿态 5：HIT 受击（水下，后仰）----
def pose_hit(char):
    w = h = 96
    cl = canvas(w, h)
    fx = canvas(w, h)
    p = pal_for(char, True)
    hx, hy = (40, 2) if char == "yy" else (42, 0)
    head, hi = head_for(char, "side", True, hit=True, goggles_down=(char == "yy"))
    if char == "yy":
        line(cl, [(46, 38), (64, 22)], p["skin"], 5)        # 手臂后甩
        ell(cl, 62, 18, 70, 26, p["skin"])
        line(cl, [(44, 44), (22, 54)], p["skin"], 5)        # 前臂下挥
        ell(cl, 16, 51, 24, 59, p["skin"])
        ell(cl, 40, 34, 54, 50, p["skin"])
        rect(cl, 46, 26, 54, 40, p["skin"])                 # 颈部连接
        ell(cl, 38, 36, 64, 66, p["suit"])                  # 躯干后仰
        rect(cl, 40, 42, 62, 62, p["suit"])
        line(cl, [(46, 64), (56, 80)], p["skin"], 6)        # 腿拖尾
        line(cl, [(56, 80), (48, 90)], p["skin"], 5)
        line(cl, [(44, 88), (52, 92)], p["skin"], 3)
        line(cl, [(50, 66), (62, 80)], p["sh"], 5)
        line(cl, [(62, 80), (56, 89)], p["sh"], 4)
        stars = [(24, 8, 31, 14), (28, 4, 33, 10), (20, 14, 27, 18)]
        bubbles = [(70, 40, 1), (76, 34, 1)]
    else:
        line(cl, [(52, 42), (72, 24)], p["skin"], 6)
        ell(cl, 70, 19, 79, 28, p["skin"])
        line(cl, [(50, 49), (24, 60)], p["skin"], 5)
        ell(cl, 17, 57, 26, 66, p["skin"])
        ell(cl, 46, 38, 62, 56, p["skin"])
        rect(cl, 50, 26, 58, 44, p["skin"])                 # 颈部连接
        ell(cl, 44, 40, 72, 74, p["suit"])
        rect(cl, 46, 47, 70, 70, p["suit"])
        line(cl, [(52, 72), (62, 88)], p["skin"], 6)
        line(cl, [(62, 88), (54, 95)], p["skin"], 5)
        line(cl, [(56, 74), (70, 87)], p["sh"], 5)
        line(cl, [(70, 87), (64, 95)], p["sh"], 4)
        stars = [(26, 8, 34, 15), (31, 4, 37, 11), (21, 15, 29, 20)]
        bubbles = [(78, 44, 1), (84, 38, 1)]
    for x0, y0, x1, y1 in stars:
        line(fx, [(x0, y0), (x1, y1)], WAT_L, 1)
    for bx, by, br in bubbles:
        D(fx).ellipse([bx - br, by - br, bx + br, by + br], outline=BUBBLE, width=1)
    return cl, fx, head, hi, (hx, hy)

# ---- 姿态 6：BREATH 出水换气（正面，张口）----
def pose_breath(char):
    w = h = 96
    cl = canvas(w, h)
    fx = canvas(w, h)
    p = pal_for(char, False)
    hx, hy = (34, 2) if char == "yy" else (33, 0)
    head, hi = head_for(char, "front", False, gasp=True)
    if char == "yy":
        rect(cl, 42, 27, 50, 38, p["skin"])                 # 颈
        ell(cl, 26, 36, 66, 50, p["skin"])                  # 肩
        rect(cl, 30, 42, 62, 66, p["suit"])                 # 胸/躯干入水
        ell(cl, 28, 40, 64, 56, p["suit"])
        line(cl, [(28, 42), (14, 52)], p["skin"], 5)        # 双臂拨水
        ell(cl, 9, 49, 17, 57, p["skin"])
        line(cl, [(64, 42), (78, 52)], p["skin"], 5)
        ell(cl, 75, 49, 83, 57, p["skin"])
        wl = 58
        drops = [(20, 46), (76, 46), (26, 40), (68, 40), (12, 55), (84, 55), (22, 52), (74, 52)]
    else:
        rect(cl, 43, 27, 53, 42, p["skin"])
        ell(cl, 24, 38, 72, 54, p["skin"])
        rect(cl, 28, 46, 68, 72, p["suit"])
        ell(cl, 26, 44, 70, 62, p["suit"])
        line(cl, [(26, 46), (10, 56)], p["skin"], 6)
        ell(cl, 4, 52, 13, 61, p["skin"])
        line(cl, [(70, 46), (86, 56)], p["skin"], 6)
        ell(cl, 83, 52, 92, 61, p["skin"])
        wl = 62
        drops = [(18, 50), (80, 50), (24, 44), (74, 44), (8, 60), (88, 60), (20, 57), (78, 57)]
    # 水面与溅圈
    rect(fx, 0, wl, w - 1, wl + 7, WAT)
    line(fx, [(0, wl), (w - 1, wl)], WAT_L, 1)
    D(fx).ellipse([hx - 14, wl - 4, hx + 42, wl + 5], outline=WAT_L, width=1)
    D(fx).ellipse([hx - 20, wl - 2, hx + 48, wl + 7], outline=WAT_D, width=1)
    pxs(fx, drops, WHT)
    return cl, fx, head, hi, (hx, hy)

POSES = {
    "SURF_SWIM": pose_surf,
    "JUMP": pose_jump,
    "UW_SWIM": pose_uwswim,
    "ATTACK": pose_attack,
    "HIT": pose_hit,
    "BREATH": pose_breath,
}
UW_POSES = {"UW_SWIM", "ATTACK", "HIT"}
LR_POSES = {"SURF_SWIM", "UW_SWIM", "ATTACK"}


# ---------------------------------------------------------------- 组装
def build(char, pose, direction):
    cl, fx, head, hi, (hx, hy) = POSES[pose](char)
    hb = opaque_bbox(head)
    head_size = (hb[2] - hb[0], hb[3] - hb[1])
    cell = canvas(*cl.size)
    char_layer = canvas(*cl.size)
    paste(char_layer, cl, 0, 0)
    paste(char_layer, head, hx, hy)
    outline(char_layer, uw(OUT) if pose in UW_POSES else OUT)
    paste(cell, char_layer, 0, 0)
    paste(cell, fx, 0, 0)
    W = cell.size[0]
    d = D(cell)
    if direction == "L":
        for e in hi:
            d.point((hx + e["cx"] + e["ox"], hy + e["cy"] + e["oy"]), fill=WHT)
    else:
        cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
        d = D(cell)
        for e in hi:
            old_x = W - 1 - (hx + e["cx"] + e["ox"])
            old_y = hy + e["cy"] + e["oy"]
            d.point((old_x, old_y), fill=e["base"])       # 擦除镜像到错侧的旧高光
            struct_new_left = W - (hx + e["cx"]) - e["sw"]
            d.point((struct_new_left + e["ox"], old_y), fill=WHT)
    return cell, dict(head_w=head_size[0], head_h=head_size[1],
                      cell=[cell.size[0], cell.size[1]],
                      headCell=[hx + hb[0], hy + hb[1], hx + hb[2], hy + hb[3]])

# ---------------------------------------------------------------- 图纸工具
def zoom(img, k):
    return img.resize((img.size[0] * k, img.size[1] * k), Image.NEAREST)

def on_color(w, h, c=(158, 166, 178, 255)):
    return Image.new("RGBA", (w, h), c)

LABEL = (25, 30, 45, 255)
SUBLABEL = (52, 62, 82, 255)
ACCENT = (168, 88, 16, 255)

# ---------------------------------------------------------------- 场景小样
def scene_mockup(sprites):
    """512×448 静态观感小样：256×224 逻辑构图 ×2 最近邻。"""
    LW, LH = 256, 224
    g = canvas(LW, LH)
    SKY = (122, 190, 244, 255); SKY_D = (96, 164, 232, 255)
    MT = (96, 96, 176, 255); MT_SNOW = (238, 244, 252, 255)
    BLD = (70, 84, 128, 255); BLD_D = (52, 62, 100, 255); WIN = (190, 214, 240, 255)
    DECK = (226, 230, 236, 255); DECK_D = (176, 184, 196, 255)
    UW1 = (52, 148, 180, 255); UW2 = (36, 116, 150, 255); UW3 = (24, 88, 122, 255)
    HUD = (12, 12, 16, 255); HUD_F = (240, 240, 244, 255)
    HP = (238, 84, 84, 255); OXY = (120, 208, 240, 255)

    rect(g, 0, 0, LW - 1, 71, SKY)                 # 天空
    rect(g, 0, 56, LW - 1, 71, SKY_D)
    # 云
    for cx0, cy0 in [(30, 12), (150, 8), (206, 20)]:
        ell(g, cx0, cy0, cx0 + 22, cy0 + 6, HUD_F)
        ell(g, cx0 + 6, cy0 - 3, cx0 + 16, cy0 + 4, HUD_F)
    # 富士山
    D(g).polygon([(150, 68), (196, 26), (242, 68)], fill=MT)
    D(g).polygon([(186, 36), (196, 26), (206, 36), (201, 40), (196, 37), (191, 40)], fill=MT_SNOW)
    # 建筑
    for bx, bw, bh in [(4, 26, 40), (34, 20, 30), (58, 16, 46)]:
        rect(g, bx, 68 - bh, bx + bw, 68, BLD)
        rect(g, bx, 68 - bh, bx + bw, 68 - bh + 2, BLD_D)
        for wy in range(68 - bh + 5, 66, 7):
            for wx in range(bx + 3, bx + bw - 2, 6):
                rect(g, wx, wy, wx + 2, wy + 3, WIN)
    # 池岸
    rect(g, 0, 68, LW - 1, 73, DECK)
    rect(g, 0, 71, LW - 1, 73, DECK_D)
    # 水面带
    rect(g, 0, 74, LW - 1, 101, WAT)
    rect(g, 0, 74, LW - 1, 75, WAT_L)
    for x in range(0, LW, 8):                      # 波光
        rect(g, x + 2, 78, x + 5, 78, WAT_L)
        rect(g, x + 5, 88, x + 7, 88, WAT_D)
        rect(g, x, 96, x + 3, 96, WAT_D)
    # 水下
    rect(g, 0, 102, LW - 1, 167, UW1)
    rect(g, 0, 126, LW - 1, 167, UW2)
    rect(g, 0, 150, LW - 1, 167, UW3)
    rect(g, 0, 102, LW - 1, 103, WAT_D)            # 水层分界
    # 中央泳道绳
    for y in range(74, 168, 4):
        rect(g, 127, y, 128, y + 1, HUD_F if (y // 4) % 2 else (30, 30, 40, 255))
    # HUD
    rect(g, 0, 168, LW - 1, 223, HUD)
    D(g).rectangle([2, 170, LW - 3, 221], outline=HUD_F, width=1)
    text(g, 8, 176, "1P YY", HUD_F)
    text(g, 8, 186, "HP", HUD_F)
    rect(g, 22, 186, 62, 190, HP)
    text(g, 8, 196, "OXY", HUD_F)
    rect(g, 22, 196, 58, 200, OXY)
    text(g, 112, 176, "TIME 3:00", HUD_F)
    text(g, 168, 176, "CPU DAD", HUD_F)
    text(g, 168, 186, "HP", HUD_F)
    rect(g, 184, 186, 224, 190, HP)
    text(g, 168, 196, "OXY", HUD_F)
    rect(g, 184, 196, 220, 200, OXY)
    # 角色：阳阳水面（SURF_SWIM 朝右），爸爸水下（UW_SWIM 朝左）
    yy = sprites[("yy", "SURF_SWIM", "R")]
    dd = sprites[("dd", "UW_SWIM", "L")]
    paste(g, yy, 24, 34)                           # 水面：头出水、躯干贴水线
    paste(g, dd, 104, 106)                         # 水下深层
    # 标注
    text(g, 6, 4, "STATIC MOCKUP / NOT IN-GAME", (20, 30, 60, 255))
    return zoom(g, 2)

# ---------------------------------------------------------------- 审核图
def sheet_char(char, sprites):
    """单角色动作表：每姿态 [1x L | 1x R(若有) | 2x L]"""
    rows = []
    for pose in POSES:
        imgs = [sprites[(char, pose, "L")]]
        if pose in LR_POSES:
            imgs.append(sprites[(char, pose, "R")])
        rows.append((pose, imgs))
    cw = 150 if char == "yy" else 160
    rh = 210
    W = 40 + cw * 3
    H = 30 + rh * len(rows)
    sheet = on_color(W, H)
    text(sheet, 8, 8, ("YY" if char == "yy" else "DAD") + " POSE SHEET", LABEL)
    y = 30
    for pose, imgs in rows:
        text(sheet, 8, y + 4, pose, SUBLABEL)
        paste(sheet, imgs[0], 40, y + 14)                       # 1x L
        x = 40 + cw
        if len(imgs) > 1:
            paste(sheet, imgs[1], x, y + 14)                    # 1x R
        x += cw
        z2 = zoom(imgs[0], 2)
        paste(sheet, z2, x, y + 10)                             # 2x L
        y += rh
    return sheet

def sheet_blind(entries):
    """盲审表：匿名编号、固定可复现顺序；1x 在上、3x 在下竖排，不出现姓名。"""
    # 固定匿名顺序（确定性打乱，答案写入验收记录）
    order = [5, 11, 0, 8, 14, 2, 17, 6, 9, 13, 1, 16, 4, 10, 7, 15, 3, 12]
    cols = 3
    cw, rh = 420, 460
    rows = (len(order) + cols - 1) // cols
    W = 20 + cw * cols
    H = 30 + rh * rows
    sheet = on_color(W, H)
    text(sheet, 8, 8, "BLIND REVIEW 1X/3X", LABEL)
    for i, ei in enumerate(order):
        img = entries[ei]
        cx = 20 + (i % cols) * cw
        cy = 30 + (i // cols) * rh
        text(sheet, cx, cy, "#%02d" % (i + 1), ACCENT)
        paste(sheet, img, cx + 4, cy + 14)                    # 1x
        z3 = zoom(img, 3)
        paste(sheet, z3, cx + 4, cy + 130)                    # 3x
    return sheet, order

def sheet_zoom(sprites, infos):
    """放大验收表：每角色每姿态 3x 全图 + 真实头部区域 8x 裁切。"""
    rows = [(c, p) for c in ("yy", "dd") for p in POSES]
    W = 640
    H = 30 + len(rows) * 310
    sheet = on_color(W, H)
    text(sheet, 8, 8, "ZOOM REVIEW 3X + HEAD 8X", LABEL)
    y = 30
    for c, p in rows:
        img = sprites[(c, p, "L")]
        text(sheet, 8, y + 4, ("YY " if c == "yy" else "DAD ") + p, SUBLABEL)
        z3 = zoom(img, 3)
        paste(sheet, z3, 8, y + 14)
        hb = infos[(c, p, "L")]["headCell"]
        head_crop = img.crop((hb[0], hb[1], hb[2], hb[3]))
        z8 = zoom(head_crop, 8)
        paste(sheet, z8, 400, y + 14)
        y += 310
    return sheet


# ---------------------------------------------------------------- 主流程
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
    manifest = {
        "schemaVersion": 1,
        "stage": "CONCEPT-1A",
        "artifactKind": "concept-style-static-sprites",
        "applied": False,
        "note": "静态美术门；不接入正式游戏HTML",
        "surfacePalette": {k: list(v) for k, v in {
            "OUT": OUT, "SKIN": SKIN, "SKIN_SH": SKIN_SH, "SKIND": SKIND,
            "SKIND_SH": SKIND_SH, "CAP": CAP, "CAP_L": CAP_L, "CAP_D": CAP_D,
            "GOG_F": GOG_F, "GOG_L": GOG_L, "SUIT": SUIT, "SUIT_D": SUIT_D,
            "HAIR": HAIR, "HAIR_L": HAIR_L, "GLS": GLS, "GLS_L": GLS_L,
            "SUITD": SUITD, "SUITD_L": SUITD_L, "WHT": WHT, "INK": INK,
            "BROW": BROW, "MOUTH": MOUTH, "MOUTH_D": MOUTH_D,
            "WAT": WAT, "WAT_L": WAT_L, "WAT_D": WAT_D}.items()},
        "underwaterMapping": {str(list(k)): list(v) for k, v in UW_MAP.items()},
        "designHeight": {"yy": 66, "dd": 78},
        "sprites": [],
        "sheets": [],
        "checks": {},
    }
    sprites = {}
    infos = {}
    for char in ("yy", "dd"):
        for pose in POSES:
            dirs = ("L", "R") if pose in LR_POSES else ("L",)
            for drc in dirs:
                img, info = build(char, pose, drc)
                sprites[(char, pose, drc)] = img
                name = f"{char}_{pose}_{drc}.png"
                save_png(img, SPRITES / name)
                bad = check_alpha(img)
                if bad:
                    raise SystemExit(f"alpha非0/255: {name} {bad}")
                infos[(char, pose, drc)] = info
                manifest["sprites"].append({
                    "file": f"sprites/{name}", "char": char, "pose": pose, "dir": drc,
                    "cell": info["cell"], "head": [info["head_w"], info["head_h"]],
                    "palette": ("underwater" if pose in UW_POSES else "surface"),
                    "sha256": sha256_bytes((SPRITES / name).read_bytes()),
                })
    # 头部尺寸门槛
    head_fail = []
    for s in manifest["sprites"]:
        need = 24 if s["char"] == "yy" else 28
        if s["head"][0] < need - 2 or s["head"][1] < need - 2:
            head_fail.append((s["file"], s["head"]))
    manifest["checks"]["headMinSize"] = {
        "rule": "yy>=约24x24, dd>=约28x28（容差2px）", "fail": head_fail,
        "pass": not head_fail}
    # 单元格门槛
    cell_fail = []
    for s in manifest["sprites"]:
        w, h = s["cell"]
        if s["pose"] in LR_POSES:
            if w not in (112, 128):
                cell_fail.append(s["file"])
        elif (w, h) != (96, 96):
            cell_fail.append(s["file"])
    manifest["checks"]["cellSize"] = {
        "rule": "横向112/128宽；其余96x96", "fail": cell_fail, "pass": not cell_fail}
    manifest["checks"]["alphaBinary"] = {"pass": True, "note": "全部输出逐像素检查alpha∈{0,255}"}
    # HTML 未改动
    html_sha = sha256_bytes(HTML.read_bytes())
    manifest["checks"]["mainHtmlUnchanged"] = {
        "pass": html_sha == EXPECTED_HTML_SHA, "sha256": html_sha}
    if html_sha != EXPECTED_HTML_SHA:
        raise SystemExit("主HTML SHA 变化，立即停止")
    # 审核图
    s_yy = sheet_char("yy", sprites)
    s_dd = sheet_char("dd", sprites)
    save_png(s_yy, HERE / "阳阳静态动作表.png")
    save_png(s_dd, HERE / "爸爸静态动作表.png")
    entries = []
    keys = []
    for char in ("yy", "dd"):
        for pose in POSES:
            for drc in (("L", "R") if pose in LR_POSES else ("L",)):
                entries.append(sprites[(char, pose, drc)])
                keys.append(f"{char}_{pose}_{drc}")
    blind, order = sheet_blind(entries)
    save_png(blind, HERE / "双角色1x盲审表.png")
    zoom_sheet = sheet_zoom(sprites, infos)
    save_png(zoom_sheet, HERE / "双角色放大验收表.png")
    mock = scene_mockup(sprites)
    save_png(mock, HERE / "游戏观感静态小样.png")
    manifest["blindAnswer"] = {"order": order, "keyOfIndex": keys,
                               "note": "#NN 对应 entries[order[NN-1]]"}
    for name, img in [("阳阳静态动作表.png", s_yy), ("爸爸静态动作表.png", s_dd),
                      ("双角色1x盲审表.png", blind), ("双角色放大验收表.png", zoom_sheet),
                      ("游戏观感静态小样.png", mock)]:
        bad = check_alpha(img)
        if bad:
            raise SystemExit(f"alpha非0/255: {name} {bad}")
        manifest["sheets"].append({"file": name, "size": list(img.size),
                                   "sha256": sha256_bytes((HERE / name).read_bytes())})
    save_png(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), SPRITES / ".keep")  # 目录占位
    (SPRITES / ".keep").unlink()
    with open(HERE / "concept_1a_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    print("sprites:", len(manifest["sprites"]))
    print("checks:", json.dumps({k: v.get("pass") for k, v in manifest["checks"].items()}))
    print("blind order:", order)

if __name__ == "__main__":
    main()
