#!/usr/bin/env python3
"""R3B-I-P3: preserve the R3B-I bodies, strengthen child/glasses identity.

This is a non-integrated visual candidate.  It reads the exact R3B-I JSON,
changes only already-opaque pixels in the head/face, and proves that dimensions,
root, visible bounds and alpha silhouettes remain unchanged.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE = PROJECT / "过程文件/Kimi开发/R3B-I/identity_sprites_r3bi.json"
SOURCE_SHA256 = "c1da15bb33b72322ff638c4d84ad8257a9223e18bdcd396728464c8e14434839"
SPRITES = HERE / "sprites"

PAL_SURF = {
    "O": (0, 0, 0), "D": (60, 32, 24), "d": (120, 64, 49),
    "s": (180, 96, 73), "S": (241, 129, 98), "W": (241, 242, 241),
    "C": (60, 156, 240), "c": (30, 90, 168),
    "H": (56, 36, 26), "h": (92, 64, 48),
}
PAL_UW = {"u": (0, 64, 88), "m": (60, 188, 252),
          "l": (164, 228, 252), "w": (252, 252, 252)}


def span(x0: int, x1: int, ch: str) -> dict[int, str]:
    return {x: ch for x in range(x0, x1 + 1)}


def merge(*parts: dict[int, str]) -> dict[int, str]:
    out: dict[int, str] = {}
    for part in parts:
        out.update(part)
    return out


# Left-direction changes only. Right direction is mirrored using each sprite's
# real width. Coordinates deliberately stop above the neck/shoulder interface.
PATCH_L: dict[tuple[str, str], dict[int, dict[int, str]]] = {
    ("SURF0", "yy"): {
        # Brighter cap highlight + one large, friendly profile eye + tiny mouth.
        1: merge(span(4, 8, "C"), {9: "W"}),
        7: span(11, 15, "O"),
        8: {8: "s", 11: "O", 12: "W", 13: "O", 14: "W", 15: "O"},
        9: {8: "D", 11: "O", 12: "W", 13: "O", 14: "W", 15: "O"},
    },
    ("SURF0", "dd"): {
        # High-contrast rectangular frame, white lens and visible temple arm.
        7: merge(span(8, 16, "O")),
        8: {8: "O", 9: "O", 10: "O", 11: "O", 12: "W", 13: "O",
            14: "W", 15: "O", 16: "O"},
        9: {11: "O", 12: "W", 13: "O", 14: "W", 15: "O", 16: "O"},
    },
    ("JUMP_AIR", "yy"): {
        # Two readable child eyes. The old huge adult mouth becomes a compact grin.
        7: merge(span(16, 21, "O"), span(28, 32, "O")),
        8: {16: "O", 17: "W", 18: "O", 19: "W", 20: "W", 21: "O",
            28: "O", 29: "W", 30: "O", 31: "W", 32: "O"},
        9: {16: "O", 17: "W", 18: "O", 19: "W", 20: "W", 21: "O",
            28: "O", 29: "W", 30: "O", 31: "W", 32: "O"},
        10: merge(span(16, 21, "O"), span(28, 31, "O")),
        12: {20: "s", 30: "s"},
        14: span(20, 30, "S"),
        15: merge(span(21, 29, "O"), span(24, 26, "W")),
        16: span(21, 29, "O"),
        17: span(20, 30, "S"),
    },
    ("JUMP_AIR", "dd"): {
        # Thick black twin lenses; hair and the original expressive mouth stay put.
        7: merge(span(16, 21, "O"), span(28, 33, "O")),
        8: {16: "O", 17: "W", 18: "O", 19: "W", 20: "W", 21: "O",
            28: "O", 29: "W", 30: "O", 31: "W", 32: "W", 33: "O"},
        9: {16: "O", 17: "W", 18: "O", 19: "W", 20: "W", 21: "O",
            28: "O", 29: "W", 30: "O", 31: "W", 32: "W", 33: "O"},
        10: merge(span(16, 21, "O"), span(28, 31, "O")),
    },
    ("UW_NORMAL", "yy"): {
        # Larger bright goggle lens and a short, childlike mouth mark.
        7: span(21, 24, "u"),
        8: {21: "u", 22: "w", 23: "l", 24: "u"},
        9: {21: "u", 22: "w", 23: "u", 24: "u"},
        10: {21: "m", 22: "m"},
    },
    ("UW_NORMAL", "dd"): {
        # Monochrome underwater glasses: dark temple/frame, white lens reflection.
        7: span(20, 24, "u"),
        8: merge(span(17, 21, "u"), {22: "w", 23: "l", 24: "u"}),
        9: merge(span(18, 21, "u"), {22: "w", 23: "u", 24: "u"}),
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int):
    for path in ("/System/Library/Fonts/PingFang.ttc",
                 "/System/Library/Fonts/Hiragino Sans GB.ttc"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def pal_for(pose: str):
    return PAL_UW if pose == "UW_NORMAL" else PAL_SURF


def mirrored_patch(patch: dict[int, dict[int, str]], width: int):
    return {y: {width - 1 - x: ch for x, ch in cols.items()}
            for y, cols in patch.items()}


def apply_patch_rows(rows: list[str], patch: dict[int, dict[int, str]], label: str):
    out = list(rows)
    changed = []
    for y, cols in patch.items():
        if not 0 <= y < len(out):
            raise SystemExit(f"{label}: y out of range: {y}")
        row = out[y]
        for x, ch in cols.items():
            if not 0 <= x < len(row):
                raise SystemExit(f"{label}: x out of range: {x}")
            if row[x] == ".":
                raise SystemExit(f"{label}: attempted transparent-pixel edit {(x, y)}")
            if ch not in pal_for(label.split('/')[0]):
                raise SystemExit(f"{label}: invalid palette char {ch}")
            if row[x] != ch:
                changed.append((x, y, row[x], ch))
                row = row[:x] + ch + row[x + 1:]
        out[y] = row
    if {(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != "."} != \
       {(x, y) for y, r in enumerate(out) for x, ch in enumerate(r) if ch != "."}:
        raise SystemExit(f"{label}: alpha silhouette changed")
    return out, changed


def rows_image(rows: list[str], pal: dict[str, tuple[int, int, int]]):
    image = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    px = image.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                px[x, y] = pal[ch] + (255,)
    return image


def checker(size: tuple[int, int], cell: int):
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            color = "#34343E" if (x // cell + y // cell) % 2 == 0 else "#262630"
            draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=color)
    return image


def preview(rows: list[str], pal, scale: int):
    sprite = rows_image(rows, pal)
    base = checker(sprite.size, 4)
    base.paste(sprite, (0, 0), sprite)
    return base.resize((base.width * scale, base.height * scale), Image.Resampling.NEAREST)


def review_sheet(source, enhanced):
    width, row_h = 1940, 420
    sheet = Image.new("RGB", (width, 48 + row_h * 6), "#17171D")
    draw = ImageDraw.Draw(sheet)
    draw.text((18, 12), "R3B-I-P3  原体型不变：阳阳儿童化 / 爸爸黑框眼镜（1× + 7×）",
              fill="#F1F2F1", font=font(22))
    headers = ((130, "阳阳·原版"), (560, "阳阳·强化"),
               (990, "爸爸·原版"), (1420, "爸爸·强化"))
    for x, title in headers:
        draw.text((x, 50), title, fill="#F1F2F1", font=font(18))
    row = 0
    for pose in ("SURF0", "JUMP_AIR", "UW_NORMAL"):
        for direction in ("L", "R"):
            y = 78 + row * row_h
            draw.text((18, y + 12), f"{pose} / {direction}", fill="#70C9FF", font=font(17))
            entries = (("yy", source), ("yy", enhanced), ("dd", source), ("dd", enhanced))
            for (x, _), (who, data) in zip(headers, entries):
                rows = data[pose][who][direction]
                pal = pal_for(pose)
                small = preview(rows, pal, 1)
                large = preview(rows, pal, 7)
                sheet.paste(small, (x, y + 38))
                sheet.paste(large, (x, y + 72))
            draw.line((0, y + row_h - 1, width, y + row_h - 1), fill="#3E3E48")
            row += 1
    return sheet


def native_strip(enhanced):
    # Native/3x-only sheet answers whether the identity survives at actual game size.
    width, row_h = 1250, 150
    sheet = Image.new("RGB", (width, 36 + row_h * 3), "#EEF4F6")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "R3B-I-P3 游戏尺寸身份预览", fill="#17202A", font=font(18))
    for i, pose in enumerate(("SURF0", "JUMP_AIR", "UW_NORMAL")):
        y = 36 + i * row_h
        draw.text((12, y + 8), pose, fill="#17202A", font=font(15))
        x = 140
        for who in ("yy", "dd"):
            draw.text((x, y + 8), "阳阳 L / R" if who == "yy" else "爸爸 L / R",
                      fill="#17202A", font=font(13))
            for direction in ("L", "R"):
                rows = enhanced[pose][who][direction]
                one = preview(rows, pal_for(pose), 1)
                three = preview(rows, pal_for(pose), 3)
                sheet.paste(one, (x, y + 36)); x += one.width + 14
                sheet.paste(three, (x, y + 28)); x += three.width + 34
        draw.line((0, y + row_h - 1, width, y + row_h - 1), fill="#BFC9CE")
    return sheet


def png_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, "PNG", optimize=False)
    return buf.getvalue()


def main():
    if not SOURCE.exists() or sha256(SOURCE) != SOURCE_SHA256:
        raise SystemExit("R3B-I-P3 FAIL: source JSON missing or SHA changed")
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    source_rows = {}
    enhanced_rows = {}
    output = {
        "meta": {
            "stage": "R3B-I-P3", "status": "prototype-not-integrated",
            "source": str(SOURCE.relative_to(PROJECT)), "sourceSha256": SOURCE_SHA256,
            "contract": "same w/h/root/visibleBBox/opaque-pixel set; face-color edits only",
        },
        "sprites": {},
    }
    SPRITES.mkdir(parents=True, exist_ok=True)
    for pose in ("SURF0", "JUMP_AIR", "UW_NORMAL"):
        output["sprites"][pose] = {}
        for who in ("yy", "dd"):
            output["sprites"][pose][who] = {}
            for direction in ("L", "R"):
                src = document["sprites"][pose][who][direction]
                rows = src["rows"]
                patch = PATCH_L[(pose, who)]
                if direction == "R":
                    patch = mirrored_patch(patch, src["w"])
                label = f"{pose}/{who}/{direction}"
                new_rows, changed = apply_patch_rows(rows, patch, label)
                if len(new_rows) != src["h"] or any(len(r) != src["w"] for r in new_rows):
                    raise SystemExit(f"{label}: dimensions changed")
                source_rows[(pose, who, direction)] = rows
                enhanced_rows[(pose, who, direction)] = new_rows
                image = rows_image(new_rows, pal_for(pose))
                file = f"{pose}_{who}_{direction}.png"
                data = png_bytes(image)
                (SPRITES / file).write_bytes(data)
                output["sprites"][pose][who][direction] = {
                    "file": f"sprites/{file}", "w": src["w"], "h": src["h"],
                    "root": src["root"], "visibleBBox": src["visibleBBox"],
                    "changedPixelCount": len(changed),
                    "contentSha256": hashlib.sha256(("\n".join(new_rows) + "\n").encode()).hexdigest(),
                    "pngSha256": hashlib.sha256(data).hexdigest(),
                }
    # Convert tuple-key maps to the nested shape used by the sheet helpers.
    src_nested = {p: {w: {d: source_rows[(p, w, d)] for d in ("L", "R")}
                          for w in ("yy", "dd")}
                  for p in ("SURF0", "JUMP_AIR", "UW_NORMAL")}
    out_nested = {p: {w: {d: enhanced_rows[(p, w, d)] for d in ("L", "R")}
                          for w in ("yy", "dd")}
                  for p in ("SURF0", "JUMP_AIR", "UW_NORMAL")}
    (HERE / "identity_enhanced_r3bip3.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "阶段R3B-I-P3身份强化对照表.png").write_bytes(
        png_bytes(review_sheet(src_nested, out_nested)))
    (HERE / "阶段R3B-I-P3游戏尺寸预览.png").write_bytes(
        png_bytes(native_strip(out_nested)))
    print("OK R3B-I-P3 generated 12 enhanced sprites; body/alpha contracts preserved")


if __name__ == "__main__":
    main()
