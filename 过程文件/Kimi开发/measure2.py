from PIL import Image
from collections import Counter

US = "/Users/xingbili/Downloads/kimi/阳阳游泳游戏/过程文件/原版参考/视频帧/usa-swim-frames/06m45s.png"
JP = "/Users/xingbili/Downloads/kimi/阳阳游泳游戏/过程文件/原版参考/官方截图/jp-action-e.gif"
OUT = "/Users/xingbili/Downloads/kimi/阳阳游泳游戏/过程文件/Kimi开发/"

us = Image.open(US).convert("RGB")
jp = Image.open(JP).convert("RGB")

# --- HUD x 向测量: 找白条框/文字/槽的 x 范围 ---
px = us.load()
def spans(y, pred, w=256):
    xs = [x for x in range(w) if pred(px[x, y][:3])]
    if not xs: return "none"
    out, s, p = [], xs[0], xs[0]
    for x in xs[1:]:
        if x > p + 1: out.append((s, p)); s = x
        p = x
    out.append((s, p))
    return out

print("== US HUD x-spans ==")
for y in [169, 171, 176, 192, 193, 196, 209, 210, 216, 218]:
    print(f"y={y} white:", spans(y, lambda c: min(c) > 200))
for y in [193, 196, 210, 213]:
    print(f"y={y} brightbar:", spans(y, lambda c: c[2] > 150 and c[0] > 100))

# --- 泳道绳/浮球: 中央 x 附近列采样 ---
print("== US center column colors ==")
for y in [75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 130, 140, 150, 160]:
    print(f"y={y} x=126..131:", [px[x, y][:3] for x in range(126, 132)])

# --- 水下墙面透视: 每行的非黑 x 范围(左墙右墙) ---
print("== US underwater non-black spans ==")
for y in [105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155, 160, 165]:
    row = [px[x, y][:3] for x in range(256)]
    nonblack = [x for x in range(256) if max(row[x]) > 60]
    if nonblack:
        print(f"y={y} first={nonblack[0]} last={nonblack[-1]} n={len(nonblack)}")

# --- 水面波纹: y=76 与 y=88 的 x 色块 ---
print("== US surface rows ==")
for y in [74, 78, 84, 90, 96, 100]:
    runs, prev, s = [], None, 0
    for x in range(256):
        c = px[x, y][:3]
        k = 'W' if min(c) > 200 else ('B' if max(c) < 60 else ('L' if c[2] > 180 else 'o'))
        if k != prev:
            if prev is not None: runs.append((s, x - 1, prev))
            s, prev = x, k
    runs.append((s, 255, prev))
    print(f"y={y}:", runs[:28])

# --- JP gif 行分析 ---
print("== JP row profile ==")
w, h = jp.size
pj = jp.load()
prev = None
for y in range(h):
    row = [pj[x, y][:3] for x in range(0, w, 4)]
    cnt = Counter(row)
    dom, dn = cnt.most_common(1)[0]
    black = sum(v for c, v in cnt.items() if max(c) < 40) / len(row)
    white = sum(v for c, v in cnt.items() if min(c) > 200) / len(row)
    sig = (dom, round(black, 2), round(white, 2))
    if sig != prev:
        print(f"y={y:3d} dom={dom} black={black:.2f} white={white:.2f}")
        prev = sig

# --- 放大裁剪: US 的 HUD/水面/水下 + JP 全图 ---
us.crop((0, 166, 256, 224)).resize((768, 174), Image.NEAREST).save(OUT + "crop_us_hud.png")
us.crop((0, 56, 256, 104)).resize((768, 144), Image.NEAREST).save(OUT + "crop_us_surface.png")
us.crop((0, 100, 256, 168)).resize((768, 204), Image.NEAREST).save(OUT + "crop_us_under.png")
jp.resize((768, 576), Image.NEAREST).save(OUT + "crop_jp_e.png")
print("crops saved")
