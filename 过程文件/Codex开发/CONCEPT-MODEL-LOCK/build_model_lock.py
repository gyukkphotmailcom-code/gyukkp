#!/usr/bin/env python3
"""Build the local-only character model lock board from the approved concept art.

The two source concept images are private local references. This script only crops
and arranges their existing pixels; it never redraws or uploads the characters.
"""

import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
HEAD_REF = ROOT / "过程文件/Kimi开发/R3B-I-LikenessTest/阳阳爸爸头像方向参考-本地勿提交.png"
ACTION_REF = ROOT / "过程文件/Codex开发/R3B-I-P2/阳阳爸爸多动作概念参考-本地勿提交.png"
OUT = HERE / "人物模型定档总表-本地勿提交.png"
MANIFEST = HERE / "concept_model_lock_manifest.json"

YY_HEAD_BOX = (540, 25, 1035, 570)
DAD_HEAD_BOX = (185, 585, 700, 1175)
YY_ACTION_BOXES = (
    (55, 90, 470, 410),
    (470, 45, 825, 410),
    (815, 105, 1275, 410),
    (1260, 75, 1715, 410),
)
DAD_ACTION_BOXES = (
    (45, 455, 475, 830),
    (470, 430, 825, 825),
    (815, 480, 1275, 820),
    (1260, 455, 1715, 825),
)

BG = (38, 43, 54)
PANEL = (57, 64, 78)
LINE = (118, 132, 154)
TEXT = (240, 244, 250)
MUTED = (180, 192, 210)
YY = (88, 160, 242)
DAD = (242, 166, 92)


def font(size: int):
    candidates = (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


F_TITLE = font(36)
F_HEAD = font(26)
F_BODY = font(21)
F_SMALL = font(17)


def crop(im: Image.Image, box):
    return im.crop(box)


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_nearest(im: Image.Image, max_w: int, max_h: int):
    scale = min(max_w / im.width, max_h / im.height)
    if scale >= 1:
        factor = max(1, int(scale))
        size = (im.width * factor, im.height * factor)
    else:
        inv = max(1, math.ceil(1 / scale))
        size = (max(1, im.width // inv), max(1, im.height // inv))
    return im.resize(size, Image.Resampling.NEAREST)


def panel(board, xy, size, title, accent, content, note=""):
    x, y = xy
    w, h = size
    d = ImageDraw.Draw(board)
    d.rounded_rectangle((x, y, x + w, y + h), radius=14, fill=PANEL, outline=LINE, width=2)
    d.rectangle((x, y, x + 8, y + h), fill=accent)
    d.text((x + 22, y + 15), title, fill=TEXT, font=F_HEAD)
    if note:
        d.text((x + 22, y + 51), note, fill=MUTED, font=F_SMALL)
    top = y + (80 if note else 58)
    rendered = fit_nearest(content, w - 34, h - (top - y) - 18)
    px = x + (w - rendered.width) // 2
    py = top + (h - (top - y) - rendered.height) // 2
    board.paste(rendered, (px, py))


def main():
    head = Image.open(HEAD_REF).convert("RGB")
    action = Image.open(ACTION_REF).convert("RGB")

    # Canonical head crops from the original concept sheet.
    yy_head = crop(head, YY_HEAD_BOX)
    dad_head = crop(head, DAD_HEAD_BOX)

    # Full-body identity anchors from the original multi-action concept sheet.
    yy_actions = [crop(action, box) for box in YY_ACTION_BOXES]
    dad_actions = [crop(action, box) for box in DAD_ACTION_BOXES]

    board = Image.new("RGB", (2048, 1536), BG)
    d = ImageDraw.Draw(board)
    d.text((64, 42), "阳阳游泳游戏｜人物模型定档 V1", fill=TEXT, font=F_TITLE)
    d.text(
        (64, 91),
        "人物外观唯一来源：现有概念图原像素；后续动作唯一来源：FC原版连续帧",
        fill=MUTED,
        font=F_BODY,
    )
    d.text((64, 128), "本地隐私参考｜禁止提交、上传或嵌入正式游戏", fill=(245, 112, 112), font=F_BODY)

    panel(board, (64, 190), (620, 520), "阳阳｜权威正面头部", YY, yy_head,
          "锁定脸型、眼睛、泳帽、泳镜、耳朵与配色")
    panel(board, (704, 190), (620, 520), "爸爸｜权威正面头部", DAD, dad_head,
          "锁定成年脸、短黑发、高额头、黑框眼镜与笑容")

    # Quick identity contract, kept next to the untouched source crops.
    x = 1344
    y = 190
    w = 640
    h = 520
    d.rounded_rectangle((x, y, x + w, y + h), radius=14, fill=PANEL, outline=LINE, width=2)
    d.text((x + 24, y + 18), "不可变身份合同", fill=TEXT, font=F_HEAD)
    lines = [
        ("阳阳", YY),
        ("儿童圆短脸、大眼黑瞳与高光、小鼻小嘴、可见耳朵", TEXT),
        ("圆顶蓝泳帽、深浅蓝分区、白框双镜片泳镜和镜带", TEXT),
        ("蓝色泳装、紧凑儿童体型、圆润手脚", TEXT),
        ("爸爸", DAD),
        ("成年略长脸、短黑碎发、高额头、两侧收短", TEXT),
        ("黑色粗方框眼镜包眼、可见镜腿、露齿亲切笑", TEXT),
        ("深色泳装、成年体型，整体大于阳阳", TEXT),
        ("共同禁令", (245, 112, 112)),
        ("不得锅盖头、头盔泳帽、方块脸、箱形躯干或线状四肢", TEXT),
        ("不得因动作改变五官比例、发型、泳镜/眼镜和服装结构", TEXT),
    ]
    ty = y + 68
    for line_text, color in lines:
        d.text((x + 28, ty), line_text, fill=color, font=F_SMALL)
        ty += 39 if line_text in {"阳阳", "爸爸", "共同禁令"} else 32

    d.text((64, 748), "全身造型锚点（只锁人物形象与比例，不锁这些动作）", fill=TEXT, font=F_HEAD)
    d.text(
        (64, 714),
        "朝向硬规则：下列横向概念姿态不作为朝向证据；不得把 FC 的正面/斜前朝向改成横向侧身",
        fill=(245, 112, 112),
        font=F_SMALL,
    )
    labels = ("水面", "跳跃", "水下平游", "出水")
    start_y = 800
    cell_w = 470
    gap = 24
    for i, (label, yy_im, dd_im) in enumerate(zip(labels, yy_actions, dad_actions)):
        px = 64 + i * (cell_w + gap)
        combined = Image.new("RGB", (max(yy_im.width, dd_im.width), yy_im.height + dd_im.height), (200, 199, 199))
        combined.paste(yy_im, ((combined.width - yy_im.width) // 2, 0))
        combined.paste(dd_im, ((combined.width - dd_im.width) // 2, yy_im.height))
        panel(board, (px, start_y), (cell_w, 650), label, YY if i % 2 == 0 else DAD, combined,
              "上：阳阳　下：爸爸")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    board.save(OUT, format="PNG")
    manifest = {
        "schemaVersion": 1,
        "stage": "CONCEPT-MODEL-LOCK",
        "reviewState": "user-approved-v1",
        "userApproval": {
            "status": "approved",
            "note": "人物形象可以；后续不得破坏FC原版的非横向朝向",
        },
        "privacy": "local-only; source references and lock board must not be committed or uploaded",
        "identitySourcePriority": "the two existing concept images are the sole visual authority",
        "actionSourcePriority": "FC original continuous frames are the sole authority for pose, phase, timing and pair contact",
        "sources": {
            "headReference": {
                "path": str(HEAD_REF.relative_to(ROOT)),
                "sha256": sha256(HEAD_REF),
                "canonicalCrops": {
                    "yyFrontHead": list(YY_HEAD_BOX),
                    "dadFrontHead": list(DAD_HEAD_BOX),
                },
            },
            "multiActionReference": {
                "path": str(ACTION_REF.relative_to(ROOT)),
                "sha256": sha256(ACTION_REF),
                "labels": ["surface", "jump", "underwaterSwim", "emerge"],
                "yyCrops": [list(box) for box in YY_ACTION_BOXES],
                "dadCrops": [list(box) for box in DAD_ACTION_BOXES],
            },
        },
        "identityContract": {
            "yy": [
                "child with a round short face, large dark eyes with highlights, small nose and mouth, visible ears",
                "rounded blue swim cap with dark/light blue panels and top highlights",
                "complete white-framed two-lens goggles with dark lenses, bridge and strap",
                "blue swimsuit, compact child proportions, rounded hands and feet",
            ],
            "dad": [
                "adult with a slightly longer face and friendly toothy smile",
                "short black textured hair, high forehead and closely tapered sides",
                "thick black rounded-square glasses enclosing the eyes, with visible temples",
                "dark swimsuit and a larger adult build than YY",
            ],
            "forbidden": [
                "helmet or bowl-cut hair",
                "helmet-like swim cap or square goggle panels",
                "box torso, line limbs, generic replacement face",
                "changing identity proportions or costume structure to accommodate an action",
            ],
        },
        "orientationContract": {
            "authority": "FC original frame-by-frame evidence only",
            "rules": [
                "movement direction, body axis, head direction and camera-facing angle are separate values",
                "L/R names are action-direction variants and must not be interpreted as mandatory pure profile views",
                "preserve the front-facing or three-quarter camera orientation visible in each FC source frame",
                "the horizontal poses in the concept sheet lock identity and rendering style only; they are not orientation references",
                "no automatic mirroring when it changes face visibility, near/far limb order, foreshortening or pool perspective",
            ],
            "requiredPerFrameFields": [
                "sourceFrame",
                "movementVector",
                "bodyAxis",
                "bodyYawToCamera",
                "headYawToCamera",
                "nearFarLimbOrder",
                "waterlineOrDepthPlane",
            ],
        },
        "runtimeSizing": {
            "status": "not locked by the model sheet",
            "rule": "do not simplify the locked identity to satisfy a low pixel budget; validate runtime size with the first FC-pose translation",
        },
        "outputs": {
            "localLockBoard": OUT.name,
            "localLockBoardSha256": sha256(OUT),
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    print(MANIFEST)


if __name__ == "__main__":
    main()
