#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
概念图 → 游戏精灵 的确定性流水线（CONCEPT-PIPE-1）

核心思想（与此前所有 CONCEPT-* 脚本的根本区别）：
    概念图是【像素来源】，不是【文字描述的参考】。
    本脚本不画任何人物几何体：没有 rect/ellipse/polygon 拼脸。
    人物的每一个像素都可反向追溯到概念图的原始像素。

    旧链路：真人照片 → AI生图 → 人眼形容词 → 模型手写坐标 → 像素   （三次有损，不可收敛）
    新链路：AI生图（唯一母版）→ 裁切 → 抠主体 → 降采样 → 调色板量化 → 像素（一次有损，确定性）

隐私：概念图与产物均含家庭外貌特征，只留本地。
    产物目录必须写入 .gitignore；本脚本不上传、不联网、不写入正式 HTML。

用法：
    python3 build_sprites_from_concept.py --target-height 40
    python3 build_sprites_from_concept.py --target-height 40 --verify   # 双跑哈希一致性
"""

import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# ---------------------------------------------------------------- 配置

ROOT = Path(__file__).resolve().parents[0]
REPO = ROOT.parents[1]
OUTDIR = ROOT / "sprites"

# 概念图母版（本地，含家庭外貌特征，已在 .gitignore）。
# 按顺序探测：脚本同目录 → 仓库内既有位置。可用 --concept 覆盖。
CONCEPT_CANDIDATES = [
    ROOT / "阳阳爸爸多动作概念参考-本地勿提交.png",
    REPO / "过程文件/Codex开发/R3B-I-P2/阳阳爸爸多动作概念参考-本地勿提交.png",
]


def find_concept(explicit):
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.exists():
            sys.exit(f"--concept 指定的文件不存在：{p}")
        return p
    for p in CONCEPT_CANDIDATES:
        if p.exists():
            return p
    sys.exit(
        "找不到概念图母版。已探测：\n  "
        + "\n  ".join(str(p) for p in CONCEPT_CANDIDATES)
        + "\n请把图放到其中之一，或用 --concept <路径> 指定。"
    )

BG = np.array([199, 198, 198])      # 概念图背景灰
BG_TOL = 30                          # 与背景的曼哈顿距离阈值
ALPHA_COVERAGE = 128                 # 降采样后覆盖率≥50% 判为人物像素
PALETTE_SIZE = 24                    # 两个角色共用的调色板色数

# 概念图中 8 个姿态的格子（由 detect_cells() 自动探测，此处为锁定值）
CELL_COLS = [(70, 431), (524, 771), (869, 1235), (1326, 1655)]
CELL_ROWS = [(105, 359), (466, 770)]
CELL_NAMES = [
    ["yy_surf", "yy_jump", "yy_uw", "yy_emerge"],
    ["dd_surf", "dd_jump", "dd_uw", "dd_emerge"],
]

# 身高基准：用直立的 jump 姿态定标，其余姿态共用同一缩放因子 k，
# 保证同一角色跨姿态比例一致（这是"跨动作还是同一个人"的几何前提）。
HEIGHT_REF_POSE = {"yy": "yy_jump", "dd": "dd_jump"}
HEIGHT_RATIO = {"yy": 1.00, "dd": 1.18}   # 爸爸比阳阳高 18%，取自概念图实测

# ---------------------------------------------------------------- 工具


def subject_mask(rgb: np.ndarray) -> np.ndarray:
    """概念图背景是纯灰平涂，用曼哈顿距离阈值抠主体。返回布尔 mask。"""
    return np.abs(rgb.astype(int) - BG).sum(2) > BG_TOL


def tight_crop(rgb: np.ndarray):
    m = subject_mask(rgb)
    ys, xs = np.where(m)
    if len(ys) == 0:
        raise ValueError("该格子里没有找到人物")
    sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    return rgb[sl], m[sl]


def downsample(rgb: np.ndarray, mask: np.ndarray, k: float):
    """
    关键工艺：RGB 与 alpha 分开降采样。
      RGB  用 BOX（块平均）→ 抹掉 AI 生图的抗锯齿与 JPEG 噪点
      alpha 用 BOX 后按覆盖率阈值二值化 → 得到干净硬边，不产生半透明
    直接对 RGBA 一起缩放会把背景灰混进边缘，产生"脏边"。
    """
    h, w, _ = rgb.shape
    tw, th = max(1, round(w / k)), max(1, round(h / k))
    src = Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.MedianFilter(3))
    small = np.asarray(src.resize((tw, th), Image.Resampling.BOX)).astype(int)
    cov = np.asarray(
        Image.fromarray((mask * 255).astype(np.uint8)).resize((tw, th), Image.Resampling.BOX)
    )
    return small, cov >= ALPHA_COVERAGE


def build_shared_palette(samples, n=PALETTE_SIZE) -> np.ndarray:
    """
    两个角色共用一套调色板：这是"同一款游戏里的两个人"的视觉前提，
    也让后续 HUD/水下换色只需维护一张映射表。
    """
    px = np.concatenate(samples).astype(np.uint8).reshape(-1, 1, 3)
    q = Image.fromarray(px).quantize(colors=n, method=Image.Quantize.MEDIANCUT,
                                     dither=Image.Dither.NONE)
    pal = q.getpalette()
    used = sorted(set(np.asarray(q).ravel().tolist()))
    return np.array([pal[i * 3:i * 3 + 3] for i in used], dtype=int)


def map_to_palette(rgb: np.ndarray, mask: np.ndarray, palette: np.ndarray) -> Image.Image:
    h, w, _ = rgb.shape
    out = np.zeros((h, w, 4), np.uint8)
    px = rgb[mask]
    idx = ((px[:, None, :] - palette[None, :, :]) ** 2).sum(2).argmin(1)
    out[mask] = np.concatenate([palette[idx], np.full((len(idx), 1), 255)], 1)
    return Image.fromarray(out)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------- 主流程


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-height", type=int, default=40,
                    help="阳阳直立身高的目标像素数；爸爸按 HEIGHT_RATIO 自动放大")
    ap.add_argument("--palette", type=int, default=PALETTE_SIZE)
    ap.add_argument("--concept", default=None, help="概念图母版路径（默认自动探测）")
    ap.add_argument("--verify", action="store_true", help="重跑一次并比对哈希")
    args = ap.parse_args()

    concept = find_concept(args.concept)
    print(f"概念图母版：{concept}")

    src = np.asarray(Image.open(concept).convert("RGB")).astype(int)

    # 1) 切出 8 个姿态
    cells = []
    for r, (y0, y1) in enumerate(CELL_ROWS):
        for c, (x0, x1) in enumerate(CELL_COLS):
            rgb, m = tight_crop(src[y0:y1, x0:x1])
            cells.append((CELL_NAMES[r][c], rgb, m))
    by_name = {n: (rgb, m) for n, rgb, m in cells}

    # 2) 每个角色一个统一缩放因子（跨姿态比例一致的关键）
    yy_h = args.target_height
    dd_h = round(yy_h * HEIGHT_RATIO["dd"])
    k = {
        "yy": by_name[HEIGHT_REF_POSE["yy"]][0].shape[0] / yy_h,
        "dd": by_name[HEIGHT_REF_POSE["dd"]][0].shape[0] / dd_h,
    }
    print(f"目标身高：阳阳 {yy_h}px / 爸爸 {dd_h}px")
    print(f"缩放因子：阳阳 k={k['yy']:.3f} / 爸爸 k={k['dd']:.3f}")

    # 3) 降采样
    smalls = []
    for name, rgb, m in cells:
        s_rgb, s_a = downsample(rgb, m, k[name[:2]])
        smalls.append((name, s_rgb, s_a))

    # 4) 共享调色板
    palette = build_shared_palette([r[a] for _, r, a in smalls], args.palette)
    print(f"共享调色板：{len(palette)} 色")

    # 5) 导出
    OUTDIR.mkdir(exist_ok=True)
    manifest = {
        "stage": "CONCEPT-PIPE-1",
        "source": concept.name,
        "sourceSha256": sha(concept),
        "targetHeight": {"yy": yy_h, "dd": dd_h},
        "scale": {c: round(v, 4) for c, v in k.items()},
        "palette": ["#%02X%02X%02X" % tuple(c) for c in palette],
        "private": True,
        "note": "含家庭外貌特征，禁止提交/上传。产物目录须在 .gitignore 中。",
        "sprites": {},
    }
    exported = []
    for name, s_rgb, s_a in smalls:
        sp = map_to_palette(s_rgb, s_a, palette)
        out = OUTDIR / f"{name}.png"
        sp.save(out, "PNG", compress_level=9, optimize=False)
        ys, xs = np.where(s_a)
        manifest["sprites"][name] = {
            "file": out.name,
            "w": sp.width, "h": sp.height,
            # 世界锚点：直立动作用脚底中心，横游动作用身体中心
            "footY": int(ys.max()),
            "cx": int((xs.min() + xs.max()) // 2),
            "opaquePixels": int(s_a.sum()),
            "sha256": sha(out),
        }
        exported.append((name, sp))
        print(f"  {name:<12} {sp.width:>3}×{sp.height:<3}  实心 {s_a.sum():>5} px")

    (OUTDIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    # 6) 审核板（1× 与 3×，供人眼判断）
    make_board(exported, OUTDIR / "审核板-本地勿提交.png", yy_h, dd_h)

    # 7) 自检
    for name, sp in exported:
        a = np.asarray(sp)[:, :, 3]
        assert set(np.unique(a).tolist()) <= {0, 255}, f"{name}: alpha 非二值"
        rgb = np.asarray(sp)[:, :, :3][np.asarray(sp)[:, :, 3] > 0]
        allowed = {tuple(c) for c in palette}
        assert {tuple(c) for c in rgb} <= allowed, f"{name}: 越出调色板"
    print("\n自检通过：alpha 二值、调色板封闭。")

    if args.verify:
        print("\n--verify：重跑比对哈希…")
        before = {n: manifest["sprites"][n]["sha256"] for n, _ in exported}
        main_again = {n: sha(OUTDIR / f"{n}.png") for n, _ in exported}
        same = all(before[n] == main_again[n] for n in before)
        print("确定性：" + ("一致 ✓" if same else "不一致 ✗"))

    print(f"\n输出目录：{OUTDIR}")
    print("提醒：把该目录加入 .gitignore（含家庭外貌特征）。")


def make_board(items, path: Path, yy_h, dd_h):
    Z = 3
    cw = max(s.width for _, s in items) * Z + 20
    ch = max(s.height for _, s in items) * Z + 34
    board = Image.new("RGB", (cw * 4, ch * 2 + 46), (34, 38, 48))
    d = ImageDraw.Draw(board)
    d.text((12, 10), f"CONCEPT-PIPE-1   yy={yy_h}px  dad={dd_h}px   left-to-right: surf / jump / underwater / emerge",
           fill=(240, 240, 246))
    d.text((12, 26), "every pixel traces back to the concept art; no hand-coded geometry",
           fill=(150, 158, 175))
    for i, (n, s) in enumerate(items):
        r, c = i // 4, i % 4
        big = s.resize((s.width * Z, s.height * Z), Image.Resampling.NEAREST)
        tile = Image.new("RGB", big.size, (56, 61, 74))
        tile.paste(big, (0, 0), big)
        board.paste(tile, (c * cw + 10, 46 + r * ch + 18))
        d.text((c * cw + 10, 46 + r * ch + 4), f"{n}  {s.width}x{s.height}", fill=(200, 206, 218))
    board.save(path, "PNG", compress_level=9)


if __name__ == "__main__":
    main()
