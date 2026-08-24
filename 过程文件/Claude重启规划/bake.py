#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bake.py —— 把概念图流水线产出的 PNG 精灵烘焙进主 HTML 的 SPRITES 段

这是 B0「资产层解耦」的最后一环，解决"单 HTML 双击即玩"与"美术分离开发"的矛盾：
    开发时  sprites/*.png + manifest.json   （分离、可 diff、可重跑）
    交付时  单个 HTML                        （双击就能玩，零依赖）

用法：
    # 1) 先跑流水线生成精灵
    python3 build_sprites_from_concept.py --target-height 40

    # 2) 预览将要注入的 JS（不写文件）
    python3 bake.py --dry-run

    # 3) 真正注入主 HTML（自动备份 .bak）
    python3 bake.py --inject

    # 4) 回退到占位资产
    python3 bake.py --restore-placeholder

注入位置：主 HTML 中
    /* BAKE:SPRITES:BEGIN */ ... /* BAKE:SPRITES:END */
两个标记之间的内容被整段替换。标记之外的玩法代码一个字节都不动
——这正是「换美术时玩法代码零改动」的实现方式。

隐私：sprites/ 含家庭外貌特征，已在 .gitignore。
     注入后的 HTML 同样含这些像素，**不要提交注入后的 HTML**。
     提交前先跑 --restore-placeholder。
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[0]
REPO = ROOT.parents[1]
SPRITES_DIR = ROOT / "sprites"
HTML = REPO / "阳阳水泳大乱斗-原版复刻.html"
# 默认产物：独立的本地美术版。主 HTML 保持占位资产，始终可安全提交。
DEFAULT_LOCAL_OUT = REPO / "阳阳水泳大乱斗-本地美术勿提交.html"

BEGIN = "/* BAKE:SPRITES:BEGIN"
END = "/* BAKE:SPRITES:END */"

# 调色板索引 → 字符。'.' 保留给透明，故排除。
CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# 概念图姿态名 → 游戏动作帧 id 的映射。
# 概念图目前只有 8 个姿态，其余动作继续用占位帧（见《唯一尺寸与画风合同》4.4）。
POSE_TO_FRAMES = {
    "surf":   [("SURF", 0), ("SURF", 1)],
    "jump":   [("JUMP", 0), ("JUMP", 2)],
    "uw":     [("UW", 0), ("UW", 1), ("UWB", 0), ("UWB", 1)],
    "emerge": [("EMERGE", 0), ("UWU", 0)],
}
AVATAR_OF = {"yy": "yy", "dd": "dd"}

# 尚无概念图的动作 → 借用最接近的正式帧。
# 这不是"做完了"，是"占位得体面"：不这样做，40px 的正式帧会和 24px 的旧占位帧同屏，
# 一个人在同一局里忽大忽小、忽而换脸。借用后至少保证全程同一比例、同一张脸。
# 借来的帧仍标 placeholder:true，A3 阶段补画概念图后逐个替换。
ALIAS = {
    ("DIVE", 0): ("UW", 0), ("DIVE", 1): ("UW", 1), ("DIVE", 2): ("UW", 0),
    ("UWD", 0): ("UW", 0),
    ("JUMP", 1): ("JUMP", 0),
    ("BREATH", 0): ("SURF", 0), ("BREATH", 1): ("EMERGE", 0),
    ("BREATH", 2): ("EMERGE", 0), ("BREATH", 3): ("SURF", 1),
    ("KICK", 0): ("UWB", 0), ("KICK", 1): ("UWB", 1),
    ("HIT", 0): ("UW", 1), ("HIT", 1): ("UW", 0),
    ("DROWN", 0): ("UW", 0), ("DROWN", 1): ("UW", 1),
    ("LOSE", 0): ("SURF", 0), ("LOSE", 1): ("SURF", 1),
    ("GRAPPLE", 0): ("EMERGE", 0), ("GRAPPLE", 1): ("SURF", 0),
    ("GRAPPLE_STRUGGLE", 0): ("SURF", 1), ("GRAPPLE_STRUGGLE", 1): ("EMERGE", 0),
    ("GRAPPLE_PUNCH", 0): ("EMERGE", 0), ("GRAPPLE_PUNCH", 1): ("SURF", 0),
    ("MOUNT", 0): ("JUMP", 0), ("MOUNT", 1): ("JUMP", 2),
    ("MOUNTED", 0): ("SURF", 0), ("MOUNTED", 1): ("SURF", 1),
    ("LEGPULL", 0): ("UW", 0), ("LEGPULL", 1): ("UWB", 0),
    ("LEGPULLED", 0): ("UW", 1), ("LEGPULLED", 1): ("UW", 0),
}


def quantize_to_charset(rgba: np.ndarray, palette_hex):
    """RGBA 数组 → 字符网格。颜色必须已在调色板内（流水线保证）。"""
    lut = {}
    for i, hx in enumerate(palette_hex):
        rgb = (int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16))
        lut[rgb] = CHARSET[i]
    rows = []
    unknown = set()
    for r in range(rgba.shape[0]):
        line = []
        for q in range(rgba.shape[1]):
            px = rgba[r, q]
            if px[3] == 0:
                line.append(".")
                continue
            key = (int(px[0]), int(px[1]), int(px[2]))
            ch = lut.get(key)
            if ch is None:
                unknown.add(key)
                ch = CHARSET[0]
            line.append(ch)
        rows.append("".join(line))
    return rows, unknown


def bbox_of(rows):
    x0, y0, x1, y1 = 10**9, 10**9, -1, -1
    for r, line in enumerate(rows):
        for q, ch in enumerate(line):
            if ch == ".":
                continue
            x0, x1 = min(x0, q), max(x1, q)
            y0, y1 = min(y0, r), max(y1, r)
    if x1 < 0:
        return None
    return {"x": x0, "y": y0, "w": x1 - x0 + 1, "h": y1 - y0 + 1}


def mirror(rows):
    return [line[::-1] for line in rows]


def build_js():
    manifest_path = SPRITES_DIR / "manifest.json"
    if not manifest_path.exists():
        sys.exit(
            f"找不到 {manifest_path}\n"
            "请先运行：python3 build_sprites_from_concept.py --target-height 40"
        )
    man = json.loads(manifest_path.read_text(encoding="utf-8"))
    palette = man["palette"]
    if len(palette) > len(CHARSET):
        sys.exit(f"调色板 {len(palette)} 色超过字符集容量 {len(CHARSET)}")

    frames = {}
    all_unknown = set()
    covered = []
    for name, meta in man["sprites"].items():
        avatar_key, pose = name.split("_", 1)
        avatar = AVATAR_OF.get(avatar_key)
        targets = POSE_TO_FRAMES.get(pose)
        if avatar is None or targets is None:
            print(f"  跳过 {name}（没有对应的游戏动作）")
            continue

        img = Image.open(SPRITES_DIR / meta["file"]).convert("RGBA")
        rows_r, unknown = quantize_to_charset(np.asarray(img), palette)
        all_unknown |= unknown
        rows_l = mirror(rows_r)

        # 世界锚点：直立姿态用脚底中心，横游姿态用身体中心。
        # 与占位帧共用同一套锚点语义，玩法代码不需要知道换过美术。
        anchor_x = meta["cx"]
        anchor_y = meta["footY"] + 1

        for action, idx in targets:
            for dir_ch, rows in (("R", rows_r), ("L", rows_l)):
                ax = anchor_x if dir_ch == "R" else (img.width - 1 - anchor_x)
                frames[f"{avatar}.{action}.{dir_ch}.{idx}"] = {
                    "w": img.width,
                    "h": img.height,
                    "anchorX": ax,
                    "anchorY": anchor_y,
                    "rows": rows,
                    "bbox": bbox_of(rows),
                    "hurtbox": None,   # hitbox/hurtbox 由主 HTML 的 attachBoxes() 按动作/相位注入
                    "hitbox": None,
                    "placeholder": False,
                    "pal": True,   # 用共享调色板着色，占位符在 JS 里展开
                }
            covered.append(f"{avatar}.{action}.{idx}")

    if all_unknown:
        print(f"  警告：{len(all_unknown)} 个像素颜色不在 manifest 调色板内（已就近归零）")

    # 借用步骤：把还没有概念图的动作指向最接近的正式帧，避免 40px/24px 混排
    aliased = []
    for (action, idx), (src_action, src_idx) in ALIAS.items():
        for avatar in ("yy", "dd"):
            for dir_ch in ("R", "L"):
                src = frames.get(f"{avatar}.{src_action}.{dir_ch}.{src_idx}")
                if src is None:
                    continue
                f = dict(src)
                f["placeholder"] = True          # 仍是占位, 只是借了正式像素
                f["aliasOf"] = f"{src_action}.{src_idx}"
                frames[f"{avatar}.{action}.{dir_ch}.{idx}"] = f
                aliased.append(f"{avatar}.{action}.{idx}")
    print(f"借用帧：{len(aliased)} 个（仍标 placeholder，A3 补画后替换）")

    pal_js = "{" + ",".join(
        f'"{CHARSET[i]}":"{hx}"' for i, hx in enumerate(palette)
    ) + "}"

    lines = [
        "/* 以下由 bake.py 自动生成，请勿手工编辑。",
        f"   来源：{man['source']}  sha256={man['sourceSha256'][:16]}…",
        f"   目标身高：阳阳 {man['targetHeight']['yy']}px / 爸爸 {man['targetHeight']['dd']}px",
        f"   正式帧 {len(frames)} 张，其余动作仍用占位帧。*/",
        "bakeFrames();                       // 先铺满占位帧",
        f"const BAKED_PAL = {pal_js};",
        "const BAKED = " + json.dumps(frames, ensure_ascii=False, separators=(",", ":")) + ";",
        "for (const id in BAKED){ const f = BAKED[id]; f.pal = BAKED_PAL; SPRITES.frames[id] = f; }",
        f"SPRITES.meta.source = 'concept-pipe-1';",
        f"SPRITES.meta.yyHeight = {man['targetHeight']['yy']};",
        f"SPRITES.meta.ddHeight = {man['targetHeight']['dd']};",
    ]
    return "\n".join(lines), sorted(set(covered))


def replace_region(html: str, body: str) -> str:
    pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END), re.S
    )
    if not pattern.search(html):
        sys.exit(f"主 HTML 里找不到 {BEGIN} … {END} 标记段")
    marker = BEGIN + " —— 本段由 bake.py 整段替换, 手工编辑会在下次 bake 时丢失 */\n"
    return pattern.sub(lambda _: marker + body + "\n" + END, html)


PLACEHOLDER_BODY = (
    "bakeFrames();                       "
    "// 占位资产: 由阶段2/3已验收像素合成, 全部 placeholder:true"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只打印将注入的 JS")
    ap.add_argument("--inject", action="store_true", help="写入主 HTML（自动备份 .bak）")
    ap.add_argument("--restore-placeholder", action="store_true", help="回退到占位资产")
    ap.add_argument(
        "--out",
        nargs="?",
        const=str(DEFAULT_LOCAL_OUT),
        default=None,
        help="生成一份独立的本地美术 HTML，不改主 HTML（默认文件名已在 .gitignore）",
    )
    args = ap.parse_args()

    if not HTML.exists():
        sys.exit(f"找不到主 HTML：{HTML}")

    if args.restore_placeholder:
        html = HTML.read_text(encoding="utf-8")
        shutil.copy2(HTML, HTML.with_suffix(".html.bak"))
        HTML.write_text(replace_region(html, PLACEHOLDER_BODY), encoding="utf-8")
        print("已回退到占位资产（备份 .html.bak）")
        return

    body, covered = build_js()
    print(f"正式帧覆盖：{len(covered)} 个动作帧")
    for c in covered:
        print(f"  {c}")

    if args.out:
        out = Path(args.out)
        html = HTML.read_text(encoding="utf-8")
        out.write_text(replace_region(html, body), encoding="utf-8")
        print(f"\n已生成本地美术版：{out}")
        print("主 HTML 未改动（仍是占位资产，可安全提交）。")
        return

    if args.dry_run or not args.inject:
        print("\n---- 将注入的 JS（前 40 行）----")
        for line in body.splitlines()[:40]:
            print(line[:160])
        if not args.inject:
            print("\n（未写入。用 --out 生成本地美术版，或 --inject 直接改主 HTML）")
        return

    html = HTML.read_text(encoding="utf-8")
    shutil.copy2(HTML, HTML.with_suffix(".html.bak"))
    HTML.write_text(replace_region(html, body), encoding="utf-8")
    print(f"\n已注入 {HTML}（备份 .html.bak）")
    print("提醒：注入后的 HTML 含家庭外貌特征，提交前请先 --restore-placeholder")


if __name__ == "__main__":
    main()
