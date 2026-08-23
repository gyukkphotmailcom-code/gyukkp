#!/usr/bin/env python3
# 阶段R3B-I: 在批准的 R3B-M 身份蒙版内, 为 3 个代表姿态绘制阳阳/爸爸身份像素
#
# 输入(全部只读, SHA 钉死, 不符即 fail):
#   ../sprites_r3a_human_baked.js   R3A 批准人体母版(唯一身体底稿)
#   ../build_sprites_r3a.py        R3A 生成器(仅校验未被改动)
#   ../avatar_paint.py             Stage2 身份母版(仅校验存在与哈希; 不把24×24头像贴入动作帧)
#   ../阶段3A-R3A人体母版{清单,验收记录}.md / 审核表.png / 盲审图.png  R3A 文档与审核图(仅校验)
#   ../R3B-M/build_identity_masks_r3bm.py  R3B-M 生成器(仅校验未被改动)
#   ../R3B-M/identity_masks_r3bm.json      批准身份蒙版(唯一可编辑范围来源)
#   ../R3B-M/identity_masks_r3bm_baked.js  R3B-M JS 版(仅校验未被改动)
#   ../R3B-M/masks/ 下 30 张蒙版 PNG       构建时逐像素复核与 JSON 一致
#   ../../../阳阳水泳大乱斗-原版复刻.html   主HTML(非构建输入; 仅范围保护: 构建前记录SHA, 落盘前复核未变化)
#
# 输出(全部写到本目录 R3B-I/, 自检全过后才原子落盘):
#   sprites/<POSE>_<yy|dd>_<L|R>.png   12 张原始尺寸透明 PNG
#   diff/<POSE>_<yy|dd>_<L|R>_mask.png     changed-pixel 二值图
#   diff/<POSE>_<yy|dd>_<L|R>_color.png    彩色差异图(变改像素=新色, 其余压暗)
#   diff/<POSE>_<yy|dd>_<L|R>_outside.png  identityMask 外差异证明图(应无红色)
#   identity_sprites_r3bi.json / identity_sprites_r3bi_baked.js
#   阶段R3B-I身份稿审核表.png / 阶段R3B-I身份稿盲审图.png
# 文档(清单/复现记录/验收记录)由人工(主代理)依据自检输出撰写, 不由本脚本生成。
#
# 硬规则:
#   - 只改色, 不改形: w/h/root/visibleBBox/alpha/不透明像素集合/人物外轮廓与 R3A 完全一致
#   - changedPixels ⊆ R3B-M approvedIdentityMask; 蒙版外字符/调色类别/alpha 差异=0
#   - 子蒙版语义不混用: hairOrCap 只画阳阳泳帽/爸爸头发; eyesOrGlasses 只画眼/泳镜/眼镜;
#     faceDetail 只画少量鼻颧阴影; mouth 只画嘴部
#   - 表面身份色: 阳阳帽蓝 C=#3C9CF0/c=#1E5AA8, 爸爸发棕 H=#38241A/h=#5C4030;
#     蓝只用于阳阳身份区, 棕只用于爸爸身份区; UW 只用 u/m/l/w
#   - L/R 分别逐像素设计、分别烘焙、分别验证; 固定左上光源, 身份区内部非机械镜像
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent          # R3B-I/
OUT = BASE
KIMI_DEV = BASE.parent                           # 过程文件/Kimi开发
PROJECT = KIMI_DEV.parent.parent                 # 项目根
R3BM_DIR = KIMI_DEV / "R3B-M"

R3A_JS = KIMI_DEV / "sprites_r3a_human_baked.js"
R3A_PY = KIMI_DEV / "build_sprites_r3a.py"
FACES_PY = KIMI_DEV / "avatar_paint.py"
R3BM_PY = R3BM_DIR / "build_identity_masks_r3bm.py"
R3BM_JSON = R3BM_DIR / "identity_masks_r3bm.json"
R3BM_JS = R3BM_DIR / "identity_masks_r3bm_baked.js"
MAIN_HTML = PROJECT / "阳阳水泳大乱斗-原版复刻.html"

PINNED = {
    R3A_JS: "bbd40b05f6d7143826f7d554f04deb878a98bf503c09c6fd5bf00c1e612bf7f2",
    R3A_PY: "bffb7e445be037fe5262993393c91e5f33ada7ca5c6eee2a2a629854b075d1be",
    FACES_PY: "615daea6e81acbc60d1e59bf5c83fd4582fd064c35b1d5aa425c1793d7b1194e",
    KIMI_DEV / "阶段3A-R3A人体母版清单.md": "f49af48471782e5edbbcc3f01bc90c90eefcd48fb48edb54fdb15fd509c31152",
    KIMI_DEV / "阶段3A-R3A人体母版验收记录.md": "6c0fe04e5aff1f7aaf6cbd01098f03bfb38cb99bfd4e43f732bee2adeda5e04a",
    KIMI_DEV / "阶段3A-R3A构建复现记录.md": "d480a7207fe28344d1e61ec7d1eba0ea85e3e895ddabad4a1b2c8ec3dfd6cec1",
    KIMI_DEV / "阶段3A-R3A人体母版审核表.png": "1069f4f055f26dcd9a8a3dbee8fe5f71ab7cb889c21ef82d2ece5dba041156e2",
    KIMI_DEV / "阶段3A-R3A人体盲审图.png": "2b3fd17060e925dcb4065baf2158358de827eea197e5cb728d7e581a3d8cf86e",
    R3BM_PY: "deac9f147ae26d43f61ee62a7146d8866a7d30208f802e9e64ea176116a37d6c",
    R3BM_JSON: "00448adfa11cacd37a9b1aa39d94f2772cb6a311e2f86a4a79b852d5699053f1",
    R3BM_JS: "9ffd8aafa8ce77315d42f2f8e5a3fb85ffc3a107c22404bd5ba327a65f91ffaa",
}
# 主HTML不是构建输入, 仅作范围保护: 构建前记录SHA, 正式落盘前复核未变化;
# 不固定任何特定版本SHA, 也不写入任何输出物(仅终端日志), 保证干净Git基线可复现。

# R3A 表面调色板 + 本轮批准的表面身份色(阶段2钉值色)
PAL_SURF = {"O": (0, 0, 0), "D": (60, 32, 24), "d": (120, 64, 49), "s": (180, 96, 73),
            "S": (241, 129, 98), "W": (241, 242, 241),
            "C": (60, 156, 240), "c": (30, 90, 168), "H": (56, 36, 26), "h": (92, 64, 48)}
PAL_UW = {"u": (0, 64, 88), "m": (60, 188, 252), "l": (164, 228, 252), "w": (252, 252, 252)}
PAL_SURF_HEX = {"O": "#000000", "D": "#3C2018", "d": "#784031", "s": "#B46049",
                "S": "#F18162", "W": "#F1F2F1",
                "C": "#3C9CF0", "c": "#1E5AA8", "H": "#38241A", "h": "#5C4030"}
PAL_UW_HEX = {"u": "#004058", "m": "#3CBCFC", "l": "#A4E4FC", "w": "#FCFCFC"}
SURFACE_IDENTITY_HEX = {"C": "#3C9CF0", "c": "#1E5AA8", "H": "#38241A", "h": "#5C4030"}
UW_IDENTITY_MAPPING = {
    "yy": {"泳帽主色": "m", "泳帽高光(左上光源)": "l", "泳帽深部/后缘": "u",
           "泳镜镜片/高光": "l/w", "泳镜框与脑后镜带端": "u/l"},
    "dd": {"头发/发际线": "u(主)+l(顶缘单点反光)", "眼镜框/镜腿": "u", "镜片反光": "l/w"},
}

SUBKINDS = ("hairOrCapMask", "eyesOrGlassesMask", "faceDetailMask", "mouthMask")
POSES = ("SURF0", "JUMP_AIR", "UW_NORMAL")
DIRS = ("L", "R")
PERSONS = ("yy", "dd")
UW_POSES = ("UW_NORMAL",)

# 与 R3B-M POSE_RULES 相同的复核常量(仅用于复检, 不重新生成蒙版)
POSE_CHECK = {
    "SURF0": {"headWin": (0, 0, 20, 9), "neckY": 10, "clusterGap": 3,
              "forbidRects": [(20, 9, 30, 12), (0, 10, 30, 20), (21, 0, 30, 8)]},
    "JUMP_AIR": {"headWin": (11, 0, 33, 11), "neckY": 12, "clusterGap": 3,
                 "forbidRects": [(34, 0, 54, 12), (0, 13, 10, 26), (0, 12, 54, 41)]},
    "UW_NORMAL": {"headWin": (12, 1, 25, 10), "neckY": 11, "clusterGap": 4,
                  "forbidRects": [(26, 5, 38, 12), (0, 8, 11, 19), (0, 11, 38, 20)]},
}

# 子蒙版语义允许字符(表面姿态): 身份色只能进入本人语义区
ALLOWED_SURF = {
    "yy": {"hairOrCapMask": set("Cc"), "eyesOrGlassesMask": set("OWCc"),
           "faceDetailMask": set("ODdsSW"), "mouthMask": set("ODdsSW")},
    "dd": {"hairOrCapMask": set("Hh"), "eyesOrGlassesMask": set("OWHh"),
           "faceDetailMask": set("ODdsSW"), "mouthMask": set("ODdsSW")},
}
ALLOWED_UW = {p: {k: set("umlw") for k in SUBKINDS} for p in PERSONS}


def R(x0, s):
    """从 x0 起连续涂 s 中各字符。"""
    return {x0 + i: ch for i, ch in enumerate(s)}


def seg(*parts):
    out = {}
    for p in parts:
        out.update(p)
    return out


# ---------- 逐像素身份绘制表: PAINT[(pose, person, dir)][y] = {x: 字符} ----------
# 固定左上光源; 脸朝向: SURF0/L 朝左、SURF0/R 朝右; UW_NORMAL/L 朝右、UW_NORMAL/R 朝左;
# JUMP_AIR 为正面微侧(主目镜区 L 在 x17-21、R 在 x33-37, 副眼点 L x30 / R x24)。
PAINT = {
    # ===== SURF0 水面俯泳 =====
    ("SURF0", "yy", "L"): {
        1: seg(R(3, "CCCCCCCCCCCC"), R(15, "ccc")),          # 泳帽: 主蓝C, 右下背光c
        2: seg(R(3, "CCCCCCCCCCC"), R(14, "cccc")),
        3: seg(R(1, "CCC"), R(4, "ccccccccccccccc")),        # 帽檐下缘暗带
        6: R(13, "SS"),                                       # 颧部受光
        7: R(13, "OOO"),                                      # 泳镜上框
        8: {11: "O", 12: "c", 15: "O"},                       # 镜框+朝前瞳孔(x13-14留W镜片)
        9: {8: "d", 11: "O", 12: "c", 15: "O"},               # 简洁小嘴
    },
    ("SURF0", "yy", "R"): {
        1: seg(R(13, "CCCCCCCCCCCC"), R(25, "ccc")),
        2: seg(R(13, "CCCCCCCCCCC"), R(24, "cccc")),
        3: seg(R(12, "CCC"), R(15, "ccccccccccccccc")),
        6: R(16, "SS"),
        7: R(15, "OOO"),
        8: {15: "O", 18: "c", 19: "O"},                       # 朝右瞳孔x18
        9: {15: "O", 18: "c", 19: "O", 22: "d"},
    },
    ("SURF0", "dd", "L"): {
        1: seg(R(3, "hhh"), R(6, "HHHHHHHHHHHH")),            # 棕发: 左上受光h, 主色H
        2: seg(R(3, "hh"), R(5, "HHHHHHHHHHHHH")),
        3: seg(R(1, "HH"), R(5, "HHHHHHHHHHHHHH")),           # x3-4保留肤色=前额发际线
        7: seg({12: "d"}, R(13, "HHH")),                      # 鼻梁影+眼镜上框
        8: {7: "d", 11: "H", 12: "O", 15: "H"},               # 微笑嘴角+棕框+朝前瞳孔
        9: {8: "d", 11: "H", 12: "O", 15: "H"},
    },
    ("SURF0", "dd", "R"): {
        1: seg(R(13, "hhh"), R(16, "HHHHHHHHHHHH")),
        2: seg(R(13, "hh"), R(15, "HHHHHHHHHHHHH")),
        3: seg(R(12, "HHHHHHHHHHHHHH"), R(28, "HH")),         # x26-27保留肤色=发际线
        7: seg(R(15, "HHH"), {18: "d"}),
        8: {15: "H", 18: "O", 19: "H", 23: "d"},              # 朝右瞳孔x18
        9: {15: "H", 18: "O", 19: "H", 22: "d"},
    },
    # ===== JUMP_AIR 空中飞扑 =====
    ("JUMP_AIR", "yy", "L"): {
        1: seg(R(14, "CCCCCCCCCCCCCCCC"), R(30, "ccc")),
        2: seg(R(12, "CCCCCCCCCCCCCCCCCC"), R(30, "cccc")),
        3: seg(R(12, "CCCCCCCCCCCCCCCCC"), R(29, "ccccc")),
        4: seg(R(12, "CCCCCCCCC"), R(21, "ccccccccccccc")),   # 帽下缘暗带
        7: R(17, "OOO"),                                      # 主泳镜上框
        8: {17: "O", 19: "O"},                                # x18留W镜片高光
        9: {17: "O", 18: "c", 21: "O", 30: "O"},              # 瞳孔朝左x18; 副眼点框x30
        10: {17: "O", 18: "c", 21: "O", 30: "O"},
        11: seg(R(17, "OOOOO"), {25: "d", 26: "d", 30: "O"}),  # 镜下框+简洁小嘴
    },
    ("JUMP_AIR", "yy", "R"): {
        1: seg(R(22, "CCCCCCCCCCCCCCCC"), R(38, "ccc")),
        2: seg(R(21, "CCCCCCCCCCCCCCCCCC"), R(39, "cccc")),
        3: seg(R(21, "CCCCCCCCCCCCCCCCC"), R(38, "ccccc")),
        4: seg(R(21, "CCCCCCCCC"), R(30, "ccccccccccccc")),
        7: R(35, "OOO"),
        8: {35: "O", 37: "O"},
        9: {24: "O", 33: "O", 36: "c", 37: "O"},              # 副眼点框x24; 瞳孔朝右x36
        10: {24: "O", 33: "O", 36: "c", 37: "O"},
        11: seg({24: "O", 28: "d", 29: "d"}, R(33, "OOOOO")),
    },
    ("JUMP_AIR", "dd", "L"): {
        1: seg(R(14, "hhhhhhh"), R(21, "HHHHHHHHHHHH")),
        2: seg(R(12, "hhh"), R(15, "HHHHHHHHHHHHHHHHHHH")),
        3: seg(R(12, "hh"), R(14, "HHHHHHHHHHHHHHHHHHHH")),
        4: seg(R(12, "HHHHHHHHH"), R(28, "HHHHHH")),          # x21-27保留肤色=高额发际线
        7: R(17, "HHH"),                                      # 棕眼镜上框
        8: {17: "H", 19: "H"},
        9: {17: "H", 18: "O", 21: "H", 24: "d", 30: "H"},     # 瞳孔朝左; 鼻梁影
        10: {17: "H", 18: "O", 21: "H", 24: "d", 30: "H"},    # 微笑嘴角上提
        11: seg(R(17, "HHHHH"), {25: "d", 26: "d", 27: "d", 30: "H"}),  # 镜下框+稳重嘴
    },
    ("JUMP_AIR", "dd", "R"): {
        1: seg(R(22, "hhhhh"), R(27, "HHHHHHHHHHHHHH")),
        2: seg(R(21, "hhh"), R(24, "HHHHHHHHHHHHHHHHHHH")),
        3: seg(R(21, "hh"), R(23, "HHHHHHHHHHHHHHHHHHHH")),
        4: seg(R(21, "HHHHHH"), R(34, "HHHHHHHHH")),          # x27-33保留肤色=发际线
        7: R(35, "HHH"),
        8: {35: "H", 37: "H"},
        9: {24: "H", 30: "d", 33: "H", 36: "O", 37: "H"},
        10: {24: "H", 30: "d", 33: "H", 36: "O", 37: "H"},
        11: seg({24: "H", 27: "d", 28: "d", 29: "d"}, R(33, "HHHHH")),
    },
    # ===== UW_NORMAL 水下横泳(只用 u/m/l/w) =====
    ("UW_NORMAL", "yy", "L"): {
        2: {16: "l", 17: "l", 18: "m", 19: "m"},              # 泳帽: m主色, l顶光, u后缘
        3: {13: "u", 14: "l", 15: "m", 16: "m", 17: "m", 18: "m", 19: "u"},
        7: {23: "l"},                                         # 泳镜上沿反光(x24留w)
        8: {13: "l", 21: "u", 22: "l", 24: "l"},              # 脑后镜带端x13; 镜框u+镜片l(x23留w)
        9: {13: "l", 21: "u", 22: "l", 23: "l", 24: "u"},
        10: {21: "m", 22: "m", 23: "m"},                      # 简洁嘴线
    },
    ("UW_NORMAL", "yy", "R"): {
        2: {19: "l", 20: "l", 21: "m", 22: "m"},
        3: {19: "u", 20: "l", 21: "m", 22: "m", 23: "m", 24: "m", 25: "u"},
        7: {15: "l"},
        8: {14: "l", 16: "l", 17: "u", 25: "l"},              # 脑后镜带端x25
        9: {14: "u", 15: "l", 16: "l", 17: "u", 25: "l"},
        10: {15: "m", 16: "m", 17: "m"},
    },
    ("UW_NORMAL", "dd", "L"): {
        2: {16: "l", 17: "u", 18: "u", 19: "u"},              # 头发: u主色, 顶缘单点反光l
        3: R(13, "uuuuuuu"),
        7: {23: "l"},                                         # 镜片上沿反光(x24留w)
        8: {13: "u", 17: "u", 21: "u", 22: "l", 23: "u", 24: "u"},  # 镜腿端x13; 鼻梁影; 棕镜框=u
        9: {13: "u", 17: "u", 21: "u", 22: "u", 24: "u"},     # x23留w镜片反光
        10: {21: "u"},                                        # 稳重嘴角
    },
    ("UW_NORMAL", "dd", "R"): {
        2: {19: "l", 20: "u", 21: "u", 22: "u"},
        3: R(19, "uuuuuuu"),
        7: {15: "l"},
        8: {14: "u", 15: "u", 16: "l", 17: "u", 21: "u", 25: "u"},  # 镜腿端x25
        9: {14: "u", 15: "u", 17: "u", 21: "u", 25: "u"},     # x16留w镜片反光
        10: {17: "u"},
    },
}

# 盲审固定匿名顺序(确定性, 不随机; 答案只写入验收记录)
BLIND_ORDER = [
    ("JUMP_AIR", "dd", "R"), ("SURF0", "yy", "L"), ("UW_NORMAL", "dd", "L"),
    ("JUMP_AIR", "yy", "L"), ("SURF0", "dd", "R"), ("UW_NORMAL", "yy", "R"),
    ("JUMP_AIR", "yy", "R"), ("SURF0", "dd", "L"), ("UW_NORMAL", "dd", "R"),
    ("SURF0", "yy", "R"), ("JUMP_AIR", "dd", "L"), ("UW_NORMAL", "yy", "L"),
]

IDENTITY_NOTE = {
    ("SURF0", "yy"): "蓝色泳帽(C主/c右下背光)+黑框泳镜(c瞳孔朝向前方,W镜片)+简洁小嘴",
    ("SURF0", "dd"): "棕发(H主/h左上受光, 前额保留肤色发际线)+棕框眼镜(O瞳孔朝前,W镜片)+微笑嘴角",
    ("JUMP_AIR", "yy"): "蓝色泳帽(C主/c右下背光)+黑框大泳镜(c瞳孔,W镜片高光)+副眼点镜框+简洁小嘴",
    ("JUMP_AIR", "dd"): "棕发(H主/h左上受光, 前额高发际线保留肤色)+棕框眼镜(O瞳孔,W镜片)+微笑稳重嘴",
    ("UW_NORMAL", "yy"): "水下泳帽m主色+l左上高光+u后缘深部; 泳镜u框+l镜片+w高光+脑后镜带端; 简洁m嘴线",
    ("UW_NORMAL", "dd"): "水下头发u主色+顶缘l单点反光; 眼镜u框/镜腿+l/w镜片反光; 稳重u嘴角",
}


def fail(msg):
    raise SystemExit(f"R3B-I FAIL: {msg}")


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_masters():
    src = R3A_JS.read_text(encoding="utf-8")
    m = re.search(r"=\s*(\{.*\});?\s*$", src, re.S)
    if not m:
        fail("sprites_r3a_human_baked.js 解析失败")
    return json.loads(m.group(1))


def rows_points(rows):
    return {(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != "."}


def inner_points(opaque, w, h):
    out = set()
    for (x, y) in opaque:
        ok = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or (nx, ny) not in opaque:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            out.add((x, y))
    return out


def dilate(points, r):
    out = set()
    for (x, y) in points:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                out.add((x + dx, y + dy))
    return out


def semantic_cluster_count(points, gap):
    if not points:
        return 0
    pts = set(points)
    clusters = 0
    while pts:
        clusters += 1
        region = dilate({pts.pop()}, gap)
        grown = True
        while grown:
            grown = False
            hit = {p for p in pts if p in region}
            if hit:
                pts -= hit
                region |= dilate(hit, gap)
                grown = True
    return clusters


def rect_points(rect):
    x0, y0, x1, y1 = rect
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


def mirror_set(points, w):
    return {(w - 1 - x, y) for (x, y) in points}


def pal_of(pose):
    return PAL_UW if pose in UW_POSES else PAL_SURF


def hex_of(pose):
    return PAL_UW_HEX if pose in UW_POSES else PAL_SURF_HEX


def load_masks():
    """读取批准的 R3B-M 蒙版 JSON, 并与 masks/ 下 30 张 PNG 逐像素复核一致。"""
    mdoc = json.loads(R3BM_JSON.read_text(encoding="utf-8"))
    if mdoc["meta"]["stage"] != "R3B-M" or mdoc["meta"]["applied"] is not False:
        fail("R3B-M JSON meta 不符(应为 stage=R3B-M 且 applied=false 的蒙版提案)")
    masks = {}
    for pose in POSES:
        for d in DIRS:
            mk = mdoc["masks"][pose][d]
            subs = {k: {(int(x), int(y)) for x, y in mk["submasks"][k]} for k in SUBKINDS}
            total = {(int(x), int(y)) for x, y in mk["identityMask"]}
            masks[(pose, d)] = {"subs": subs, "total": total}
            # 与总蒙版 PNG 复核
            p = R3BM_DIR / "masks" / f"{pose}_{d}.png"
            if not p.exists():
                fail(f"缺蒙版PNG {p.name}")
                # unreachable
            img = Image.open(p)
            if img.mode != "L" or img.size != (mk["w"], mk["h"]):
                fail(f"{p.name} 模式/尺寸不符: {img.mode} {img.size}")
            png_pts = {(x, y) for y in range(img.size[1]) for x in range(img.size[0])
                       if img.getpixel((x, y)) != 0}
            vals = {img.getpixel((x, y)) for y in range(img.size[1]) for x in range(img.size[0])}
            if not vals <= {0, 255}:
                fail(f"{p.name} 非二值")
            if png_pts != total:
                fail(f"{p.name} 与 R3B-M JSON 总蒙版不一致")
            for k in SUBKINDS:
                sp = R3BM_DIR / "masks" / "sub" / f"{pose}_{d}_{k}.png"
                if not sp.exists():
                    fail(f"缺子蒙版PNG {sp.name}")
                simg = Image.open(sp)
                if simg.mode != "L" or simg.size != (mk["w"], mk["h"]):
                    fail(f"{sp.name} 模式/尺寸不符")
                spts = {(x, y) for y in range(simg.size[1]) for x in range(simg.size[0])
                        if simg.getpixel((x, y)) != 0}
                svals = {simg.getpixel((x, y)) for y in range(simg.size[1])
                         for x in range(simg.size[0])}
                if not svals <= {0, 255}:
                    fail(f"{sp.name} 非二值")
                if spts != subs[k]:
                    fail(f"{sp.name} 与 R3B-M JSON 子蒙版 {k} 不一致")
    return masks


def verify_masks_vs_master(data, masks):
    """复检 R3B-M 关键不变量(子区互斥/并集=总蒙版/⊆inner/禁区=0/颈肩=0/单簇/LR镜像)。"""
    for pose in POSES:
        pv = data["poses"][pose]
        w, h = pv["w"], pv["h"]
        spec = POSE_CHECK[pose]
        for d in DIRS:
            rows = pv["masterRowsByDir"][d]
            opaque = rows_points(rows)
            inner = inner_points(opaque, w, h)
            subs = masks[(pose, d)]["subs"]
            total = masks[(pose, d)]["total"]
            seen = set()
            for k in SUBKINDS:
                if seen & subs[k]:
                    fail(f"{pose}/{d} 批准蒙版子区重叠 {k}")
                seen |= subs[k]
            if seen != total:
                fail(f"{pose}/{d} 批准蒙版子区并集!=总蒙版")
            if not total <= opaque or not total <= inner:
                fail(f"{pose}/{d} 批准蒙版越出人体内部")
            for rect in spec["forbidRects"]:
                fr = rect_points(rect)
                if d == "R":
                    fr = mirror_set(fr, w)
                if total & fr:
                    fail(f"{pose}/{d} 批准蒙版侵入禁区 {rect}")
            if {p for p in total if p[1] >= spec["neckY"]}:
                fail(f"{pose}/{d} 批准蒙版侵入颈肩接口")
            if semantic_cluster_count(total, spec["clusterGap"]) != 1:
                fail(f"{pose}/{d} 批准蒙版语义簇!=1")
        ml = masks[(pose, "L")]["total"]
        mr = masks[(pose, "R")]["total"]
        if mirror_set(ml, w) != mr:
            fail(f"{pose} 批准蒙版 L/R 非严格镜像(与 R3B-M 记录不符)")


def apply_paint(pose, person, d, master_rows, masks):
    """在蒙版内逐像素换色; 返回 (new_rows, changed:set, sub_changed:dict)。"""
    pv_rows = master_rows
    w, h = len(pv_rows[0]), len(pv_rows)
    mk = masks[(pose, d)]
    total = mk["total"]
    sub_of = {}
    for k in SUBKINDS:
        for p in mk["subs"][k]:
            sub_of[p] = k
    allowed = ALLOWED_UW[person] if pose in UW_POSES else ALLOWED_SURF[person]
    table = PAINT.get((pose, person, d))
    if table is None:
        fail(f"缺绘制表 {pose}/{person}/{d}")
    new_rows = list(pv_rows)
    for y, cols in table.items():
        if not (0 <= y < h):
            fail(f"{pose}/{person}/{d} 绘制行越界 y={y}")
        for x, ch in cols.items():
            if not (0 <= x < w):
                fail(f"{pose}/{person}/{d} 绘制列越界 x={x}")
            if (x, y) not in total:
                fail(f"{pose}/{person}/{d} 在批准蒙版外绘制 ({x},{y})")
            k = sub_of[(x, y)]
            if ch not in allowed[k]:
                fail(f"{pose}/{person}/{d} 子蒙版语义越权: ({x},{y})∈{k} 禁止字符 '{ch}'")
            if ch not in pal_of(pose):
                fail(f"{pose}/{person}/{d} 字符 '{ch}' 不在该姿态调色板")
            r = new_rows[y]
            if r[x] == ".":
                fail(f"{pose}/{person}/{d} 试图改透明像素 ({x},{y})")
            new_rows[y] = r[:x] + ch + r[x + 1:]
    changed = {(x, y) for y in range(h) for x in range(w)
               if new_rows[y][x] != pv_rows[y][x]}
    sub_changed = {k: len(changed & mk["subs"][k]) for k in SUBKINDS}
    return new_rows, changed, sub_changed


def visible_bbox(rows):
    pts = rows_points(rows)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def sprite_png_bytes(rows, pal):
    w, h = len(rows[0]), len(rows)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                px[x, y] = pal[ch] + (255,)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def checker_bg(w, h, cell=4):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (58, 58, 68) if (x // cell + y // cell) % 2 == 0 else (42, 42, 52)
    return img


def over_checker(rows, pal, scale=1):
    w, h = len(rows[0]), len(rows)
    bg = checker_bg(w, h)
    px = bg.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                px[x, y] = pal[ch]
    if scale > 1:
        bg = bg.resize((w * scale, h * scale), Image.NEAREST)
    return bg


def mask_overlay_img(rows, pal, total, scale=1):
    w, h = len(rows[0]), len(rows)
    bg = checker_bg(w, h)
    px = bg.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                px[x, y] = (252, 60, 200) if (x, y) in total else pal[ch]
    if scale > 1:
        bg = bg.resize((w * scale, h * scale), Image.NEAREST)
    return bg


def changed_binary_png_bytes(w, h, changed):
    img = Image.new("L", (w, h), 0)
    px = img.load()
    for (x, y) in changed:
        px[x, y] = 255
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def color_diff_img(master_rows, new_rows, pal, scale=1):
    """彩色差异图: 变化像素=新色原色, 未变不透明像素压暗, 透明=深色底。"""
    w, h = len(master_rows[0]), len(master_rows)
    img = Image.new("RGB", (w, h), (16, 16, 20))
    px = img.load()
    for y in range(h):
        for x in range(w):
            a, b = master_rows[y][x], new_rows[y][x]
            if a == ".":
                continue
            if a != b:
                px[x, y] = pal[b]
            else:
                c = pal[a]
                px[x, y] = (c[0] // 3, c[1] // 3, c[2] // 3)
    if scale > 1:
        img = img.resize((w * scale, h * scale), Image.NEAREST)
    return img


def outside_proof_img(master_rows, total, outside_changed, scale=1):
    """identityMask 外差异证明: 蒙版区=深蓝, 蒙版外人体=灰, 蒙版外差异=纯红(必须为零)。"""
    w, h = len(master_rows[0]), len(master_rows)
    img = Image.new("RGB", (w, h), (16, 16, 20))
    px = img.load()
    for y in range(h):
        for x in range(w):
            if master_rows[y][x] == ".":
                continue
            px[x, y] = (44, 58, 108) if (x, y) in total else (58, 58, 66)
    for (x, y) in outside_changed:
        px[x, y] = (255, 0, 0)
    if scale > 1:
        img = img.resize((w * scale, h * scale), Image.NEAREST)
    return img


def crop_rows(rows, rect):
    x0, y0, x1, y1 = rect
    return [r[x0:x1 + 1] for r in rows[y0:y1 + 1]]


def get_font(size=14):
    for p in ("/System/Library/Fonts/PingFang.ttc",
              "/System/Library/Fonts/Hiragino Sans GB.ttc",
              "/System/Library/Fonts/STHeiti Light.ttc"):
        try:
            return ImageFont.truetype(p, size), True
        except Exception:
            continue
    return ImageFont.load_default(), False


def main():
    # ---------- 0. 输入钉值校验(显式 fail, 不用 assert) ----------
    for path, want in PINNED.items():
        if not path.exists():
            fail(f"缺批准输入 {path.name}")
        got = sha256_file(path)
        if got != want:
            fail(f"{path.name} SHA 不符: {got[:12]}… != 钉值 {want[:12]}…(批准输入被改动)")
    if not MAIN_HTML.exists():
        fail("缺主HTML")
    main_html_before = sha256_file(MAIN_HTML)
    print(f"主HTML范围保护: 构建前SHA={main_html_before[:16]}…(仅日志, 不参与输出)")

    data = load_masters()
    meta = data["meta"]
    if meta.get("personalized") is not False:
        fail("R3A 母版 personalized != false")
    for pose in POSES:
        pv = data["poses"][pose]
        for d in DIRS:
            rows = pv["masterRowsByDir"][d]
            got = hashlib.sha256(("\n".join(rows) + "\n").encode("ascii")).hexdigest()
            if got != pv["contentSha256ByDir"][d]:
                fail(f"{pose}/{d} 行集内容 SHA 与 R3A 记录不符")

    masks = load_masks()
    verify_masks_vs_master(data, masks)
    print("批准蒙版复核: JSON↔30张PNG一致, 子区互斥, ⊆inner, 禁区=0, 颈肩=0, 单簇, L/R镜像一致")

    # ---------- 1. 逐像素绘制 + 逐张合同检查 ----------
    sprites = {}   # (pose, person, d) -> dict
    for pose in POSES:
        pv = data["poses"][pose]
        w, h = pv["w"], pv["h"]
        spec = POSE_CHECK[pose]
        pal = pal_of(pose)
        for d in DIRS:
            master_rows = pv["masterRowsByDir"][d]
            opaque = rows_points(master_rows)
            inner = inner_points(opaque, w, h)
            mk = masks[(pose, d)]
            total = mk["total"]
            forbid = set()
            for rect in spec["forbidRects"]:
                fr = rect_points(rect)
                if d == "R":
                    fr = mirror_set(fr, w)
                forbid |= fr
            forbid |= {p for p in opaque if p[1] >= spec["neckY"]}   # 颈肩带
            forbid |= (opaque - inner)                               # 人物外轮廓
            per = {}
            for person in PERSONS:
                new_rows, changed, sub_changed = apply_paint(pose, person, d, master_rows, masks)
                # 1/2. w/h 一致(由构造, 仍显式校验)
                if len(new_rows) != h or any(len(r) != w for r in new_rows):
                    fail(f"{pose}/{person}/{d} 尺寸漂移")
                # 3. visibleBBox 一致
                if visible_bbox(new_rows) != list(pv["visibleBBoxByDir"][d]):
                    fail(f"{pose}/{person}/{d} visibleBBox 漂移")
                # 4/5/6. alpha/不透明集合/外轮廓一致(只允许不透明->不透明换色)
                if rows_points(new_rows) != opaque:
                    fail(f"{pose}/{person}/{d} alpha/不透明像素集合发生变化")
                # 7/8. changed ⊆ mask; 蒙版外字符差异=0
                if not changed <= total:
                    fail(f"{pose}/{person}/{d} changedPixels 越出批准蒙版 {len(changed - total)}px")
                outside = {(x, y) for y in range(h) for x in range(w)
                           if (x, y) not in total and new_rows[y][x] != master_rows[y][x]}
                if outside:
                    fail(f"{pose}/{person}/{d} identityMask 外存在差异 {len(outside)}px")
                # 9. 禁区(手/拳/臂/颈肩/躯干/泳衣/腿脚/外轮廓)误改=0
                bad = changed & forbid
                if bad:
                    fail(f"{pose}/{person}/{d} 误改禁区/外轮廓 {len(bad)}px")
                # 11. 必须存在有意义的身份修改
                if len(changed) < 8:
                    fail(f"{pose}/{person}/{d} 身份修改过少 changed={len(changed)}")
                # 12/13. hairOrCap 与 eyesOrGlasses 都必须有有意义身份像素
                if sub_changed["hairOrCapMask"] < 4:
                    fail(f"{pose}/{person}/{d} hairOrCap 身份像素不足: {sub_changed['hairOrCapMask']}")
                if sub_changed["eyesOrGlassesMask"] < 3:
                    fail(f"{pose}/{person}/{d} eyesOrGlasses 身份像素不足: {sub_changed['eyesOrGlassesMask']}")
                # 14/15. 单一头部特征簇: changed ⊆ 单一批准蒙版簇(复检=1)且 alpha 未变,
                #        不可能新增第二组眼鼻嘴; 簇桥接间隙内允许未修改的锁定像素
                if semantic_cluster_count(changed, spec["clusterGap"]) < 1:
                    fail(f"{pose}/{person}/{d} 无身份簇")
                # 16. 实际使用颜色 ⊆ 批准调色板(apply_paint 已逐像素卡死, 再整图复核)
                used = sorted({ch for r in new_rows for ch in r if ch != "."})
                if not set(used) <= set(pal.keys()):
                    fail(f"{pose}/{person}/{d} 使用调色板外颜色 {used}")
                per[person] = {"rows": new_rows, "changed": changed,
                               "sub_changed": sub_changed, "outside": outside}
            # 10. 阳阳/爸爸在 identityMask 外完全相同
            ry, rd = per["yy"]["rows"], per["dd"]["rows"]
            for y in range(h):
                for x in range(w):
                    if (x, y) not in total and ry[y][x] != rd[y][x]:
                        fail(f"{pose}/{d} 阳阳/爸爸蒙版外不一致 ({x},{y})")
            for person in PERSONS:
                sprites[(pose, person, d)] = per[person]
            print(f"{pose}/{d}: yy changed={len(per['yy']['changed'])} "
                  f"子区={per['yy']['sub_changed']} | dd changed={len(per['dd']['changed'])} "
                  f"子区={per['dd']['sub_changed']} | outside=0 alpha=0 禁区=0")

    # ---------- 2. 生成全部产物(内存中, 自检后统一原子落盘) ----------
    files = {}
    jsprites = {}
    for pose in POSES:
        pv = data["poses"][pose]
        w, h = pv["w"], pv["h"]
        pal = pal_of(pose)
        hexpal = hex_of(pose)
        jsprites[pose] = {}
        for person in PERSONS:
            jsprites[pose][person] = {}
            for d in DIRS:
                sp = sprites[(pose, person, d)]
                rows = sp["rows"]
                content_sha = hashlib.sha256(("\n".join(rows) + "\n").encode("ascii")).hexdigest()
                used = sorted({ch for r in rows for ch in r if ch != "."})
                used_id = sorted({rows[y][x] for (x, y) in sp["changed"]})
                jsprites[pose][person][d] = {
                    "w": w, "h": h,
                    "root": list(pv["rootByDir"][d]),
                    "visibleBBox": list(pv["visibleBBoxByDir"][d]),
                    "rows": rows,
                    "contentSha256": content_sha,
                    "changedPixels": sorted([list(p) for p in sp["changed"]]),
                    "changedPixelsTotal": len(sp["changed"]),
                    "submaskChanges": sp["sub_changed"],
                    "outsideDiff": 0,
                    "alphaDiff": 0,
                    "forbiddenBodyDiff": 0,
                    "colorsUsed": {ch: hexpal[ch] for ch in used},
                    "colorsUsedInChangedPixels": {ch: hexpal[ch] for ch in used_id},
                    "identityNote": IDENTITY_NOTE[(pose, person)],
                }
                files[f"sprites/{pose}_{person}_{d}.png"] = sprite_png_bytes(rows, pal)
                files[f"diff/{pose}_{person}_{d}_mask.png"] = changed_binary_png_bytes(w, h, sp["changed"])
                files[f"diff/{pose}_{person}_{d}_color.png"] = png_bytes_of(
                    color_diff_img(pv["masterRowsByDir"][d], rows, pal))
                files[f"diff/{pose}_{person}_{d}_outside.png"] = png_bytes_of(
                    outside_proof_img(pv["masterRowsByDir"][d], masks[(pose, d)]["total"], sp["outside"]))

    jdoc = {
        "meta": {
            "schemaVersion": 1,
            "stage": "R3B-I",
            "artifactKind": "identity-sprites",
            "applied": True,
            "sourceMaster": {"file": "sprites_r3a_human_baked.js", "sha256": PINNED[R3A_JS]},
            "r3bm": {"generatorFile": "R3B-M/build_identity_masks_r3bm.py",
                     "generatorSha256": PINNED[R3BM_PY],
                     "jsonFile": "R3B-M/identity_masks_r3bm.json",
                     "jsonSha256": PINNED[R3BM_JSON],
                     "jsFile": "R3B-M/identity_masks_r3bm_baked.js",
                     "jsSha256": PINNED[R3BM_JS]},
            "stage2Avatar": {"file": "avatar_paint.py", "sha256": PINNED[FACES_PY],
                             "note": "仅提供身份特征与批准身份色, 24x24头像未贴入动作帧"},
            "surfaceIdentityPalette": SURFACE_IDENTITY_HEX,
            "underwaterIdentityColorMapping": UW_IDENTITY_MAPPING,
            "poses": list(POSES), "directions": list(DIRS), "persons": list(PERSONS),
            "blindOrder": [f"{p}_{who}_{d}" for p, who, d in BLIND_ORDER],
            "integrationStatus": "not-integrated; machine-PASS only; 视觉需用户/Codex人工审核",
        },
        "sprites": jsprites,
    }
    files["identity_sprites_r3bi.json"] = (json.dumps(jdoc, ensure_ascii=False, indent=1) + "\n").encode()
    files["identity_sprites_r3bi_baked.js"] = (
        "// Generated by build_identity_sprites_r3bi.py; R3B-I identity sprites, NOT referenced by main HTML.\n"
        "const IDENTITY_SPRITES_R3BI = " + json.dumps(jdoc, ensure_ascii=False) + ";\n"
    ).encode()

    files["阶段R3B-I身份稿审核表.png"] = png_bytes_of(build_review_sheet(data, masks, sprites))
    files["阶段R3B-I身份稿盲审图.png"] = png_bytes_of(build_blind_sheet(sprites))

    # ---------- 3. 落盘(tmp + rename, 自检已全过) ----------
    if sha256_file(MAIN_HTML) != main_html_before:
        fail("主HTML在R3B-I构建期间发生变化")
    for rel, content in files.items():
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        tmp.write_bytes(content)
        tmp.replace(dst)
        print(f"写出 {rel} ({len(content)}B)")
    print("ALL R3B-I CHECKS PASS")


def png_bytes_of(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def stack_v(imgs, gap=2, bg=(16, 16, 20)):
    w = max(i.size[0] for i in imgs)
    h = sum(i.size[1] for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("RGB", (w, h), bg)
    y = 0
    for im in imgs:
        out.paste(im, (0, y))
        y += im.size[1] + gap
    return out


def build_review_sheet(data, masks, sprites):
    """6 行(姿态×方向) × 12 栏审核表; 1× 为原像素, 放大均为单次 NEAREST。"""
    font, cjk = get_font(14)
    rows_grid = []
    for pose in POSES:
        pv = data["poses"][pose]
        w, h = pv["w"], pv["h"]
        spec = POSE_CHECK[pose]
        pal = pal_of(pose)
        for d in DIRS:
            mrows = pv["masterRowsByDir"][d]
            yy = sprites[(pose, "yy", d)]["rows"]
            dd = sprites[(pose, "dd", d)]["rows"]
            total = masks[(pose, d)]["total"]
            yy_ch, dd_ch = sprites[(pose, "yy", d)]["changed"], sprites[(pose, "dd", d)]["changed"]
            # 1 母版1× / 2 yy1× / 3 dd1×
            p1 = over_checker(mrows, pal)
            p2 = over_checker(yy, pal)
            p3 = over_checker(dd, pal)
            # 4 yy|dd 并排1×
            pair = checker_bg(w * 2 + 2, h)
            for yy_, r in enumerate(yy):
                for x_, ch in enumerate(r):
                    if ch != ".":
                        pair.load()[x_, yy_] = pal[ch]
            for yy_, r in enumerate(dd):
                for x_, ch in enumerate(r):
                    if ch != ".":
                        pair.load()[w + 2 + x_, yy_] = pal[ch]
            p4 = pair
            # 5/6 yy8× / dd8×
            p5 = over_checker(yy, pal, 8)
            p6 = over_checker(dd, pal, 8)
            # 7 批准蒙版叠加1×(品红=蒙版)
            p7 = mask_overlay_img(mrows, pal, total)
            # 8 changed-pixel 差异(上yy下dd, 变化=新色, 其余压暗)
            p8 = stack_v([color_diff_img(mrows, yy, pal), color_diff_img(mrows, dd, pal)])
            # 9 mask外差异证明(上yy下dd; 红=违规, 应为零)
            p9 = stack_v([outside_proof_img(mrows, total, sprites[(pose, "yy", d)]["outside"]),
                          outside_proof_img(mrows, total, sprites[(pose, "dd", d)]["outside"])])
            # 10 头颈接口8×(yy; 颈肩区蒙版外, yy=dd)
            hw = spec["headWin"]
            if d == "R":
                hw = (w - 1 - hw[2], hw[1], w - 1 - hw[0], hw[3])
            nx0, nx1 = max(0, hw[0] - 2), min(w - 1, hw[2] + 2)
            ny0, ny1 = max(0, spec["neckY"] - 4), min(h - 1, spec["neckY"] + 3)
            p10 = over_checker(crop_rows(yy, (nx0, ny0, nx1, ny1)), pal, 8)
            # 11 手/拳禁区局部8×(yy=dd, 未改)
            hr = spec["forbidRects"][0]
            if d == "R":
                hr = (w - 1 - hr[2], hr[1], w - 1 - hr[0], hr[3])
            p11 = over_checker(crop_rows(yy, hr), pal, 8)
            # 12 真实像素统计
            yc, dc = sprites[(pose, "yy", d)]["sub_changed"], sprites[(pose, "dd", d)]["sub_changed"]
            lines = [f"changed yy={len(yy_ch)} dd={len(dd_ch)}",
                     f"帽/发 y{yc['hairOrCapMask']} d{dc['hairOrCapMask']}",
                     f"镜/眼镜 y{yc['eyesOrGlassesMask']} d{dc['eyesOrGlassesMask']}",
                     f"鼻颧 y{yc['faceDetailMask']} d{dc['faceDetailMask']}",
                     f"嘴 y{yc['mouthMask']} d{dc['mouthMask']}",
                     "outside=0 alpha=0", "bbox/root不变", "禁区=0 轮廓=0"]
            p12 = Image.new("RGB", (250, max(8 * 20 + 10, 60)), (20, 22, 30))
            dr = ImageDraw.Draw(p12)
            for i, ln in enumerate(lines):
                dr.text((6, 5 + i * 20), ln, fill=(210, 210, 220), font=font)
            panels = [("母版1×", p1), ("阳阳1×", p2), ("爸爸1×", p3), ("阳|爸1×", p4),
                      ("阳阳8×", p5), ("爸爸8×", p6), ("蒙版叠加1×", p7),
                      ("差异yy/dd1×", p8), ("mask外差异yy/dd", p9),
                      ("头颈8×(阳;颈肩阳=爸)", p10), ("手拳8×(阳=爸,未改)", p11),
                      ("真实像素统计", p12)]
            rows_grid.append((f"{pose} · {d}", panels))
    col_gap, label_h = 10, 22
    col_titles = [t for t, _ in rows_grid[0][1]]
    col_w = []
    for ci, name in enumerate(col_titles):
        wmax = max(panels[ci][1].size[0] for _, panels in rows_grid)
        tw = int(font.getlength(name)) + 6
        col_w.append(max(wmax, tw))
    row_h = [max(p.size[1] for _, p in panels) + label_h for _, panels in rows_grid]
    total_w = sum(col_w) + col_gap * (len(col_w) + 1) + 100
    total_h = sum(row_h) + 8 * (len(rows_grid) + 1) + 30
    sheet = Image.new("RGB", (total_w, total_h), (28, 28, 34))
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 6), "阶段R3B-I 身份稿审核表(机器PASS≠视觉通过; 待人检)" if cjk else "R3B-I review",
            fill=(255, 220, 100), font=font)
    y = 30
    for ri, (label, panels) in enumerate(rows_grid):
        dr.text((6, y + 4), label, fill=(140, 220, 252), font=font)
        x = 100
        for ci, (title, p) in enumerate(panels):
            dr.text((x, y), title, fill=(200, 200, 210), font=font)
            sheet.paste(p, (x, y + label_h))
            x += col_w[ci] + col_gap
        y += row_h[ri] + 8
    return sheet


def build_blind_sheet(sprites):
    """12 张完整人物盲审: 固定匿名顺序, 每张 1×/3×/8×, 无姓名/身份标签。"""
    font, cjk = get_font(14)
    tiles = []
    for i, (pose, person, d) in enumerate(BLIND_ORDER):
        rows = sprites[(pose, person, d)]["rows"]
        pal = pal_of(pose)
        w, h = len(rows[0]), len(rows)
        trip = Image.new("RGB", (w + 2 + w * 3 + 2 + w * 8, h * 8), (16, 16, 20))
        trip.paste(over_checker(rows, pal, 1), (0, 0))
        trip.paste(over_checker(rows, pal, 3), (w + 2, 0))
        trip.paste(over_checker(rows, pal, 8), (w + 2 + w * 3 + 2, 0))
        tiles.append((f"#{i + 1}", trip))
    tw = max(t.size[0] for _, t in tiles)
    th = max(t.size[1] for _, t in tiles)
    cols = 2
    rowsn = (len(tiles) + cols - 1) // cols
    blind = Image.new("RGB", (tw * cols + 20 * (cols + 1), (th + 26) * rowsn + 60), (24, 24, 30))
    drb = ImageDraw.Draw(blind)
    drb.text((10, 6), "盲审(固定匿名顺序): 每张应是一个完整的人+正确动作; 1×/3×/8× 单次最近邻" if cjk
             else "blind review", fill=(255, 220, 100), font=font)
    drb.text((10, 26), "判断: 人物完整? 动作正确? 两种身份能否区分?" if cjk else "",
             fill=(200, 200, 210), font=font)
    for i, (lab, t) in enumerate(tiles):
        gx = 20 + (i % cols) * (tw + 20)
        gy = 48 + (i // cols) * (th + 26)
        drb.text((gx, gy - 18), lab, fill=(180, 180, 190), font=font)
        blind.paste(t, (gx, gy))
    return blind


if __name__ == "__main__":
    main()
