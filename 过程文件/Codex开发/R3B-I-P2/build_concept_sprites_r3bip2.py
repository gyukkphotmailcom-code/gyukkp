#!/usr/bin/env python3
"""R3B-I-P2: concept-led deterministic character prototype sprites.

This intentionally does not preserve the old adult body silhouette.  It turns the
approved Yangyang/Dad portrait direction into compact, readable whole characters.
The generated concept sheet is a human reference only; this builder has no image,
photo, network, random-number, or untracked-file dependency.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
SPRITES = HERE / "sprites"

P = {
    "outline": "#101018",
    "skin": "#F0A06E",
    "skin_hi": "#FFC28E",
    "skin_lo": "#C96D4E",
    "white": "#F8F5E9",
    "blue": "#278FDF",
    "blue_hi": "#71C5F4",
    "blue_lo": "#124D97",
    "yy_suit": "#1767B2",
    "dad_suit": "#252932",
    "hair": "#111018",
    "hair_hi": "#3A2B24",
    "water_hi": "#A9ECFF",
    "water": "#35B8E8",
    "water_lo": "#1475A6",
    "under": "#093C63",
    "under_lo": "#062942",
}

META = {
    "SURFACE": {"size": (44, 30), "root": (22, 25)},
    "JUMP": {"size": (48, 44), "root": (25, 42)},
    "SWIM": {"size": (52, 30), "root": (25, 24)},
    "BREATH": {"size": (44, 42), "root": (22, 38)},
}


def rect(d: ImageDraw.ImageDraw, box, color):
    d.rectangle(box, fill=P[color] if color in P else color)


def poly(d: ImageDraw.ImageDraw, pts, color):
    d.polygon(pts, fill=P[color] if color in P else color)


def line(d: ImageDraw.ImageDraw, pts, color, width=1):
    d.line(pts, fill=P[color] if color in P else color, width=width)


def draw_head(img: Image.Image, x: int, y: int, who: str, front: bool = False) -> None:
    """Draw one coherent 18x16 head. Faces stay upright for chibi readability."""
    d = ImageDraw.Draw(img)
    # One continuous head silhouette; ears are attached, never detached "second faces".
    poly(d, [(x+4,y), (x+13,y), (x+17,y+3), (x+17,y+11),
             (x+14,y+15), (x+5,y+15), (x+1,y+11), (x+1,y+4)], "outline")
    rect(d, (x, y+7, x+2, y+11), "outline")
    rect(d, (x+16, y+6, x+18, y+11), "outline")
    poly(d, [(x+4,y+4), (x+14,y+4), (x+16,y+6), (x+16,y+11),
             (x+13,y+14), (x+5,y+14), (x+2,y+11), (x+2,y+6)], "skin")
    rect(d, (x+1, y+8, x+2, y+10), "skin")
    rect(d, (x+16, y+8, x+17, y+10), "skin_lo")
    rect(d, (x+4, y+5, x+13, y+6), "skin_hi")

    if who == "yy":
        # Blue cap and pushed-up goggles from the selected portrait concept.
        poly(d, [(x+3,y+1), (x+13,y+1), (x+16,y+4), (x+16,y+7),
                 (x+3,y+7), (x+2,y+5)], "blue")
        rect(d, (x+5,y+1,x+12,y+2), "blue_hi")
        rect(d, (x+3,y+6,x+15,y+7), "blue_lo")
        # Two goggles, clearly on the cap rather than replacing the eyes.
        rect(d, (x+4,y+3,x+8,y+5), "outline")
        rect(d, (x+10,y+3,x+14,y+5), "outline")
        rect(d, (x+5,y+4,x+7,y+4), "white")
        rect(d, (x+11,y+4,x+13,y+4), "white")
        rect(d, (x+8,y+4,x+10,y+4), "white")
        # Large child eyes below the goggles.
        rect(d, (x+4,y+8,x+6,y+11), "white")
        rect(d, (x+11,y+8,x+13,y+11), "white")
        rect(d, (x+4,y+9,x+5,y+11), "outline")
        rect(d, (x+11,y+9,x+12,y+11), "outline")
        rect(d, (x+5,y+9,x+5,y+9), "white")
        rect(d, (x+12,y+9,x+12,y+9), "white")
        rect(d, (x+8,y+11,x+8,y+11), "skin_lo")
        line(d, [(x+7,y+13),(x+9,y+14),(x+11,y+13)], "outline")
        rect(d, (x+8,y+13,x+10,y+13), "white")
    else:
        # Short black hair and high forehead.
        poly(d, [(x+3,y+1),(x+14,y+1),(x+16,y+3),(x+15,y+5),
                 (x+13,y+4),(x+11,y+5),(x+9,y+4),(x+7,y+5),(x+5,y+4),(x+3,y+6)], "hair")
        rect(d, (x+5,y+1,x+11,y+1), "hair_hi")
        rect(d, (x+14,y+3,x+16,y+7), "hair")
        # Dark rectangular glasses remain visible in every pose.
        rect(d, (x+3,y+7,x+8,y+11), "outline")
        rect(d, (x+10,y+7,x+15,y+11), "outline")
        rect(d, (x+4,y+8,x+7,y+10), "white")
        rect(d, (x+11,y+8,x+14,y+10), "white")
        rect(d, (x+5,y+9,x+6,y+10), "outline")
        rect(d, (x+12,y+9,x+13,y+10), "outline")
        rect(d, (x+8,y+8,x+10,y+9), "outline")
        rect(d, (x+15,y+8,x+17,y+9), "outline")
        rect(d, (x+8,y+11,x+9,y+11), "skin_lo")
        line(d, [(x+6,y+13),(x+8,y+14),(x+11,y+14),(x+13,y+12)], "outline")
        rect(d, (x+8,y+13,x+11,y+13), "white")


def limb(d, outer_pts, inner_pts) -> None:
    poly(d, outer_pts, "outline")
    poly(d, inner_pts, "skin")


def draw_surface(who: str) -> Image.Image:
    img = Image.new("RGBA", META["SURFACE"]["size"], (0,0,0,0))
    d = ImageDraw.Draw(img)
    suit = "yy_suit" if who == "yy" else "dad_suit"
    draw_head(img, 3, 1, who)
    # Compact shoulder/body, not the old oversized adult torso.
    poly(d, [(17,15),(31,14),(40,19),(40,25),(18,25),(14,21)], "outline")
    poly(d, [(18,16),(30,16),(38,19),(38,23),(18,23),(15,20)], suit)
    # Near arm resting on water; one readable hand only.
    limb(d, [(14,18),(7,20),(1,20),(1,24),(9,24),(17,22)],
         [(14,19),(7,21),(2,21),(2,22),(9,22),(16,21)])
    # Back shoulder highlight and small trailing hand.
    rect(d, (32,17,37,18), "skin")
    rect(d, (38,18,42,21), "outline")
    rect(d, (38,19,41,20), "skin")
    return img


def draw_jump(who: str) -> Image.Image:
    img = Image.new("RGBA", META["JUMP"]["size"], (0,0,0,0))
    d = ImageDraw.Draw(img)
    suit = "yy_suit" if who == "yy" else "dad_suit"
    draw_head(img, 3, 2, who)
    # Diagonal compact torso.
    poly(d, [(18,16),(32,16),(38,23),(34,31),(22,28),(15,21)], "outline")
    poly(d, [(19,17),(30,18),(35,23),(32,28),(23,26),(17,21)], suit)
    # Front arm points left/down, rear arm extends right; neither resembles a head.
    limb(d, [(17,18),(10,20),(3,25),(4,29),(12,25),(21,22)],
         [(17,19),(11,21),(5,25),(6,27),(12,23),(20,21)])
    limb(d, [(29,17),(36,13),(44,12),(46,15),(39,18),(33,22)],
         [(30,18),(36,15),(43,14),(44,15),(38,17),(33,20)])
    # Two bent child/adult legs, visually separated.
    limb(d, [(27,28),(36,29),(41,34),(39,38),(34,34),(27,33)],
         [(28,29),(35,30),(39,34),(38,36),(34,32),(28,32)])
    limb(d, [(24,27),(28,34),(26,41),(22,42),(21,35),(19,29)],
         [(24,29),(26,34),(25,39),(23,40),(23,34),(21,29)])
    return img


def draw_swim(who: str) -> Image.Image:
    img = Image.new("RGBA", META["SWIM"]["size"], (0,0,0,0))
    d = ImageDraw.Draw(img)
    suit = "yy_suit" if who == "yy" else "dad_suit"
    draw_head(img, 2, 4, who)
    # Horizontal torso.
    poly(d, [(18,15),(36,14),(43,18),(42,25),(20,25),(15,21)], "outline")
    poly(d, [(19,16),(35,16),(40,18),(40,23),(20,23),(16,20)], suit)
    # Long forward arm under the face.
    limb(d, [(17,18),(9,19),(1,21),(0,24),(9,24),(21,22)],
         [(17,19),(9,20),(2,22),(2,23),(9,22),(20,21)])
    # Split kick legs.
    limb(d, [(39,18),(48,14),(51,15),(50,18),(43,22)],
         [(40,18),(48,15),(50,16),(48,17),(42,21)])
    limb(d, [(40,22),(49,23),(51,26),(49,28),(42,25)],
         [(41,22),(48,24),(49,25),(48,26),(42,24)])
    return img


def draw_breath(who: str) -> Image.Image:
    img = Image.new("RGBA", META["BREATH"]["size"], (0,0,0,0))
    d = ImageDraw.Draw(img)
    suit = "yy_suit" if who == "yy" else "dad_suit"
    draw_head(img, 13, 1, who, front=True)
    poly(d, [(16,16),(29,16),(34,23),(31,37),(13,37),(10,23)], "outline")
    poly(d, [(17,18),(28,18),(31,23),(29,35),(15,35),(12,23)], suit)
    # Open arms, symmetrical and clearly attached to shoulders.
    limb(d, [(14,19),(8,14),(3,8),(0,10),(5,17),(12,24)],
         [(13,20),(8,16),(3,10),(2,11),(6,17),(12,22)])
    limb(d, [(30,19),(36,14),(41,8),(44,10),(39,17),(32,24)],
         [(31,20),(36,16),(41,10),(42,11),(38,17),(32,22)])
    # Open palms.
    rect(d, (0,7,3,11), "outline"); rect(d, (1,8,2,10), "skin")
    rect(d, (41,7,43,11), "outline"); rect(d, (42,8,43,10), "skin")
    return img


BUILDERS = {
    "SURFACE": draw_surface,
    "JUMP": draw_jump,
    "SWIM": draw_swim,
    "BREATH": draw_breath,
}


def checker(size, cell=4):
    img = Image.new("RGBA", size, "white")
    d = ImageDraw.Draw(img)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            c = "#D8D8DC" if (x//cell+y//cell)%2 == 0 else "#F0F0F2"
            d.rectangle((x,y,x+cell-1,y+cell-1), fill=c)
    return img


def on_checker(sprite, scale=1):
    if scale != 1:
        sprite = sprite.resize((sprite.width*scale, sprite.height*scale), Image.Resampling.NEAREST)
    bg = checker(sprite.size, max(2, 3*scale))
    bg.alpha_composite(sprite)
    return bg.convert("RGB")


def font(size=14):
    try:
        return ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", size)
    except OSError:
        return ImageFont.load_default()


def review_sheet(sprites):
    # Two fixed-width character columns. The old horizontal flow could crop
    # Dad's 8x preview and make the review sheet itself misleading.
    fw, row_h = 1400, 440
    sheet = Image.new("RGB", (fw, row_h*4+48), "#F7F7F8")
    d = ImageDraw.Draw(sheet)
    d.text((18,12), "R3B-I-P2 concept-led prototype — 1x / 3x / 8x", fill="#111118", font=font(20))
    for row, action in enumerate(("SURFACE","JUMP","SWIM","BREATH")):
        y = 48 + row*row_h
        d.text((18,y+14), action, fill="#111118", font=font(18))
        for column, who in enumerate(("yy","dad")):
            x = 105 + column * 690
            sp = sprites[(action,who)]
            d.text((x,y+14), "YANGYANG" if who=="yy" else "DAD", fill="#111118", font=font(15))
            for preview_x, sc in ((x, 1), (x+95, 3)):
                cell = on_checker(sp, sc)
                sheet.paste(cell, (preview_x,y+48))
                d.text((preview_x,y+55+cell.height), f"{sc}x  {sp.width}x{sp.height}", fill="#55555C", font=font(12))
            large = on_checker(sp, 8)
            large_x = x + 250
            sheet.paste(large, (large_x,y+42))
            d.text((large_x,y+49+large.height), f"8x  {sp.width}x{sp.height}", fill="#55555C", font=font(12))
        d.line((0,y+row_h-1,fw,y+row_h-1), fill="#D0D0D4")
    return sheet


def water_panel(title, action, sprites):
    w,h = 256,112
    img = Image.new("RGB", (w,h), P["water_hi"])
    d = ImageDraw.Draw(img)
    # Simple project-palette pool context; it is a review mockup, not a background replacement.
    rect(d,(0,0,w-1,31),"#EAF8FA")
    rect(d,(0,32,w-1,37),"water")
    rect(d,(0,38,w-1,h-1),"under")
    for yy in (60,84,108):
        line(d,[(0,yy),(w-1,yy)],"under_lo")
    for xx in range(16,w,32):
        line(d,[(xx,38),(xx,h-1)],"water_lo")
    d.text((6,5), title, fill="#102030", font=font(13))
    yysp=sprites[(action,"yy")]; ddsp=sprites[(action,"dad")]
    if action=="JUMP":
        pos=((70,18),(180,18))
    elif action=="SWIM":
        pos=((30,58),(150,70))
    elif action=="BREATH":
        pos=((58,23),(174,23))
    else:
        pos=((62,16),(176,16))
    img.paste(yysp,pos[0],yysp); img.paste(ddsp,pos[1],ddsp)
    return img


def scene_sheet(sprites):
    actions=(("WATER SURFACE","SURFACE"),("AIRBORNE JUMP","JUMP"),
             ("UNDERWATER SWIM","SWIM"),("SUPER BREATH","BREATH"))
    native=Image.new("RGB",(512,224),"#101018")
    for i,(title,action) in enumerate(actions):
        p=water_panel(title,action,sprites)
        native.paste(p,((i%2)*256,(i//2)*112))
    return native.resize((1536,672),Image.Resampling.NEAREST)


def png_bytes(img):
    b=io.BytesIO(); img.save(b,"PNG",optimize=False); return b.getvalue()


def main():
    SPRITES.mkdir(parents=True,exist_ok=True)
    sprites={}
    manifest={"stage":"R3B-I-P2","status":"prototype-not-integrated","palette":P,"sprites":{}}
    for action,builder in BUILDERS.items():
        for who in ("yy","dad"):
            img=builder(who)
            sprites[(action,who)]=img
            name=f"{action}_{who}_L.png"
            data=png_bytes(img)
            (SPRITES/name).write_bytes(data)
            manifest["sprites"][f"{action}_{who}_L"]={
                "file":f"sprites/{name}","w":img.width,"h":img.height,
                "root":META[action]["root"],"pngSha256":hashlib.sha256(data).hexdigest()
            }
    review=review_sheet(sprites); scene=scene_sheet(sprites)
    (HERE/"阶段R3B-I-P2人物动作对照表.png").write_bytes(png_bytes(review))
    (HERE/"阶段R3B-I-P2游戏场景效果图.png").write_bytes(png_bytes(scene))
    (HERE/"concept_sprites_r3bip2.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("OK R3B-I-P2 generated 8 sprites + review sheets")


if __name__=="__main__":
    main()
