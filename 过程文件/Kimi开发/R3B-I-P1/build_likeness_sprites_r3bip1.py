#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 R3B-I-P1 本人特征小范围验证 确定性构建脚本
=================================================
目标：只做 SURF0-L / JUMP_AIR-L × 阳阳/爸爸 共 4 张"本人特征"测试稿，
验证儿童泳帽护目镜版阳阳与短黑发粗框眼镜版爸爸能否在真实动作母版上成立。

与 R3B-I 的本质区别：
  - R3B-I 的"全图 alpha 锁定"在本轮被显式放宽为一个严格受限的"头部肖像例外区域"；
  - 例外区域完全位于颈部以上、且不超出 R3A 头部原有可见包围盒；
  - 区域内允许修改脸型/下巴/耳朵/头发/泳帽/护目镜/眼镜及相关 alpha 轮廓；
  - 区域外 RGB/alpha 必须逐像素为 0 差异；颈部及以下必须为 0 差异；
  - root / 画布尺寸 / visibleBBox（不扩大）/ 身体像素 全部锁定。

硬性合同：
  1) 唯一身体底稿 = sprites_r3a_human_baked.js（SHA-256 钉值）；
  2) 旧 R3B-I 失败稿仅作为对照输入展示，绝不在其脸上小修小补；
  3) 例外区域以显式像素位图落盘（masks/）+ JSON 坐标，连通分量如实计数（允许多个）；
  4) 修改像素全部来自 R3A 表面调色板（阳阳泳帽允许两档蓝 #3C9CF0/#1E5AA8）；
  5) 不使用家庭照片、概念图作为构建输入；无随机、无平滑、无渐变；
  6) 双跑 SHA 完全一致；篡改输入必须失败且旧产物不被覆盖；
  7) 绝不修改 阳阳水泳大乱斗-原版复刻.html；
  8) 机器 PASS ≠ 视觉通过。视觉判定权属于用户与外部 Codex。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ============================================================
# 0. 路径与钉值
# ============================================================

ROOT = Path(__file__).resolve().parents[3]
OUTDIR = ROOT / "过程文件" / "Kimi开发" / "R3B-I-P1"
DEVDIR = ROOT / "过程文件" / "Kimi开发"
R3BI = DEVDIR / "R3B-I"

F_R3A_JS = DEVDIR / "sprites_r3a_human_baked.js"
F_R3A_PY = DEVDIR / "build_sprites_r3a.py"
F_AVATAR = DEVDIR / "avatar_paint.py"
F_R3A_MANIFEST = DEVDIR / "阶段3A-R3A人体母版清单.md"
F_R3A_ACCEPT = DEVDIR / "阶段3A-R3A人体母版验收记录.md"
F_R3A_REPRO = DEVDIR / "阶段3A-R3A构建复现记录.md"
F_MAIN_HTML = ROOT / "阳阳水泳大乱斗-原版复刻.html"

# 旧 R3B-I 失败稿（仅对照展示用，不是批准输入，绝不做为绘制底稿）
F_R3BI_JSON = R3BI / "identity_sprites_r3bi.json"
OLD_SPRITES = {
    ("SURF0", "yy"): R3BI / "sprites" / "SURF0_yy_L.png",
    ("SURF0", "dd"): R3BI / "sprites" / "SURF0_dd_L.png",
    ("JUMP_AIR", "yy"): R3BI / "sprites" / "JUMP_AIR_yy_L.png",
    ("JUMP_AIR", "dd"): R3BI / "sprites" / "JUMP_AIR_dd_L.png",
}

# SHA-256 钉值：与 R3B-I 相同来源
PINNED = {
    str(F_R3A_JS.relative_to(ROOT)): "bbd40b05f6d7143826f7d554f04deb878a98bf503c09c6fd5bf00c1e612bf7f2",
    str(F_R3A_PY.relative_to(ROOT)): "bffb7e445be037fe5262993393c91e5f33ada7ca5c6eee2a2a629854b075d1be",
    str(F_AVATAR.relative_to(ROOT)): "615daea6e81acbc60d1e59bf5c83fd4582fd064c35b1d5aa425c1793d7b1194e",
    str(F_R3A_MANIFEST.relative_to(ROOT)): "f49af48471782e5edbbcc3f01bc90c90eefcd48fb48edb54fdb15fd509c31152",
    str(F_R3A_ACCEPT.relative_to(ROOT)): "6c0fe04e5aff1f7aaf6cbd01098f03bfb38cb99bfd4e43f732bee2adeda5e04a",
    str(F_R3A_REPRO.relative_to(ROOT)): "d480a7207fe28344d1e61ec7d1eba0ea85e3e895ddabad4a1b2c8ec3dfd6cec1",
}
for rel, want in PINNED.items():
    p = ROOT / rel
    if not p.is_file():
        print(f"FATAL: 批准输入缺失: {rel}", file=sys.stderr)
        sys.exit(1)
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != want:
        print(f"FATAL: 批准输入SHA不匹配: {rel}", file=sys.stderr)
        sys.exit(1)
if not F_MAIN_HTML.is_file():
    print("FATAL: 主HTML不存在", file=sys.stderr)
    sys.exit(1)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


# ============================================================
# 1. 调色板（R3A 表面板 + 阶段2批准阳阳蓝；爸爸本轮使用黑/深棕发系 O/D）
# ============================================================

RGB = {
    "O": (0, 0, 0),
    "D": (60, 32, 24),
    "d": (120, 64, 49),
    "s": (180, 96, 73),
    "S": (241, 129, 98),
    "W": (241, 242, 241),
    "C": (60, 156, 240),   # 阳阳泳帽亮蓝（仅阳阳）
    "c": (30, 90, 168),    # 阳阳泳帽暗蓝（仅阳阳）
}
SURFACE_KEYS = set(RGB.keys())

# ============================================================
# 2. R3A 母版载入
# ============================================================

src = F_R3A_JS.read_text(encoding="utf-8")
m = re.search(r"=\s*(\{.*\});?\s*$", src, re.S)
if not m:
    fail("无法解析 sprites_r3a_human_baked.js")
try:
    r3a = json.loads(m.group(1))
except json.JSONDecodeError as exc:
    fail(f"R3A JSON 解析失败: {exc}")
POSES = r3a["poses"]
for pose in ("SURF0", "JUMP_AIR"):
    if pose not in POSES:
        fail(f"R3A 缺少姿态 {pose}")

NECK_Y = {"SURF0": 10, "JUMP_AIR": 12}      # 颈行 y（y>=neckY 为颈部及以下，禁改）
WIN_X0 = {"SURF0": 0, "JUMP_AIR": 10}       # 编辑表窗口起点 x

# ============================================================
# 3. 头部肖像例外区域（显式定义，逐像素位图落盘）
#    规则：region = 头部可见包围盒内 且 y < neckY 的像素集合（含盒内透明孔）；
#    另加行级规则：y == neckY-1（紧邻颈行的头底行）只允许换色，不允许 alpha 增减，
#    以保证颈接面形状不变。alpha 变更仅在 y <= neckY-2 发生。
# ============================================================


def build_region(pose: str, master: list[str]) -> set[tuple[int, int]]:
    neck = NECK_Y[pose]
    head_rows = master[:neck]
    xs = [x for row in head_rows for x, ch in enumerate(row) if ch != "."]
    ys = [y for y, row in enumerate(head_rows) for x, ch in enumerate(row) if ch != "."]
    if not xs:
        fail(f"{pose}: 头部无非透明像素")
    hx0, hx1, hy0, hy1 = min(xs), max(xs), min(ys), max(ys)
    region = {(x, y) for y in range(hy0, hy1 + 1) for x in range(hx0, hx1 + 1)}
    # 防御：必须全部位于颈部以上
    if hy1 > neck - 1:
        fail(f"{pose}: 头部包围盒越入颈行")
    return region


def components(region: set[tuple[int, int]]) -> int:
    """4-邻接连通分量计数（如实报告，允许多个）。"""
    seen: set[tuple[int, int]] = set()
    n = 0
    for start in region:
        if start in seen:
            continue
        n += 1
        dq = deque([start])
        seen.add(start)
        while dq:
            x, y = dq.popleft()
            for nb in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nb in region and nb not in seen:
                    seen.add(nb)
                    dq.append(nb)
    return n

# ============================================================
# 4. 四张身份设计表（窗口坐标：SURF0 x0..21；JUMP_AIR x10..35）
#    '.'=透明（仅允许在 y<=neckY-2 与原图不同）；未列出的行 = 不修改。
#    设计依据见 阶段R3B-I-P1身份稿清单.md。
# ============================================================

EDITS: dict[tuple[str, str], dict[int, str]] = {
    # ---------------- SURF0 / 阳阳：圆短儿童脸 + 蓝泳帽 + 帽上护目镜 ----------------
    ("SURF0", "yy"): {
        0: "......OOOOOOOOO.......",
        1: "...OOCCCCCCCCCCCO.....",
        2: "..OCCCCCCCCCCCCCCCO...",
        3: "..OCCCOWWWWWWWWOCCCO..",
        4: "..OCCCOccccccOOCCCCO..",
        5: "..OCCCOcO..OcOOCCCCO..",
        6: "..OCCCOOWWWWWOOCCCCO..",
        7: "..OCSSSSSSSSSWOWSsO...",
        8: "....OsSSSdOWOOWWSdO....",
        9: ".....OsSSdOdOSSSSDOd..",
    },
    # ---------------- SURF0 / 爸爸：短黑发 + 高额头 + 粗方框眼镜 + 露齿笑 ----------------
    ("SURF0", "dd"): {
        0: "......OOOOOOOOO.......",
        1: "...OOOOOOOOOOOOOOO....",
        2: "..OOOOOOOOOOOOOOOOO...",
        3: "..OsSSSSSSSSSSSSSsO...",
        4: "..OSSSSSSSSSSSSSSSO...",
        5: "..OSsSSSSSSSSSSsO....",
        6: "..OSsOOOOOOsOOOOOSO...",
        7: "..OSsOWWWWOsOWWWOSO...",
        8: "..ODsSSSSSSSSSSdO.....",
        9: ".....OsSSOWWWWOsdDOd..",
    },
    # ---------------- JUMP_AIR / 阳阳（窗口 x10..35；idx≥19 举臂列照抄母版） ----------------
    ("JUMP_AIR", "yy"): {
        0: "......OOOOOOOOOOO..OOOOOO.",
        1: "....OOCCCCCCCCCCCCCOOOOOOOOD",
        2: "..OCCCCCCCCCCCCCCCCCOsOOOD",
        3: "..OCCCOWWWWWWWWWCCCCCOOOOD",
        4: "..OCCCOcOccOccOOCCCCCOOOOD",
        5: "..OCCCOcOccOccOOCCCCCOOOOD",
        6: "..OCCCOWWWWWWWWWCCCCCOOOOD",
        7: "...OCSSWWOOWsOdSSSSSOOOOOD",
        8: "...OCSSsWWWssOdSSSSSOOOOOD",
        9: ".OOODSSSSSSSsOsSSSDOWWOOSS",
        10: ".SSODSSSSSSSsOdOSSDOWW..SS",
        11: ".SSDdSSSSSSSsDsSSSdDWW..SS",
    },
    # ---------------- JUMP_AIR / 爸爸 ----------------
    ("JUMP_AIR", "dd"): {
        0: ".....OOOOOOOOOOOOOOOOOOOO.",
        1: "....OOOOOOOOOOOOOOOOOOOOOD",
        2: "...OOdOOOOOOOOOOOOdOOOOOOOD",
        3: "...OsSSSSSSSSSSSsSDOSSOOOD",
        4: "...OSsSSSSSSSSSSsSDOSSOOOD",
        5: "...OSsSSSSSSSSSSsDdsSSOOOD",
        6: "...OSsOWWWOOWWWOOsSSSOOOD",
        7: ".OOODSSOssOOdssOOSSSOOOOOD",
        8: ".OOODSSSSSSOdSSSSSSSOOOOOD",
        9: ".OOODSSSSSSSsOsSSSDOWWOOSS",
        10: ".SSODSSSSSSSsOWWWODOWW..SS",
        11: ".SSDdSSSSSSSsDdddDdDWW..SS",
    },
}

IDENTITY_NOTES = {
    ("SURF0", "yy"): "儿童：脸部收圆收短(下巴上移)、大眼大镜片；蓝泳帽(C/c两档)+推在帽上的护目镜(W框/c镜片/O瞳)；小开口笑。",
    ("SURF0", "dd"): "成年：短黑发(O/D)+高额头(发际线上移)；深色粗方框眼镜(2px O框/W镜片)；露齿亲切笑(W齿)。",
    ("JUMP_AIR", "yy"): "儿童：脸圆短、大眼带高光；蓝泳帽+帽上护目镜；小鼻+小开口笑。",
    ("JUMP_AIR", "dd"): "成年：短黑发+高额头；深色粗方框眼镜(左右镜圈+鼻梁+镜腿入发)；露齿笑+嘴部阴影。",
}

# ============================================================
# 5. 构建与验证
# ============================================================


def rgba_of(ch: str) -> tuple[int, int, int, int]:
    if ch == ".":
        return (0, 0, 0, 0)
    return (*RGB[ch], 255)


def bbox_of(rows: list[str]) -> list[int] | None:
    xs = [x for row in rows for x, ch in enumerate(row) if ch != "."]
    ys = [y for y, row in enumerate(rows) for x, ch in enumerate(row) if ch != "."]
    if not xs:
        return None
    return [min(xs), min(ys), max(xs), max(ys)]


def build_sprite(pose: str, char: str):
    info = POSES[pose]
    w, h = info["w"], info["h"]
    master = list(info["masterRowsByDir"]["L"])
    if any(len(r) != w for r in master) or len(master) != h:
        fail(f"{pose}: R3A 行尺寸异常")
    neck = NECK_Y[pose]
    region = build_region(pose, master)
    x0 = WIN_X0[pose]

    new = list(master)
    changed: list[list[int]] = []
    alpha_changed = 0
    inside_rgb = 0
    for y, rowstr in EDITS[(pose, char)].items():
        if y >= neck:
            fail(f"{pose}/{char}: 编辑行 y={y} 越入颈部")
        for i, ch in enumerate(rowstr):
            x = x0 + i
            if x >= w:
                fail(f"{pose}/{char}: 编辑列越界 x={x}")
            old = master[y][x]
            if ch == old:
                continue
            if (x, y) not in region:
                fail(f"{pose}/{char}: 修改越出例外区域 ({x},{y})")
            if y == neck - 1 and (old == ".") != (ch == "."):
                fail(f"{pose}/{char}: 颈接行 y={y} 禁止 alpha 变更 ({x},{y})")
            if ch != "." and ch not in SURFACE_KEYS:
                fail(f"{pose}/{char}: 非法颜色 {ch}")
            if ch != "." and char == "dd" and ch in ("C", "c"):
                fail(f"{pose}/{char}: 爸爸禁止使用泳帽蓝")
            row = new[y]
            new[y] = row[:x] + ch + row[x + 1:]
            changed.append([x, y])
            if (old == ".") != (ch == "."):
                alpha_changed += 1
            else:
                inside_rgb += 1

    # ---- 合同验证（显式异常，不用 assert）----
    root_m = info["rootByDir"]["L"]
    bbox_m = info["visibleBBoxByDir"]["L"]
    bbox_n = bbox_of(new)
    if bbox_n is None:
        fail(f"{pose}/{char}: 结果全透明")
    if len(new) != h or any(len(r) != w for r in new):
        fail(f"{pose}/{char}: 尺寸漂移")
    # 区域外 / 颈以下 / alpha 越界 逐项为 0
    outside_rgb = outside_alpha = below_neck = 0
    for y in range(h):
        for x in range(w):
            if master[y][x] == new[y][x]:
                continue
            in_r = (x, y) in region
            if y >= neck:
                below_neck += 1
            if not in_r:
                if (master[y][x] == ".") != (new[y][x] == "."):
                    outside_alpha += 1
                else:
                    outside_rgb += 1
    if below_neck != 0:
        fail(f"{pose}/{char}: 颈部及以下被修改 {below_neck}px")
    if outside_rgb != 0 or outside_alpha != 0:
        fail(f"{pose}/{char}: 区域外差异 rgb={outside_rgb} alpha={outside_alpha}")
    # visibleBBox 不得扩大（允许不变；不允许超出原包围盒）
    if bbox_n[0] < bbox_m[0] or bbox_n[1] < bbox_m[1] or bbox_n[2] > bbox_m[2] or bbox_n[3] > bbox_m[3]:
        fail(f"{pose}/{char}: visibleBBox 扩大 {bbox_m}->{bbox_n}")
    # 头部 alpha 变更只允许 y<=neck-2（行级规则已强制，再次防御）
    for x, y in changed:
        if (master[y][x] == ".") != (new[y][x] == ".") and y > neck - 2:
            fail(f"{pose}/{char}: alpha 变更过深 y={y}")
    if not changed:
        fail(f"{pose}/{char}: 无身份修改，视同复制母版")
    used = sorted({ch for r in new for ch in r if ch != "."})
    if not set(used) <= SURFACE_KEYS:
        fail(f"{pose}/{char}: 调色板外颜色 {used}")

    return {
        "rows": new,
        "region": region,
        "changed": changed,
        "insideRGB": inside_rgb,
        "insideAlpha": alpha_changed,
        "outsideRGB": outside_rgb,
        "outsideAlpha": outside_alpha,
        "belowNeck": below_neck,
        "w": w, "h": h,
        "root": root_m,
        "visibleBBoxMaster": bbox_m,
        "visibleBBox": bbox_n,
        "regionComponents": components(region),
    }


def rows_to_img(rows: list[str]) -> Image.Image:
    img = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            px[x, y] = rgba_of(ch)
    return img


# ============================================================
# 6. 证据图
# ============================================================


def checker_bg(w: int, h: int, cell: int = 4) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for yy in range(0, h, cell):
        for xx in range(0, w, cell):
            c = (204, 204, 204, 255) if ((xx // cell) + (yy // cell)) % 2 == 0 else (236, 236, 236, 255)
            d.rectangle([xx, yy, xx + cell - 1, yy + cell - 1], fill=c)
    return img


def over_checker(rows: list[str], scale: int = 1) -> Image.Image:
    w, h = len(rows[0]), len(rows)
    img = checker_bg(w * scale, h * scale, cell=max(2, 4 * scale // 2))
    sp = rows_to_img(rows)
    if scale > 1:
        sp = sp.resize((w * scale, h * scale), Image.NEAREST)
    img.alpha_composite(sp)
    return img


def mask_img(region: set[tuple[int, int]], w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for x, y in region:
        px[x, y] = (255, 0, 255, 110)
    base = checker_bg(w, h)
    base.alpha_composite(img)
    return base.resize((w * 4, h * 4), Image.NEAREST)


def inside_diff_img(master, new, region, w, h) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            if (x, y) not in region:
                continue
            a, b = master[y][x], new[y][x]
            if a == b:
                continue
            if (a == ".") != (b == "."):
                px[x, y] = (255, 128, 0, 255)   # alpha 增减=橙
            else:
                px[x, y] = (255, 0, 0, 255)     # 换色=红
    base = checker_bg(w, h)
    base.alpha_composite(img)
    return base.resize((w * 4, h * 4), Image.NEAREST)


def outside_proof_img(master, new, region, w, h) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            if (x, y) in region:
                continue
            if master[y][x] != new[y][x]:
                px[x, y] = (255, 0, 0, 255)
    base = checker_bg(w, h)
    base.alpha_composite(img)
    return base.resize((w * 4, h * 4), Image.NEAREST)


def head_neck_zoom(rows: list[str], neck: int, scale: int = 8) -> Image.Image:
    """头颈接口 8x：头部行 + 颈行上下各一行。"""
    w = len(rows[0])
    y0 = 0
    y1 = min(len(rows) - 1, neck + 1)
    crop = [r for r in rows[y0:y1 + 1]]
    img = over_checker(crop, scale)
    d = ImageDraw.Draw(img)
    ny = (neck - y0) * scale
    d.line([(0, ny - 1), (w * scale - 1, ny - 1)], fill=(255, 0, 255, 255), width=1)
    return img


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in ("/System/Library/Fonts/Hiragino Sans GB.ttc",
              "/System/Library/Fonts/STHeiti Light.ttc",
              "/System/Library/Fonts/PingFang.ttc"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ============================================================
# 7. 主流程
# ============================================================


def main() -> None:
    order = [("SURF0", "yy"), ("SURF0", "dd"), ("JUMP_AIR", "yy"), ("JUMP_AIR", "dd")]
    built: dict[tuple[str, str], dict] = {}
    for pose, char in order:
        built[(pose, char)] = build_sprite(pose, char)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    pending: dict[Path, bytes] = {}

    # ---- 4 张原始尺寸透明 PNG ----
    for pose, char in order:
        img = rows_to_img(built[(pose, char)]["rows"])
        pending[OUTDIR / "sprites" / f"{pose}_{char}_L.png"] = _png_bytes(img)

    # ---- 例外区域蒙版 PNG + 区域内差异 + 区域外证明 ----
    for pose, char in order:
        b = built[(pose, char)]
        master = POSES[pose]["masterRowsByDir"]["L"]
        w, h = b["w"], b["h"]
        pending[OUTDIR / "masks" / f"{pose}_{char}_L_headregion.png"] = _png_bytes(mask_img(b["region"], w, h))
        pending[OUTDIR / "diff" / f"{pose}_{char}_L_inside.png"] = _png_bytes(inside_diff_img(master, b["rows"], b["region"], w, h))
        pending[OUTDIR / "diff" / f"{pose}_{char}_L_outside.png"] = _png_bytes(outside_proof_img(master, b["rows"], b["region"], w, h))

    # ---- 机器验证 JSON ----
    def sha_of(rows: list[str]) -> str:
        return hashlib.sha256("".join(rows).encode("utf-8")).hexdigest()

    doc = {
        "schemaVersion": 1,
        "stage": "R3B-I-P1",
        "artifactKind": "likenessValidationSprites",
        "applied": True,
        "scope": {"poses": ["SURF0", "JUMP_AIR"], "dirs": ["L"], "chars": ["yy", "dd"]},
        "inputsSha256": {
            "r3aBakedJs": PINNED[str(F_R3A_JS.relative_to(ROOT))],
            "r3aBuilderPy": PINNED[str(F_R3A_PY.relative_to(ROOT))],
            "stage2AvatarPy": PINNED[str(F_AVATAR.relative_to(ROOT))],
            "r3biOldJson(对照参考,非批准输入)": hashlib.sha256(F_R3BI_JSON.read_bytes()).hexdigest() if F_R3BI_JSON.is_file() else None,
        },
        "headRegionRule": "头部可见包围盒内 且 y<neckY 的像素集合；y==neckY-1 仅允许换色不允许 alpha 增减；y>=neckY 禁改",
        "paletteSurface": {k: list(v) for k, v in RGB.items()},
        "sprites": {},
        "blindOrder": {},
    }
    for pose, char in order:
        b = built[(pose, char)]
        key = f"{pose}_{char}_L"
        doc["sprites"][key] = {
            "w": b["w"], "h": b["h"], "root": b["root"],
            "visibleBBoxMaster": b["visibleBBoxMaster"], "visibleBBox": b["visibleBBox"],
            "visibleBBoxNotExpanded": b["visibleBBox"] == b["visibleBBoxMaster"],
            "rows": b["rows"],
            "headRegion": sorted([list(p) for p in b["region"]]),
            "headRegionPixels": len(b["region"]),
            "regionComponents": b["regionComponents"],
            "changedPixels": b["changed"],
            "changedCount": len(b["changed"]),
            "insideRGB": b["insideRGB"], "insideAlpha": b["insideAlpha"],
            "outsideRGB": b["outsideRGB"], "outsideAlpha": b["outsideAlpha"],
            "belowNeck": b["belowNeck"],
            "usedColors": sorted({ch for r in b["rows"] for ch in r if ch != "."}),
            "contentSha256": sha_of(b["rows"]),
            "identityNote": IDENTITY_NOTES[(pose, char)],
        }

    # ---- 实名对照表（9 栏）----
    pending[OUTDIR / "阶段R3B-I-P1本人特征对照表.png"] = _png_bytes(build_compare_sheet(built, order))

    # ---- 匿名盲审图（固定可复现顺序）----
    blind = ["JUMP_AIR_dd_L", "SURF0_yy_L", "JUMP_AIR_yy_L", "SURF0_dd_L"]  # 定死，可复现
    doc["blindOrder"] = {f"#{i + 1}": blind[i] for i in range(4)}
    pending[OUTDIR / "阶段R3B-I-P1盲审图.png"] = _png_bytes(build_blind_sheet(built, blind))
    pending[OUTDIR / "blind_map.json"] = (json.dumps(doc["blindOrder"], ensure_ascii=False, indent=1) + "\n").encode("utf-8")

    pending[OUTDIR / "likeness_sprites_r3bip1.json"] = (json.dumps(doc, ensure_ascii=False, indent=1) + "\n").encode("utf-8")

    # ---- 主 HTML 范围保护 ----
    for p in pending:
        try:
            p.resolve().relative_to(OUTDIR.resolve())
        except ValueError:
            fail(f"产物路径越出 R3B-I-P1 目录: {p}")
        if p.resolve() == F_MAIN_HTML.resolve():
            fail("禁止写入主HTML")

    # ---- 原子落盘 ----
    for path, data in pending.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_", suffix=".part")
        try:
            with open(fd, "wb") as f:
                f.write(data)
            Path(tmp).replace(path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    print("OK R3B-I-P1 构建完成")
    for pose, char in order:
        b = built[(pose, char)]
        print(f"  {pose}_{char}_L: changed={len(b['changed'])} insideRGB={b['insideRGB']} "
              f"insideAlpha={b['insideAlpha']} outside=0/0 belowNeck=0 comp={b['regionComponents']}")


def _png_bytes(img: Image.Image) -> bytes:
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ============================================================
# 8. 审核图
# ============================================================


def build_compare_sheet(built, order) -> Image.Image:
    font = get_font(15)
    font_s = get_font(12)
    label_w, pad, header_h, margin = 230, 12, 34, 8
    headers = ["母版1x", "旧失败稿1x", "新候选1x", "新候选3x", "新候选8x",
               "例外区域蒙版", "区域内差异", "区域外差异=0", "头颈接口8x"]
    rows_labels = {"SURF0_yy_L": "SURF0 阳阳", "SURF0_dd_L": "SURF0 爸爸",
                   "JUMP_AIR_yy_L": "JUMP_AIR 阳阳", "JUMP_AIR_dd_L": "JUMP_AIR 爸爸"}
    # 先为每行生成 9 个单元图，再按内容最大尺寸排版（只最近邻，不缩放）
    row_cells: list[list[Image.Image]] = []
    for pose, char in order:
        b = built[(pose, char)]
        master = POSES[pose]["masterRowsByDir"]["L"]
        w, h = b["w"], b["h"]
        neck = NECK_Y[pose]
        row_cells.append([
            over_checker(master),                                  # 母版1x
            _png_on_checker(OLD_SPRITES[(pose, char)]),            # 旧失败稿1x
            over_checker(b["rows"]),                               # 新候选1x
            over_checker(b["rows"], 3),
            over_checker(b["rows"], 8),
            mask_img(b["region"], w, h),
            inside_diff_img(master, b["rows"], b["region"], w, h),
            outside_proof_img(master, b["rows"], b["region"], w, h),
            head_neck_zoom(b["rows"], neck, 8),
        ])
    col_w = [max(r[j].width for r in row_cells) + margin for j in range(9)]
    row_h = [max(c.height for c in r) + margin + 24 for r in row_cells]
    total_w = label_w + sum(col_w) + pad
    total_h = header_h + sum(row_h) + pad
    sheet = Image.new("RGB", (total_w, total_h), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    for j, htxt in enumerate(headers):
        d.text((label_w + sum(col_w[:j]) + 4, 10), htxt, fill=(0, 0, 0), font=font_s)
    y = header_h
    for i, (pose, char) in enumerate(order):
        key = f"{pose}_{char}_L"
        b = built[(pose, char)]
        rh = row_h[i]
        d.text((6, y + rh // 2 - 26), rows_labels[key], fill=(0, 0, 0), font=font)
        stats1 = f"改{len(b['changed'])}px 内RGB{b['insideRGB']} 内a{b['insideAlpha']}"
        stats2 = f"外RGB{b['outsideRGB']} 外a{b['outsideAlpha']} 颈{b['belowNeck']}"
        stats3 = f"连通{b['regionComponents']} root{b['root']} 尺寸{b['w']}x{b['h']}"
        d.text((6, y + rh // 2 - 4), stats1, fill=(80, 80, 80), font=font_s)
        d.text((6, y + rh // 2 + 12), stats2, fill=(80, 80, 80), font=font_s)
        d.text((6, y + rh // 2 + 28), stats3, fill=(80, 80, 80), font=font_s)
        x = label_w
        for j, img in enumerate(row_cells[i]):
            sheet.paste(img, (x + 4, y + (rh - img.height) // 2), img)
            d.rectangle([x, y, x + col_w[j] - 1, y + rh - 1], outline=(220, 220, 220))
            x += col_w[j]
        y += rh
    return sheet


def _png_on_checker(path: Path) -> Image.Image:
    """旧稿 PNG 原样叠到棋盘底（仅对照展示，不解析像素语义）。"""
    img = Image.open(path).convert("RGBA")
    base = checker_bg(img.width, img.height)
    base.alpha_composite(img)
    return base


def build_blind_sheet(built, blind: list[str]) -> Image.Image:
    font = get_font(18)
    font_s = get_font(12)
    label_w, pad, header_h, margin = 90, 14, 40, 10
    row_imgs = [[over_checker(built[(key.rsplit('_', 2)[0], key.rsplit('_', 2)[1])]["rows"], sc)
                 for sc in (1, 3, 8)] for key in blind]
    col_w = [max(r[j].width for r in row_imgs) + margin for j in range(3)]
    row_h = [max(c.height for c in r) + margin for r in row_imgs]
    total_w = label_w + sum(col_w) + pad
    total_h = header_h + sum(row_h) + 30
    sheet = Image.new("RGB", (total_w, total_h), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    for j, htxt in enumerate(("1x", "3x", "8x")):
        d.text((label_w + sum(col_w[:j]) + 4, 12), htxt, fill=(0, 0, 0), font=font)
    y = header_h
    for i, key in enumerate(blind):
        rh = row_h[i]
        d.text((10, y + rh // 2 - 10), f"#{i + 1}", fill=(0, 0, 0), font=font)
        x = label_w
        for j, img in enumerate(row_imgs[i]):
            sheet.paste(img, (x + (col_w[j] - img.width) // 2, y + (rh - img.height) // 2), img)
            d.rectangle([x, y, x + col_w[j] - 1, y + rh - 1], outline=(220, 220, 220))
            x += col_w[j]
        y += rh
    d.text((10, total_h - 22), "匿名编号答案见 blind_map.json / 验收记录", fill=(120, 120, 120), font=font_s)
    return sheet


if __name__ == "__main__":
    main()
