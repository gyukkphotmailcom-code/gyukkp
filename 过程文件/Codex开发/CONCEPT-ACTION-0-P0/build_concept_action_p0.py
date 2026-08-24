#!/usr/bin/env python3
"""Deterministic local builder for CONCEPT-ACTION-0-P0.

The six sprites are original, code-authored pixel drawings.  They use the
approved concept-model identity contract and the pose/orientation readings of
the three locked FC stills.  No image is uploaded and no Kimi failed draft is
read.  Private concept/FC crops are used only for an optional ignored review
board; the formal sprites do not depend on their pixels.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
LOCAL = HERE / "本地勿提交"
MANIFEST = HERE / "concept_action_p0_manifest.json"

FORMAL_HTML = ROOT / "阳阳水泳大乱斗-原版复刻.html"
FORMAL_HTML_SHA256 = "412416e95bfe4c98f4b039dc4a24fd9b28c2c23989254f22ee494d2e7bcde306"

FC_SOURCES = {
    "SURF0": ROOT / "过程文件/原版参考/官方截图/jp-action-e.gif",
    "JUMP_AIR": ROOT / "过程文件/原版参考/官方截图/jp-action-c.gif",
    "UW_NORMAL": ROOT / "过程文件/原版参考/官方截图/jp-action-b.gif",
}
FC_CROPS = {
    "SURF0": (105, 88, 136, 109),
    "JUMP_AIR": (73, 35, 128, 77),
    "UW_NORMAL": (99, 141, 138, 162),
}

HEAD_REF = ROOT / "过程文件/Kimi开发/R3B-I-LikenessTest/阳阳爸爸头像方向参考-本地勿提交.png"
ACTION_REF = ROOT / "过程文件/Codex开发/R3B-I-P2/阳阳爸爸多动作概念参考-本地勿提交.png"
HEAD_CROPS = {"yy": (540, 25, 1035, 570), "dad": (185, 585, 700, 1175)}
ACTION_CROPS = {"yy": (470, 45, 825, 410), "dad": (470, 430, 825, 825)}

# Fixed sprite palette.  Alpha is always 0 or 255.
PAL = {
    "outline": (18, 24, 34, 255),
    "outline_soft": (43, 43, 50, 255),
    "skin_shadow": (196, 91, 39, 255),
    "skin": (255, 166, 83, 255),
    "skin_light": (255, 205, 132, 255),
    "cheek": (238, 112, 64, 255),
    "white": (255, 248, 226, 255),
    "lens": (38, 93, 139, 255),
    "eye": (25, 25, 29, 255),
    "blue_dark": (18, 76, 145, 255),
    "blue": (34, 132, 222, 255),
    "blue_light": (92, 190, 246, 255),
    "blue_glint": (174, 232, 255, 255),
    "hair": (12, 15, 20, 255),
    "hair_light": (48, 46, 44, 255),
    "suit_dark": (25, 30, 40, 255),
    "suit_mid": (49, 56, 69, 255),
}


def rgba(name: str):
    return PAL[name]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int):
    for candidate in (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def box(cx, cy, w, h):
    return (round(cx - w / 2), round(cy - h / 2), round(cx + w / 2), round(cy + h / 2))


def disc(draw, cx, cy, r, fill):
    draw.ellipse(box(cx, cy, r * 2, r * 2), fill=fill)


def volume_limb(draw, points, width, fill, end_r=None):
    """A filled, outlined limb with joint volume (never a one-pixel line)."""
    outline_w = width + 5
    draw.line(points, fill=rgba("outline"), width=outline_w, joint="curve")
    for x, y in points:
        disc(draw, x, y, outline_w // 2, rgba("outline"))
    draw.line(points, fill=fill, width=width, joint="curve")
    for x, y in points:
        disc(draw, x, y, width // 2, fill)
    if end_r:
        ex, ey = points[-1]
        disc(draw, ex, ey, end_r + 2, rgba("outline"))
        disc(draw, ex, ey, end_r, fill)


def fist_detail(draw, x, y, direction="right"):
    """Break a circular primitive into a readable pixel fist/hand."""
    if direction == "right":
        draw.rectangle((x+1,y-3,x+4,y-2),fill=rgba("skin_light"))
        draw.rectangle((x+2,y+2,x+5,y+3),fill=rgba("skin_shadow"))
        draw.rectangle((x-3,y+4,x+1,y+5),fill=rgba("outline"))
    elif direction == "left":
        draw.rectangle((x-4,y-3,x-1,y-2),fill=rgba("skin_light"))
        draw.rectangle((x-5,y+2,x-2,y+3),fill=rgba("skin_shadow"))
        draw.rectangle((x-1,y+4,x+3,y+5),fill=rgba("outline"))
    else:
        draw.rectangle((x-3,y-4,x+1,y-3),fill=rgba("skin_light"))
        draw.rectangle((x+2,y-1,x+3,y+3),fill=rgba("skin_shadow"))


def foot_detail(draw, x, y, direction="down"):
    draw.rectangle((x-3,y-3,x+1,y-2),fill=rgba("skin_light"))
    if direction == "down":
        draw.rectangle((x-4,y+3,x+3,y+5),fill=rgba("skin_shadow"))
        draw.rectangle((x-1,y+5,x+4,y+6),fill=rgba("outline"))
    else:
        draw.rectangle((x+2,y+1,x+5,y+3),fill=rgba("skin_shadow"))


def yy_head(draw, cx, cy, s=1.0, yaw="front"):
    """Approved YY identity, kept front/three-quarter rather than profile."""
    q = lambda v: round(v * s)
    face_shift = {"front-left": -2, "front": 0, "front-right": 2}[yaw]

    # Ears sit behind the face and preserve the child silhouette.
    disc(draw, cx - q(17), cy + q(3), q(5), rgba("outline"))
    disc(draw, cx + q(17), cy + q(3), q(5), rgba("outline"))
    disc(draw, cx - q(17), cy + q(3), q(3), rgba("skin"))
    disc(draw, cx + q(17), cy + q(3), q(3), rgba("skin"))

    face = [
        (cx - q(15), cy - q(9)), (cx - q(17), cy + q(3)),
        (cx - q(13), cy + q(14)), (cx - q(6), cy + q(19)),
        (cx + q(5), cy + q(19)), (cx + q(13), cy + q(13)),
        (cx + q(17), cy + q(3)), (cx + q(15), cy - q(9)),
    ]
    draw.polygon(face, fill=rgba("outline"))
    inner = [
        (cx - q(12), cy - q(8)), (cx - q(14), cy + q(3)),
        (cx - q(10), cy + q(12)), (cx - q(5), cy + q(16)),
        (cx + q(5), cy + q(16)), (cx + q(10), cy + q(11)),
        (cx + q(14), cy + q(2)), (cx + q(12), cy - q(8)),
    ]
    draw.polygon(inner, fill=rgba("skin"))
    draw.polygon([(cx-q(10),cy+q(8)),(cx,cy+q(15)),(cx+q(8),cy+q(9))], fill=rgba("skin_light"))

    # Rounded multi-panel cap with a non-square crown and small highlight.
    cap_outer = [
        (cx-q(16),cy-q(8)), (cx-q(13),cy-q(17)), (cx-q(6),cy-q(23)),
        (cx+q(4),cy-q(24)), (cx+q(12),cy-q(19)), (cx+q(17),cy-q(10)),
        (cx+q(15),cy-q(5)), (cx-q(15),cy-q(5)),
    ]
    draw.polygon(cap_outer, fill=rgba("outline"))
    cap_inner = [
        (cx-q(13),cy-q(9)), (cx-q(10),cy-q(16)), (cx-q(4),cy-q(20)),
        (cx+q(4),cy-q(21)), (cx+q(10),cy-q(17)), (cx+q(14),cy-q(9)),
        (cx+q(12),cy-q(7)), (cx-q(12),cy-q(7)),
    ]
    draw.polygon(cap_inner, fill=rgba("blue"))
    draw.polygon([(cx-q(11),cy-q(15)),(cx-q(4),cy-q(20)),(cx-q(2),cy-q(7)),(cx-q(10),cy-q(8))], fill=rgba("blue_light"))
    draw.polygon([(cx+q(5),cy-q(20)),(cx+q(10),cy-q(17)),(cx+q(12),cy-q(8)),(cx+q(4),cy-q(8))], fill=rgba("blue_dark"))
    draw.rectangle((cx-q(6),cy-q(19),cx+q(2),cy-q(17)), fill=rgba("blue_glint"))

    # Complete two-lens white goggles rest on the cap, as on the approved
    # full-body concept anchors.  The large child eyes remain unobstructed.
    gy = cy - q(12)
    draw.rectangle((cx-q(17),gy-q(3),cx-q(13),gy+q(3)), fill=rgba("white"))
    draw.rectangle((cx+q(13),gy-q(3),cx+q(17),gy+q(3)), fill=rgba("white"))
    for lx in (cx-q(7)+q(face_shift), cx+q(7)+q(face_shift)):
        draw.rounded_rectangle(box(lx, gy, q(12), q(9)), radius=max(1,q(2)), fill=rgba("outline"))
        draw.rounded_rectangle(box(lx, gy, q(8), q(5)), radius=max(1,q(1)), fill=rgba("lens"))
        draw.rectangle((lx-q(2),gy-q(2),lx+q(1),gy), fill=rgba("blue_glint"))
    draw.rectangle((cx-q(2)+q(face_shift),gy-q(1),cx+q(2)+q(face_shift),gy+q(1)), fill=rgba("white"))

    # Large concept-model eyes with white highlights, then small nose/mouth.
    ey = cy - q(2)
    for ex in (cx-q(7)+q(face_shift),cx+q(7)+q(face_shift)):
        draw.rectangle((ex-q(3),ey-q(3),ex+q(3),ey+q(4)),fill=rgba("white"))
        draw.rectangle((ex-q(1)+q(face_shift/2),ey-q(2),ex+q(2)+q(face_shift/2),ey+q(3)),fill=rgba("eye"))
        draw.point((ex+q(face_shift/2),ey-q(2)),fill=rgba("white"))
    draw.rectangle((cx+q(face_shift)-1, cy+q(5), cx+q(face_shift)+1, cy+q(7)), fill=rgba("skin_shadow"))
    draw.rectangle((cx+q(face_shift)-q(4), cy+q(11), cx+q(face_shift)+q(4), cy+q(13)), fill=rgba("outline"))
    draw.rectangle((cx+q(face_shift)-q(2), cy+q(11), cx+q(face_shift)+q(2), cy+q(11)), fill=rgba("white"))
    draw.rectangle((cx-q(12),cy+q(8),cx-q(10),cy+q(9)), fill=rgba("cheek"))


def dad_head(draw, cx, cy, s=1.0, yaw="front"):
    """Approved Dad identity: high forehead, tapered textured hair, black glasses."""
    q = lambda v: round(v * s)
    face_shift = {"front-left": -2, "front": 0, "front-right": 2}[yaw]

    disc(draw, cx-q(18), cy+q(2), q(5), rgba("outline"))
    disc(draw, cx+q(18), cy+q(2), q(5), rgba("outline"))
    disc(draw, cx-q(18), cy+q(2), q(3), rgba("skin"))
    disc(draw, cx+q(18), cy+q(2), q(3), rgba("skin"))
    face = [(cx-q(16),cy-q(12)),(cx-q(18),cy+q(2)),(cx-q(13),cy+q(16)),
            (cx-q(5),cy+q(21)),(cx+q(6),cy+q(20)),(cx+q(14),cy+q(13)),
            (cx+q(18),cy+q(1)),(cx+q(15),cy-q(12))]
    draw.polygon(face, fill=rgba("outline"))
    inner = [(cx-q(13),cy-q(10)),(cx-q(14),cy+q(2)),(cx-q(10),cy+q(13)),
             (cx-q(4),cy+q(17)),(cx+q(5),cy+q(17)),(cx+q(11),cy+q(11)),
             (cx+q(14),cy+q(1)),(cx+q(12),cy-q(10))]
    draw.polygon(inner, fill=rgba("skin"))
    draw.polygon([(cx-q(10),cy+q(9)),(cx,cy+q(17)),(cx+q(10),cy+q(8))], fill=rgba("skin_light"))

    # Short textured crop with high forehead and clearly tapered sides.
    hair = [(cx-q(16),cy-q(11)),(cx-q(15),cy-q(18)),(cx-q(11),cy-q(21)),
            (cx-q(7),cy-q(22)),(cx-q(3),cy-q(21)),(cx,cy-q(23)),
            (cx+q(4),cy-q(22)),(cx+q(7),cy-q(23)),(cx+q(10),cy-q(21)),
            (cx+q(14),cy-q(19)),(cx+q(16),cy-q(14)),(cx+q(15),cy-q(8)),
            (cx+q(10),cy-q(11)),(cx+q(6),cy-q(14)),(cx-q(7),cy-q(14)),
            (cx-q(12),cy-q(11))]
    draw.polygon(hair, fill=rgba("hair"))
    draw.rectangle((cx-q(10),cy-q(20),cx-q(7),cy-q(17)), fill=rgba("hair_light"))
    draw.rectangle((cx+q(2),cy-q(21),cx+q(5),cy-q(19)), fill=rgba("hair_light"))
    draw.rectangle((cx-q(16),cy-q(11),cx-q(13),cy-q(4)), fill=rgba("hair_light"))
    draw.rectangle((cx+q(13),cy-q(11),cx+q(16),cy-q(4)), fill=rgba("hair_light"))

    # Two thick rounded-square frames, with bridge, temples, lenses and pupils.
    gy = cy - q(2)
    for lx in (cx-q(8)+q(face_shift), cx+q(8)+q(face_shift)):
        draw.rounded_rectangle(box(lx,gy,q(15),q(12)), radius=max(1,q(2)), fill=rgba("hair"))
        draw.rounded_rectangle(box(lx,gy,q(9),q(7)), radius=max(1,q(1)), fill=rgba("white"))
        disc(draw,lx+q(face_shift/2),gy+q(1),max(1,q(2)),rgba("eye"))
        draw.rectangle((lx-q(2),gy-q(2),lx,gy-q(1)), fill=rgba("skin_light"))
    draw.rectangle((cx-q(2)+q(face_shift),gy-q(1),cx+q(2)+q(face_shift),gy+q(1)), fill=rgba("hair"))
    draw.rectangle((cx-q(20),gy-q(2),cx-q(15),gy), fill=rgba("hair"))
    draw.rectangle((cx+q(15),gy-q(2),cx+q(20),gy), fill=rgba("hair"))

    draw.rectangle((cx+q(face_shift)-1,cy+q(6),cx+q(face_shift)+1,cy+q(8)), fill=rgba("skin_shadow"))
    # Friendly toothy smile.
    draw.rectangle((cx+q(face_shift)-q(7),cy+q(11),cx+q(face_shift)+q(7),cy+q(15)), fill=rgba("outline"))
    draw.rectangle((cx+q(face_shift)-q(5),cy+q(11),cx+q(face_shift)+q(5),cy+q(12)), fill=rgba("white"))
    draw.rectangle((cx-q(13),cy+q(8),cx-q(11),cy+q(9)), fill=rgba("cheek"))


def draw_jump(character: str) -> Image.Image:
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dad = character == "dad"
    skin = rgba("skin")
    suit = rgba("suit_dark" if dad else "blue")
    suit_hi = rgba("suit_mid" if dad else "blue_light")

    if not dad:
        # FC source: screen-left arm descends; screen-right arm rises; one leg is foreshortened.
        volume_limb(d, [(51,58),(38,63),(27,72)], 9, skin, 5)       # far arm
        volume_limb(d, [(58,77),(51,90),(45,98)], 10, skin, 5)      # far leg
        d.polygon([(47,53),(75,52),(78,70),(70,80),(55,79),(46,68)], fill=rgba("outline"))
        d.polygon([(51,56),(71,55),(74,68),(68,76),(56,75),(50,66)], fill=suit)
        d.polygon([(52,57),(58,56),(58,74),(54,72)], fill=suit_hi)
        volume_limb(d, [(68,76),(73,91),(67,104)], 11, skin, 5)     # near downward leg
        volume_limb(d, [(73,58),(86,45),(98,30)], 10, skin, 6)      # near raised arm
        fist_detail(d,27,72,"left"); fist_detail(d,98,30,"up")
        foot_detail(d,45,98); foot_detail(d,67,104)
        yy_head(d, 62, 38, .92, "front")
    else:
        volume_limb(d, [(47,57),(32,64),(21,74)], 11, skin, 6)
        volume_limb(d, [(57,78),(47,94),(41,104)], 12, skin, 6)
        d.polygon([(43,50),(77,50),(82,70),(72,82),(52,81),(42,68)], fill=rgba("outline"))
        d.polygon([(48,54),(72,54),(77,68),(69,77),(54,76),(47,66)], fill=suit)
        d.polygon([(49,55),(56,54),(56,75),(51,71)], fill=suit_hi)
        volume_limb(d, [(69,78),(77,94),(70,112)], 13, skin, 7)
        volume_limb(d, [(75,57),(89,43),(103,26)], 12, skin, 7)
        fist_detail(d,21,74,"left"); fist_detail(d,103,26,"up")
        foot_detail(d,41,104); foot_detail(d,70,112)
        dad_head(d, 61, 34, .98, "front")
    return im


def draw_surf(character: str) -> Image.Image:
    im = Image.new("RGBA", (160, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dad = character == "dad"
    skin = rgba("skin")
    suit = rgba("suit_dark" if dad else "blue")
    suit_hi = rgba("suit_mid" if dad else "blue_light")

    if not dad:
        # Far body/leg trails to screen right under the water plane.
        d.polygon([(59,64),(85,58),(116,64),(137,76),(134,88),(93,87),(66,78)], fill=rgba("outline"))
        d.polygon([(65,66),(86,62),(114,67),(130,76),(128,83),(94,82),(68,75)], fill=suit)
        d.polygon([(93,64),(114,68),(124,75),(98,74)], fill=suit_hi)
        # Foreground sweep crosses below the face, matching the FC overlap hierarchy.
        volume_limb(d, [(66,69),(48,77),(27,78)], 11, skin, 6)
        volume_limb(d, [(77,67),(93,56),(111,54)], 9, skin, 5)
        fist_detail(d,27,78,"left"); fist_detail(d,111,54,"right")
        yy_head(d, 55, 49, 1.05, "front-left")
    else:
        d.polygon([(58,65),(91,56),(126,65),(149,80),(145,98),(96,95),(65,81)], fill=rgba("outline"))
        d.polygon([(65,68),(92,61),(122,69),(140,80),(137,91),(98,89),(69,77)], fill=suit)
        d.polygon([(99,62),(122,69),(135,79),(104,76)], fill=suit_hi)
        volume_limb(d, [(70,71),(48,82),(24,83)], 13, skin, 7)
        volume_limb(d, [(82,69),(103,55),(125,54)], 11, skin, 6)
        fist_detail(d,24,83,"left"); fist_detail(d,125,54,"right")
        dad_head(d, 57, 48, 1.08, "front-left")
    return im


def draw_uw(character: str) -> Image.Image:
    im = Image.new("RGBA", (160, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dad = character == "dad"
    skin = rgba("skin")
    suit = rgba("suit_dark" if dad else "blue")
    suit_hi = rgba("suit_mid" if dad else "blue_light")

    if not dad:
        # Far legs first: both trail left, but at different depths like the FC source.
        volume_limb(d, [(56,69),(38,74),(21,68)], 9, skin, 5)
        volume_limb(d, [(56,76),(39,89),(20,97)], 10, skin, 5)
        d.polygon([(48,57),(82,51),(101,60),(94,78),(59,82),(45,70)], fill=rgba("outline"))
        d.polygon([(53,60),(80,56),(95,62),(90,73),(60,77),(51,68)], fill=suit)
        d.polygon([(56,61),(65,59),(63,76),(55,72)], fill=suit_hi)
        # Far arm runs under the torso; near arm/fist projects toward screen right.
        volume_limb(d, [(79,69),(99,78),(119,75)], 8, skin, 5)
        volume_limb(d, [(91,59),(113,60),(137,54)], 10, skin, 7)
        foot_detail(d,21,68,"side"); foot_detail(d,20,97,"side")
        fist_detail(d,119,75,"right"); fist_detail(d,137,54,"right")
        yy_head(d, 91, 44, .90, "front-right")
    else:
        volume_limb(d, [(55,72),(34,79),(14,72)], 11, skin, 6)
        volume_limb(d, [(57,81),(36,97),(15,106)], 12, skin, 6)
        d.polygon([(45,57),(85,49),(109,60),(101,83),(60,87),(42,72)], fill=rgba("outline"))
        d.polygon([(51,61),(83,55),(102,63),(96,77),(62,81),(49,70)], fill=suit)
        d.polygon([(53,62),(62,60),(61,80),(53,75)], fill=suit_hi)
        volume_limb(d, [(84,72),(106,83),(130,79)], 10, skin, 6)
        volume_limb(d, [(100,61),(124,62),(149,53)], 12, skin, 8)
        foot_detail(d,14,72,"side"); foot_detail(d,15,106,"side")
        fist_detail(d,130,79,"right"); fist_detail(d,149,53,"right")
        dad_head(d, 99, 43, 1.00, "front-right")
    return im


POSE_BUILDERS = {"SURF0": draw_surf, "JUMP_AIR": draw_jump, "UW_NORMAL": draw_uw}
CHAR_LABEL = {"yy": "阳阳", "dad": "爸爸"}


ORIENTATION = {
    "SURF0": {
        "sourceFrame": {"file": "jp-action-e.gif", "frame": 0, "cropXYXYExclusive": [105,88,136,109], "evidence": "locked official still"},
        "movementVector": {"x": -1, "y": 0, "confidence": "pose-direction candidate; still has no timing"},
        "bodyAxis": "screen-left/front to screen-right/rear, slightly descending",
        "bodyYawToCamera": "front-left three-quarter; rear shoulder recedes to screen-right",
        "headYawToCamera": "near frontal with slight screen-left turn; both eyes visible",
        "nearFarLimbOrder": ["far trailing body/arm", "torso", "near sweeping forearm", "head/face"],
        "waterlineOrDepthPlane": "surface plane crosses below shoulders; sprite excludes water pixels",
    },
    "JUMP_AIR": {
        "sourceFrame": {"file": "jp-action-c.gif", "frame": 0, "cropXYXYExclusive": [73,35,128,77], "evidence": "locked official still"},
        "movementVector": {"x": None, "y": -1, "confidence": "vertical lift implied; horizontal component not established by still"},
        "bodyAxis": "near vertical, head above pelvis, slight diagonal compression",
        "bodyYawToCamera": "front-facing; not a profile jump",
        "headYawToCamera": "front-facing; both eyes visible",
        "nearFarLimbOrder": ["screen-left descending arm/far leg", "torso", "downward near leg", "screen-right raised arm", "head/face"],
        "waterlineOrDepthPlane": "airborne; no water plane intersects the sprite",
    },
    "UW_NORMAL": {
        "sourceFrame": {"file": "jp-action-b.gif", "frame": 0, "cropXYXYExclusive": [99,141,138,162], "evidence": "locked official still; bubble components excluded"},
        "movementVector": {"x": 1, "y": 0, "confidence": "single source-direction candidate"},
        "bodyAxis": "screen-left/rear to screen-right/front, near horizontal",
        "bodyYawToCamera": "front-right three-quarter despite horizontal body axis; not pure side-on",
        "headYawToCamera": "front-right three-quarter; both eyes remain readable",
        "nearFarLimbOrder": ["far trailing legs", "torso", "far lower arm", "head", "near projecting arm/fist"],
        "waterlineOrDepthPlane": "fully underwater; body lies on a shallow diagonal depth plane",
    },
}


def alpha_bbox(im: Image.Image):
    b = im.getchannel("A").getbbox()
    return None if b is None else [b[0], b[1], b[2]-1, b[3]-1]


def root_for(pose, character):
    return {
        ("SURF0","yy"): [81, 84], ("SURF0","dad"): [91, 93],
        ("JUMP_AIR","yy"): [67, 109], ("JUMP_AIR","dad"): [70, 119],
        ("UW_NORMAL","yy"): [80, 69], ("UW_NORMAL","dad"): [84, 73],
    }[(pose, character)]


def pnginfo(pose, character):
    info = PngImagePlugin.PngInfo()
    info.add_text("stage", "CONCEPT-ACTION-0-P0")
    info.add_text("pose", pose)
    info.add_text("character", character)
    info.add_text("identityLock", "CONCEPT-MODEL-LOCK:user-approved-v1")
    info.add_text("sourceFrame", ORIENTATION[pose]["sourceFrame"]["file"] + "#0")
    info.add_text("orientation", ORIENTATION[pose]["bodyYawToCamera"])
    info.add_text("reviewState", "machine-validated-pending-user-visual-review")
    return info


def checker(size, cell=8):
    out = Image.new("RGB", size, (216,220,226))
    d = ImageDraw.Draw(out)
    for y in range(0,size[1],cell):
        for x in range(0,size[0],cell):
            if (x//cell+y//cell)%2:
                d.rectangle((x,y,min(x+cell-1,size[0]-1),min(y+cell-1,size[1]-1)), fill=(188,194,204))
    return out


def paste_crop(board, sprite, xy, scale=1):
    b = sprite.getchannel("A").getbbox()
    crop = sprite.crop(b)
    if scale != 1:
        crop = crop.resize((crop.width*scale,crop.height*scale),Image.Resampling.NEAREST)
    tile = checker(crop.size)
    tile.paste(crop,(0,0),crop)
    board.paste(tile,xy)
    return crop.size


def build_review_board(sprites):
    board = Image.new("RGB", (1800, 1600), (37,43,55))
    d = ImageDraw.Draw(board)
    f_title,f_head,f_body = font(42),font(27),font(20)
    d.text((54,38),"CONCEPT-ACTION-0-P0｜6张用户逐张审核板",font=f_title,fill=(245,247,250))
    d.text((54,94),"左：原生1×　右：整数3×；动作/朝向取FC，人物身份取已确认概念模型",font=f_body,fill=(188,200,217))
    d.text((54,126),"机器PASS不代表视觉通过｜本阶段未接入游戏",font=f_body,fill=(255,137,120))
    pose_notes = {
        "SURF0":"近正面头部；身体向画面右后方拖行；水线在肩下",
        "JUMP_AIR":"面向镜头；左臂下展、右臂上举；一腿透视缩短",
        "UW_NORMAL":"身体轴线近水平，但头身为斜向镜头三分之四视角",
    }
    for row,pose in enumerate(("SURF0","JUMP_AIR","UW_NORMAL")):
        y=180+row*465
        d.rounded_rectangle((45,y,1755,y+430),radius=18,fill=(53,61,76),outline=(110,125,148),width=2)
        d.text((70,y+20),pose,font=f_head,fill=(255,214,105))
        d.text((250,y+25),pose_notes[pose],font=f_body,fill=(228,234,242))
        for col,ch in enumerate(("yy","dad")):
            x=80+col*850
            d.text((x,y+72),CHAR_LABEL[ch],font=f_head,fill=(91,175,255) if ch=="yy" else (255,173,91))
            sp=sprites[(pose,ch)]
            b=sp.getchannel("A").getbbox(); crop=sp.crop(b)
            paste_crop(board,sp,(x,y+120),1)
            paste_crop(board,sp,(x+190,y+95),3)
            d.text((x,y+390),f"1×可见框 {crop.width}×{crop.height}px｜画布 {sp.width}×{sp.height}",font=f_body,fill=(185,196,212))
    out=HERE/"派生精灵审核板.png"
    board.save(out,"PNG",compress_level=9)
    return out


def build_skeleton_board():
    board=Image.new("RGB",(1500,900),(34,39,50)); d=ImageDraw.Draw(board)
    ft,fh,fb=font(38),font(26),font(18)
    d.text((45,30),"FC动作骨架标定｜朝向不是L/R侧身标签",font=ft,fill=(244,247,252))
    d.text((45,82),"蓝=身体轴线　橙=近侧肢体　灰=远侧肢体　黄=移动/动势；仅为标定，不含原版截图",font=fb,fill=(188,201,220))
    skeletons={
        "SURF0":{"j":{"head":(105,115),"neck":(135,150),"hip":(225,185),"farHand":(255,135),"nearHand":(45,178)},"near":["neck","nearHand"],"far":["neck","farHand"],"axis":["head","hip"],"arrow":((180,235),(70,235))},
        "JUMP_AIR":{"j":{"head":(145,75),"neck":(145,125),"hip":(145,190),"farHand":(55,175),"nearHand":(240,65),"farFoot":(95,250),"nearFoot":(165,275)},"near":["neck","nearHand","neck","hip","hip","nearFoot"],"far":["neck","farHand","hip","farFoot"],"axis":["head","hip"],"arrow":((275,245),(275,90))},
        "UW_NORMAL":{"j":{"head":(205,105),"neck":(170,140),"hip":(105,165),"farHand":(235,185),"nearHand":(290,130),"farFoot":(35,155),"nearFoot":(25,215)},"near":["neck","nearHand"],"far":["neck","farHand","hip","farFoot","hip","nearFoot"],"axis":["head","hip"],"arrow":((90,260),(250,260))},
    }
    notes={
        "SURF0":["头近正面，身体退向画面右后方","近臂在脸下方覆盖；非侧脸"],
        "JUMP_AIR":["正面展开，双眼可见","左右臂高低不对称；腿有前后遮挡"],
        "UW_NORMAL":["水平的是身体轴，不是人物侧视","头/躯干三分之四朝镜头，近拳前投"],
    }
    for i,pose in enumerate(("SURF0","JUMP_AIR","UW_NORMAL")):
        ox=55+i*480; oy=150
        d.rounded_rectangle((ox,oy,ox+430,oy+680),radius=16,fill=(50,58,72),outline=(105,122,146),width=2)
        d.text((ox+22,oy+18),pose,font=fh,fill=(255,215,98))
        sk=skeletons[pose]; j={k:(ox+x,oy+90+y) for k,(x,y) in sk["j"].items()}
        axis=[j[k] for k in sk["axis"]]; d.line(axis,fill=(62,170,255),width=8)
        seq=sk["far"]
        for n in range(0,len(seq),2): d.line((j[seq[n]],j[seq[n+1]]),fill=(159,171,189),width=7)
        seq=sk["near"]
        for n in range(0,len(seq),2): d.line((j[seq[n]],j[seq[n+1]]),fill=(255,145,79),width=9)
        for name,(x,y) in j.items():
            r=11 if name=="head" else 6; d.ellipse((x-r,y-r,x+r,y+r),fill=(236,241,248),outline=(24,30,40),width=2)
        (ax,ay),(bx,by)=sk["arrow"]; ax+=ox;ay+=oy+90;bx+=ox;by+=oy+90
        d.line((ax,ay,bx,by),fill=(255,218,78),width=5)
        d.polygon([(bx,by),(bx+10,by-7),(bx+10,by+7)] if bx<ax else [(bx,by),(bx-10,by-7),(bx-10,by+7)],fill=(255,218,78))
        ty=oy+480
        for line in notes[pose]: d.text((ox+24,ty),line,font=fb,fill=(226,232,240)); ty+=34
        camera_note={"SURF0":"镜头：斜前近正面，后肩退向画面右侧","JUMP_AIR":"镜头：正面展开，不是侧面跳跃","UW_NORMAL":"镜头：斜前3/4，水平的只是身体轴"}[pose]
        d.text((ox+24,ty+12),camera_note,font=fb,fill=(155,203,255))
    out=HERE/"动作骨架板.png"; board.save(out,"PNG",compress_level=9); return out


def fit_nearest(im,max_w,max_h):
    factor=max(1,min(max_w//im.width,max_h//im.height))
    return im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST)


def build_private_board(sprites):
    """Optional ignored board containing FC/concept crops; never a formal asset."""
    if not all(p.exists() for p in [*FC_SOURCES.values(),HEAD_REF,ACTION_REF]): return None
    LOCAL.mkdir(parents=True,exist_ok=True)
    board=Image.new("RGB",(2050,1320),(40,45,56));d=ImageDraw.Draw(board)
    ft,fh,fb=font(36),font(24),font(18)
    d.text((45,28),"CONCEPT-ACTION-0-P0｜本地证据对照（禁止提交/上传）",font=ft,fill=(245,247,250))
    d.text((45,76),"每行：FC锁定裁剪｜阳阳/爸爸身份参考｜本轮转译结果。FC只锁动作；概念图只锁人物。",font=fb,fill=(206,215,228))
    head=Image.open(HEAD_REF).convert("RGB"); act=Image.open(ACTION_REF).convert("RGB")
    for row,pose in enumerate(("SURF0","JUMP_AIR","UW_NORMAL")):
        y=125+row*360; d.text((50,y),pose,font=fh,fill=(255,214,99))
        fc=Image.open(FC_SOURCES[pose]).convert("RGB").crop(FC_CROPS[pose]); scale=6 if pose=="JUMP_AIR" else 8; fc=fc.resize((fc.width*scale,fc.height*scale),Image.Resampling.NEAREST)
        board.paste(fc,(50,y+45)); d.text((50,y+225),"FC 8×",font=fb,fill=(190,201,218))
        for col,ch in enumerate(("yy","dad")):
            x=430+col*790
            ref=(head.crop(HEAD_CROPS[ch]) if row==0 else act.crop(ACTION_CROPS[ch]))
            ref.thumbnail((260,240),Image.Resampling.NEAREST); board.paste(ref,(x,y+45))
            sp=sprites[(pose,ch)];b=sp.getchannel("A").getbbox();crop=sp.crop(b).resize(((b[2]-b[0])*2,(b[3]-b[1])*2),Image.Resampling.NEAREST)
            tile=checker(crop.size);tile.paste(crop,(0,0),crop);board.paste(tile,(x+300,y+45))
            d.text((x,y+300),CHAR_LABEL[ch]+"：身份参考 / 转译2×",font=fb,fill=(190,201,218))
    out=LOCAL/"FC与概念模型对照板-本地勿提交.png";board.save(out,"PNG",compress_level=9);return out


def main():
    HERE.mkdir(parents=True,exist_ok=True)
    sprites={}
    entries=[]
    for pose in ("SURF0","JUMP_AIR","UW_NORMAL"):
        for ch in ("yy","dad"):
            im=POSE_BUILDERS[pose](ch)
            out=HERE/f"{pose}_{ch}.png"
            im.save(out,"PNG",pnginfo=pnginfo(pose,ch),compress_level=9,optimize=False)
            sprites[(pose,ch)]=im
            entry={"id":f"{pose}_{ch}","file":out.name,"character":ch,"pose":pose,**ORIENTATION[pose],
                   "root":root_for(pose,ch),"visibleBBox":alpha_bbox(im),"bboxConvention":"xyxyInclusive",
                   "canvas":[im.width,im.height],"palette":"CONCEPT_ACTION_P0_V1","sha256":sha256(out)}
            entries.append(entry)
    review=build_review_board(sprites); skeleton=build_skeleton_board(); private=build_private_board(sprites)
    manifest={
        "schemaVersion":1,"stage":"CONCEPT-ACTION-0-P0",
        "reviewState":"machine-validated-pending-user-visual-review",
        "scope":{"poses":["SURF0","JUMP_AIR","UW_NORMAL"],"characters":["yy","dad"],"directions":"one evidenced source direction only","integratedIntoGame":False,"animation":False},
        "identityLock":{"stage":"CONCEPT-MODEL-LOCK","reviewState":"user-approved-v1","failedDraftPixelsReused":False},
        "privacy":"pure local; formal sprites are code-authored; ignored board may contain local reference crops; nothing uploaded",
        "alphaContract":[0,255],"palette":{"id":"CONCEPT_ACTION_P0_V1","rgba":[list(v) for v in PAL.values()]},
        "frames":entries,
        "boards":{"derivedSpriteReview":{"file":review.name,"sha256":sha256(review)},"actionSkeleton":{"file":skeleton.name,"sha256":sha256(skeleton)},"privateComparison":{"file":str(private.relative_to(HERE)) if private else None,"ignored":True,"sha256":sha256(private) if private else None}},
        "formalGame":{"file":FORMAL_HTML.name,"expectedSha256":FORMAL_HTML_SHA256,"actualSha256":sha256(FORMAL_HTML),"modified":sha256(FORMAL_HTML)!=FORMAL_HTML_SHA256},
        "acceptance":"machine PASS is not visual approval; all six sprites require individual user confirmation before hash freeze",
    }
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sprites":len(entries),"review":str(review),"skeleton":str(skeleton),"private":str(private),"manifest":str(MANIFEST)},ensure_ascii=False,indent=2))


if __name__=="__main__": main()
