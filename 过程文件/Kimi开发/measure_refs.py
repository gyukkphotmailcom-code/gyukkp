from PIL import Image
from collections import Counter

def row_profile(im, name):
    w, h = im.size
    px = im.load()
    print(f"=== {name} {w}x{h} row profile ===")
    prev = None
    for y in range(h):
        row = [px[x, y][:3] for x in range(0, w, 4)]
        # 特征: 黑占比/白占比/蓝水色占比/青占比/主色
        cnt = Counter(row)
        dom, dn = cnt.most_common(1)[0]
        black = sum(v for c, v in cnt.items() if max(c) < 40) / len(row)
        white = sum(v for c, v in cnt.items() if min(c) > 200) / len(row)
        sig = (dom, round(black, 2), round(white, 2))
        if sig != prev:
            print(f"y={y:3d} dom={dom} black={black:.2f} white={white:.2f}")
            prev = sig

def sample(im, name, points):
    px = im.load()
    print(f"--- {name} samples ---")
    for (x, y, tag) in points:
        print(f"({x:3d},{y:3d}) {px[x,y][:3]} {tag}")

us = Image.open("/Users/xingbili/Downloads/kimi/阳阳游泳游戏/过程文件/原版参考/视频帧/usa-swim-frames/06m45s.png").convert("RGB")
row_profile(us, "06m45s")
