#!/usr/bin/env python3
# 阶段R3B-M: 身份编辑蒙版提案(不绘制身份, 只圈定未来允许编辑的头部内部像素)
#
# 输入(全部只读, SHA 钉死, 不符即 fail):
#   ../sprites_r3a_human_baked.js   R3A 批准人体母版(唯一人体来源)
#   ../build_sprites_r3a.py        R3A 生成器(仅校验未被改动)
#   ../avatar_paint.py             Stage2 身份母版(本轮只校验存在与哈希, 不读取像素进母版)
#   ../../../阳阳水泳大乱斗-原版复刻.html  主HTML(非构建输入; 仅范围保护: 构建前记录SHA, 落盘前复核未变化)
# 输出(全部写到本目录 R3B-M/, 自检全过后才落盘):
#   masks/<POSE>_<DIR>.png 总蒙版二值图(0/255)
#   masks/sub/<POSE>_<DIR>_<SUB>.png 四个语义子蒙版
#   identity_masks_r3bm.json / identity_masks_r3bm_baked.js
#   阶段R3B-M身份蒙版审核表.png / 阶段R3B-M身份蒙版盲审图.png
# 文档(清单/复现记录/验收记录)由人工(主代理)依据自检输出撰写, 不由本脚本生成。
#
# 蒙版规则(每姿态 L 向定义, R 向=水平镜像+独立断言, 逐向人工目检):
#   1. inner(p): p 不透明且 8 邻域全不透明 -> 排除人物外轮廓, 蒙版只能改内部
#   2. headWin 头部窗口 ∩ y < neckY(颈肩接口行起排除)
#   3. 语义子蒙版: eyesOrGlasses=头区内白字符(W/w, 原版眼窝/镜区);
#      mouth=嘴窗内像素; hairOrCap=发/帽区(y<=hairYMax); faceDetail=其余头内部像素
#   4. 禁区(手/拳/臂、颈肩带、躯干、泳衣/白领、腿脚)交集必须为 0
#   5. 总蒙版 8 连通域==1(只能对应同一颗头)
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent          # R3B-M/
OUT = BASE
KIMI_DEV = BASE.parent                           # 过程文件/Kimi开发
PROJECT = KIMI_DEV.parent.parent                 # 项目根

R3A_JS = KIMI_DEV / "sprites_r3a_human_baked.js"
R3A_PY = KIMI_DEV / "build_sprites_r3a.py"
FACES_PY = KIMI_DEV / "avatar_paint.py"
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
}
# 主HTML不是构建输入, 仅作范围保护: 构建前记录SHA, 正式落盘前复核未变化;
# 不固定任何特定版本SHA, 也不写入任何输出物(仅终端日志), 保证干净Git基线可复现。

PAL = {"O": (0, 0, 0), "D": (60, 32, 24), "d": (120, 64, 49), "s": (180, 96, 73),
       "S": (241, 129, 98), "W": (241, 242, 241),
       "u": (0, 64, 88), "m": (60, 188, 252), "l": (164, 228, 252), "w": (252, 252, 252)}

SUBKINDS = ("hairOrCapMask", "eyesOrGlassesMask", "faceDetailMask", "mouthMask")
SUBCOLOR = {"hairOrCapMask": (252, 208, 60), "eyesOrGlassesMask": (60, 220, 252),
            "faceDetailMask": (120, 220, 120), "mouthMask": (252, 80, 80)}

# 逐姿态蒙版规则(基于 L 向母版逐像素目检; 坐标均为闭区间)
# faceDetailWin = 鼻/少量脸阴影小窗; 脸基色(肤色)不进蒙版, 保持原版人体锁定
POSE_RULES = {
    "SURF0": {
        "headWin": (0, 0, 20, 9),      # 头内部窗口(x0..x1, y0..y1)
        "neckY": 10,                   # y>=10 颈肩接口/身体, 排除
        "hairYMax": 3,                 # y<=3 发/泳帽区
        "mouthWin": (7, 8, 10, 9),     # 嘴/颏部肤色暗区
        "faceDetailWin": (11, 6, 16, 7),  # 鼻/颧阴影
        "clusterGap": 3,               # 发区底y3->眼区顶y6 间 3px 锁定脸基色
        # 禁区(手/臂/颈肩/躯干): 右下臂前伸区、颈肩带、水下躯干
        "forbidRects": [(20, 9, 30, 12), (0, 10, 30, 20), (21, 0, 30, 8)],
    },
    "JUMP_AIR": {
        "headWin": (11, 0, 33, 11),
        "neckY": 12,
        "hairYMax": 4,
        "mouthWin": (23, 10, 29, 11),
        "faceDetailWin": (22, 9, 28, 9),   # 鼻梁(两眼窝之间下方)
        "clusterGap": 3,
        # 禁区: 右臂+举拳(x>=34 上段), 左臂(x<=10), 白领巾(y>=13), 躯干四肢(y>=12)
        "forbidRects": [(34, 0, 54, 12), (0, 13, 10, 26), (0, 12, 54, 41)],
    },
    "UW_NORMAL": {
        "headWin": (12, 1, 25, 10),
        "neckY": 11,
        "hairYMax": 3,
        "mouthWin": (20, 10, 24, 10),
        "faceDetailWin": (15, 8, 19, 9),   # 脸中部鼻/阴影
        "clusterGap": 4,               # 发区底y3->眼区顶y7 间 4px 锁定水下脸基色m
        # 禁区: 前伸臂(x>=26), 后肢(x<=11), 颈肩/躯干(y>=11)
        "forbidRects": [(26, 5, 38, 12), (0, 8, 11, 19), (0, 11, 38, 20)],
    },
}
POSES = ("SURF0", "JUMP_AIR", "UW_NORMAL")
DIRS = ("L", "R")


def fail(msg):
    raise SystemExit(f"R3B-M FAIL: {msg}")


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_masters():
    if not R3A_JS.exists():
        fail(f"缺 R3A 母版 {R3A_JS}")
    src = R3A_JS.read_text(encoding="utf-8")
    m = re.search(r"=\s*(\{.*\});?\s*$", src, re.S)
    if not m:
        fail("sprites_r3a_human_baked.js 解析失败")
    return json.loads(m.group(1))


def rows_points(rows):
    return {(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != "."}


def inner_points(opaque, w, h):
    """8邻域全不透明的内部像素(排除外轮廓)。"""
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
    """语义簇数: 允许子区间 <=gap px 的锁定间隙(发区到眉眼之间隔着锁定的
    脸基色行, 间隙宽度按姿态实测: SURF0=3, UW=4), 同属一颗头的子区仍算一簇;
    远处部件(如拳头/手臂)若误入会超出 gap 形成第二簇。"""
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


def build_masks_l(pose, rows):
    """按规则生成 L 向四个语义子蒙版(像素集)。"""
    spec = POSE_RULES[pose]
    w, h = len(rows[0]), len(rows)
    opaque = rows_points(rows)
    inner = inner_points(opaque, w, h)
    hw = spec["headWin"]
    head_inner = {p for p in inner
                  if hw[0] <= p[0] <= hw[2] and hw[1] <= p[1] <= hw[3]
                  and p[1] < spec["neckY"]}
    subs = {k: set() for k in SUBKINDS}
    mw = spec["mouthWin"]
    fw = spec["faceDetailWin"]
    for (x, y) in sorted(head_inner):
        ch = rows[y][x]
        if ch in ("W", "w"):
            subs["eyesOrGlassesMask"].add((x, y))
        elif mw[0] <= x <= mw[2] and mw[1] <= y <= mw[3]:
            subs["mouthMask"].add((x, y))
        elif y <= spec["hairYMax"]:
            subs["hairOrCapMask"].add((x, y))
        elif fw[0] <= x <= fw[2] and fw[1] <= y <= fw[3]:
            subs["faceDetailMask"].add((x, y))
        # 其余头内部像素(脸基色等)不进蒙版, 保持锁定
    return subs


def mirror_set(points, w):
    return {(w - 1 - x, y) for (x, y) in points}


def mask_png_bytes(w, h, points):
    img = Image.new("L", (w, h), 0)
    px = img.load()
    for (x, y) in points:
        px[x, y] = 255
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_rows(rows, scale=1, highlight=None, hl_color=(252, 60, 200), dim_outside=None):
    """母版渲染; highlight=蒙版像素(高亮色替换), dim_outside=蒙版像素集时蒙版外降暗。"""
    w, h = len(rows[0]), len(rows)
    img = Image.new("RGB", (w, h), (0, 0, 0))
    px = img.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == ".":
                px[x, y] = (0, 0, 0) if False else px[x, y]
                continue
            c = PAL[ch]
            if highlight and (x, y) in highlight:
                c = hl_color
            elif dim_outside is not None and (x, y) not in dim_outside:
                c = (c[0] // 3, c[1] // 3, c[2] // 3)
            px[x, y] = c
    if scale > 1:
        img = img.resize((w * scale, h * scale), Image.NEAREST)
    return img


def checker_bg(w, h, cell=4):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (58, 58, 68) if (x // cell + y // cell) % 2 == 0 else (42, 42, 52)
    return img


def over_checker(sprite_rows, scale):
    w, h = len(sprite_rows[0]), len(sprite_rows)
    bg = checker_bg(w, h)
    fg = render_rows(sprite_rows)
    bg.paste(fg, (0, 0), fg.split()[3] if fg.mode == "RGBA" else None)
    # 直接合成: 母版不透明像素盖棋盘
    px = bg.load()
    for y, r in enumerate(sprite_rows):
        for x, ch in enumerate(r):
            if ch != ".":
                px[x, y] = PAL[ch]
    return bg.resize((w * scale, h * scale), Image.NEAREST)


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
    # contentSha256ByDir 复核
    for pose in POSES:
        pv = data["poses"][pose]
        for d in DIRS:
            rows = pv["masterRowsByDir"][d]
            got = hashlib.sha256(("\n".join(rows) + "\n").encode("ascii")).hexdigest()
            if got != pv["contentSha256ByDir"][d]:
                fail(f"{pose}/{d} 行集内容 SHA 与 R3A 记录不符")

    # ---------- 1. 构建蒙版 ----------
    masks = {}   # (pose, dir) -> {subkind: set}
    for pose in POSES:
        pv = data["poses"][pose]
        w = pv["w"]
        subs_l = build_masks_l(pose, pv["masterRowsByDir"]["L"])
        masks[(pose, "L")] = subs_l
        masks[(pose, "R")] = {k: mirror_set(s, w) for k, s in subs_l.items()}

    # ---------- 2. 自检(全部显式 fail) ----------
    report = []
    for pose in POSES:
        pv = data["poses"][pose]
        w, h = pv["w"], pv["h"]
        spec = POSE_RULES[pose]
        for d in DIRS:
            rows = pv["masterRowsByDir"][d]
            opaque = rows_points(rows)
            subs = masks[(pose, d)]
            total = set().union(*subs.values())
            # 子蒙版互不重叠 + 并集=总蒙版(由构造保证, 仍断言)
            seen = set()
            for k in SUBKINDS:
                inter = seen & subs[k]
                if inter:
                    fail(f"{pose}/{d} 子蒙版重叠 {k}: {len(inter)}px")
                seen |= subs[k]
            if seen != total:
                fail(f"{pose}/{d} 子蒙版并集 != 总蒙版")
            # mask ⊆ opaque(头部内部不透明像素)
            if not total <= opaque:
                fail(f"{pose}/{d} 蒙版含透明/界外像素: {len(total - opaque)}px")
            # 蒙版不含外轮廓像素(全部必须为 inner)
            inner = inner_points(opaque, w, h)
            if not total <= inner:
                fail(f"{pose}/{d} 蒙版触及外轮廓: {len(total - inner)}px")
            # 禁区(镜像)交集=0
            for rect in spec["forbidRects"]:
                fr = rect_points(rect)
                if d == "R":
                    fr = mirror_set(fr, w)
                hit = total & fr
                if hit:
                    fail(f"{pose}/{d} 蒙版侵入禁区 {rect}: {len(hit)}px")
            # 颈肩带(y>=neckY)像素=0
            neck = {p for p in total if p[1] >= spec["neckY"]}
            if neck:
                fail(f"{pose}/{d} 蒙版侵入颈肩接口: {len(neck)}px")
            # 单一头部语义簇(子区间允许 <=clusterGap px 锁定肤色间隙;
            # 拳头/手臂等远离头部的误入会超出 gap 形成第二簇;
            # 与头相邻部件(如JUMP举拳)另由 forbidRects=0 显式保证)
            nclus = semantic_cluster_count(total, gap=spec["clusterGap"])
            if nclus != 1:
                fail(f"{pose}/{d} 蒙版存在 {nclus} 个语义簇(第二脸风险)")
            # 蒙版完全位于 headWin 内
            hw = spec["headWin"]
            if d == "R":
                hw = (w - 1 - hw[2], hw[1], w - 1 - hw[0], hw[3])
            out = [p for p in total
                   if not (hw[0] <= p[0] <= hw[2] and hw[1] <= p[1] <= hw[3])]
            if out:
                fail(f"{pose}/{d} 蒙版越出头部窗口: {len(out)}px")
            if not total:
                fail(f"{pose}/{d} 蒙版为空")
            counts = {k: len(subs[k]) for k in SUBKINDS}
            report.append((pose, d, len(opaque), len(total), counts))
            print(f"{pose}/{d}: 有效px={len(opaque)} 蒙版={len(total)} "
                  f"({100.0*len(total)/len(opaque):.1f}%) 子区={counts} 簇=1 禁区=0 颈肩=0")

    # changedPixels=0: 本轮不产出任何身份绘制, 母版行集原样转发, 不做任何修改
    changed_pixels = 0
    print(f"本轮身份实际绘制像素 changedPixels={changed_pixels}(必须为0)")

    # ---------- 3. 输出(先全部生成于内存, 自检过后统一落盘) ----------
    font, cjk = get_font(14)
    font_sm = font if cjk else font

    files = {}   # relpath -> bytes
    # 3a. mask PNG(总+子)
    for pose in POSES:
        pv = data["poses"][pose]
        w, h = pv["w"], pv["h"]
        for d in DIRS:
            subs = masks[(pose, d)]
            total = set().union(*subs.values())
            files[f"masks/{pose}_{d}.png"] = mask_png_bytes(w, h, total)
            for k in SUBKINDS:
                files[f"masks/sub/{pose}_{d}_{k}.png"] = mask_png_bytes(w, h, subs[k])

    # 3b. JSON / JS
    def runs_of(points):
        return sorted(points)
    jdoc = {
        "meta": {"schemaVersion": 1, "stage": "R3B-M", "artifactKind": "identity-mask-proposal",
                 "applied": False, "changedPixels": 0,
                 "sourceMaster": {"file": "sprites_r3a_human_baked.js",
                                  "sha256": PINNED[R3A_JS]},
                 "note": "仅蒙版提案; 未绘制身份; 待人工审核批准后方可进入 R3B-I"},
        "masks": {},
    }
    for pose in POSES:
        jdoc["masks"][pose] = {}
        for d in DIRS:
            subs = masks[(pose, d)]
            total = set().union(*subs.values())
            jdoc["masks"][pose][d] = {
                "w": data["poses"][pose]["w"], "h": data["poses"][pose]["h"],
                "totalPixels": len(total),
                "submaskPixels": {k: len(subs[k]) for k in SUBKINDS},
                "identityMask": runs_of(total),
                "submasks": {k: runs_of(subs[k]) for k in SUBKINDS},
            }
    files["identity_masks_r3bm.json"] = (json.dumps(jdoc, ensure_ascii=False, indent=1) + "\n").encode()
    files["identity_masks_r3bm_baked.js"] = (
        "// Generated by build_identity_masks_r3bm.py; identity mask proposal only, NOT applied.\n"
        "const IDENTITY_MASKS_R3BM = " + json.dumps(jdoc, ensure_ascii=False) + ";\n"
    ).encode()

    # 3c. 审核表: 6 行(姿态×方向) × 10 栏
    rows_img = []
    gap = 8
    col_w = []
    panels_grid = []
    for pose in POSES:
        pv = data["poses"][pose]
        w, h = pv["w"], pv["h"]
        spec = POSE_RULES[pose]
        for d in DIRS:
            rows = pv["masterRowsByDir"][d]
            subs = masks[(pose, d)]
            total = set().union(*subs.values())
            hw = spec["headWin"]
            if d == "R":
                hw = (w - 1 - hw[2], hw[1], w - 1 - hw[0], hw[3])
            hwc = (max(0, hw[0] - 2), max(0, hw[1] - 2), min(w - 1, hw[2] + 2), min(h - 1, hw[3] + 2))

            p1 = over_checker(rows, 1)                                     # 1 母版1×
            head_img = over_checker([r[hwc[0]:hwc[2] + 1] for r in rows[hwc[1]:hwc[3] + 1]], 1)
            p2 = head_img                                                  # 2 头检区1×
            p3 = Image.open(__import__("io").BytesIO(mask_png_bytes(w, h, total))).convert("RGB")  # 3 总蒙版1×
            # 4 子蒙版合成1×(四色)
            p4 = Image.new("RGB", (w, h), (16, 16, 20))
            px4 = p4.load()
            for k in SUBKINDS:
                for (x, y) in subs[k]:
                    px4[x, y] = SUBCOLOR[k]
            p5 = over_checker(rows, 1)                                     # 5 蒙版叠加1×
            ov = render_rows(rows, 1, highlight=total)
            bg = checker_bg(w, h)
            bg.paste(ov, (0, 0), Image.eval(ov.convert("L"), lambda v: 255 if v else 0))
            p5 = bg
            # 直接用简单合成重画(避免 paste mask 误判黑像素)
            p5 = checker_bg(w, h)
            px5 = p5.load()
            for y, r in enumerate(rows):
                for x, ch in enumerate(r):
                    if ch != ".":
                        px5[x, y] = (252, 60, 200) if (x, y) in total else PAL[ch]
            # 6 蒙版外锁定区1×(蒙版像素显示为暗格, 其余正常)
            p6 = checker_bg(w, h)
            px6 = p6.load()
            for y, r in enumerate(rows):
                for x, ch in enumerate(r):
                    if ch != "." and (x, y) not in total:
                        px6[x, y] = PAL[ch]
            p7 = over_checker(rows, 8)                                     # 7 母版8×
            ov8 = checker_bg(w, h)                                         # 8 叠加8×
            px8 = ov8.load()
            for y, r in enumerate(rows):
                for x, ch in enumerate(r):
                    if ch != ".":
                        px8[x, y] = (252, 60, 200) if (x, y) in total else PAL[ch]
            p8 = ov8.resize((w * 8, h * 8), Image.NEAREST)
            # 9 手/拳禁区局部 + 计数文字; 10 颈肩接口局部 + 计数文字
            hand_rect = spec["forbidRects"][0]
            if d == "R":
                hand_rect = (w - 1 - hand_rect[2], hand_rect[1], w - 1 - hand_rect[0], hand_rect[3])
            hx0, hy0, hx1, hy1 = hand_rect
            hand_crop = [r[hx0:hx1 + 1] for r in rows[hy0:hy1 + 1]]
            hand_img = checker_bg(hx1 - hx0 + 1, hy1 - hy0 + 1)
            pxh = hand_img.load()
            for yy, r in enumerate(hand_crop):
                for xx, ch in enumerate(r):
                    if ch != ".":
                        pxh[xx, yy] = PAL[ch]
            p9 = hand_img.resize(((hx1 - hx0 + 1) * 8, (hy1 - hy0 + 1) * 8), Image.NEAREST)
            ny0 = max(0, spec["neckY"] - 3)
            ny1 = min(h - 1, spec["neckY"] + 3)
            nx0, nx1 = hwc[0], hwc[2]
            neck_crop = [r[nx0:nx1 + 1] for r in rows[ny0:ny1 + 1]]
            neck_img = checker_bg(nx1 - nx0 + 1, ny1 - ny0 + 1)
            pxn = neck_img.load()
            for yy, r in enumerate(neck_crop):
                for xx, ch in enumerate(r):
                    if ch != ".":
                        pxn[xx, yy] = PAL[ch]
            p10 = neck_img.resize(((nx1 - nx0 + 1) * 8, (ny1 - ny0 + 1) * 8), Image.NEAREST)
            panels = [("母版1×", p1), ("头区1×", p2), ("蒙版1×", p3),
                      ("子区1×", p4), ("叠加1×", p5), ("锁定1×", p6),
                      ("母版8×", p7), ("叠加8×", p8),
                      ("手拳8× 蒙版=0", p9), ("颈肩8× 蒙版=0", p10)]
            panels_grid.append((f"{pose} · {d}", panels))
    # 排版: 列宽 = max(面板宽, 标签文字宽), 避免窄列标签互相重叠
    col_gap = 10
    label_h = 22
    col_titles = [t for t, _ in panels_grid[0][1]]
    col_w = []
    for ci, name in enumerate(col_titles):
        wmax = max(panels[ci][1].size[0] for _, panels in panels_grid)
        tw = int(font_sm.getlength(name)) + 6 if cjk else int(font_sm.getlength(name)) + 6
        col_w.append(max(wmax, tw))
    row_h = [max(p.size[1] for _, p in panels) + label_h for _, panels in panels_grid]
    total_w = sum(col_w) + col_gap * (len(col_w) + 1) + 130
    total_h = sum(row_h) + gap * (len(panels_grid) + 1) + 30
    sheet = Image.new("RGB", (total_w, total_h), (28, 28, 34))
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 6), "阶段R3B-M 身份蒙版审核表(仅提案, 未绘制身份)" if cjk else
            "R3B-M identity mask review (proposal only)", fill=(255, 220, 100), font=font)
    y = 30
    for ri, (label, panels) in enumerate(panels_grid):
        dr.text((6, y + 4), label, fill=(140, 220, 252), font=font)
        x = 130
        for ci, (title, p) in enumerate(panels):
            dr.text((x, y), title, fill=(200, 200, 210), font=font)
            sheet.paste(p, (x, y + label_h))
            x += col_w[ci] + col_gap
        y += row_h[ri] + gap
    import io as _io
    buf = _io.BytesIO()
    sheet.save(buf, format="PNG")
    files["阶段R3B-M身份蒙版审核表.png"] = buf.getvalue()

    # 3d. 盲审图: 6 张叠加图, 固定伪随机顺序(无姓名/姿态/队色标签, 只编号)
    order = [("UW_NORMAL", "R"), ("SURF0", "L"), ("JUMP_AIR", "R"),
             ("UW_NORMAL", "L"), ("JUMP_AIR", "L"), ("SURF0", "R")]
    tiles = []
    for i, (pose, d) in enumerate(order):
        pv = data["poses"][pose]
        rows = pv["masterRowsByDir"][d]
        w, h = pv["w"], pv["h"]
        total = set().union(*masks[(pose, d)].values())
        img = checker_bg(w, h)
        px = img.load()
        for yy, r in enumerate(rows):
            for xx, ch in enumerate(r):
                if ch != ".":
                    px[xx, yy] = (252, 60, 200) if (xx, yy) in total else PAL[ch]
        tiles.append((f"#{i + 1}", img.resize((w * 8, h * 8), Image.NEAREST)))
    tw = max(t.size[0] for _, t in tiles)
    th = max(t.size[1] for _, t in tiles)
    blind = Image.new("RGB", (tw * 3 + 60, th * 2 + 90), (24, 24, 30))
    drb = ImageDraw.Draw(blind)
    drb.text((10, 6), "盲审(无标签): 每张应只有一个头部编辑区" if cjk else "blind review",
             fill=(255, 220, 100), font=font)
    for i, (lab, t) in enumerate(tiles):
        gx = 10 + (i % 3) * (tw + 20)
        gy = 34 + (i // 3) * (th + 24)
        drb.text((gx, gy - 18), lab, fill=(180, 180, 190), font=font)
        blind.paste(t, (gx, gy))
    buf = _io.BytesIO()
    blind.save(buf, format="PNG")
    files["阶段R3B-M身份蒙版盲审图.png"] = buf.getvalue()

    # ---------- 4. 落盘(tmp + rename, 自检已全过) ----------
    # 范围保护复核: 全部计算与自检完成、尚未写入正式输出前, 确认主HTML未被构建过程触碰
    if sha256_file(MAIN_HTML) != main_html_before:
        fail("主HTML在R3B-M构建期间发生变化")
    for rel, content in files.items():
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        tmp.write_bytes(content)
        tmp.replace(dst)
        print(f"写出 {rel} ({len(content)}B)")

    print("ALL R3B-M CHECKS PASS")
    return report


if __name__ == "__main__":
    main()
