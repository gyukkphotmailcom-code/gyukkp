#!/usr/bin/env python3
"""头像底稿生成(阶段2返修版)。

1. 规定裁剪框原样输出(预览页"原照片裁剪"栏引用, 本地已忽略, 不进Git):
   - crop_yy_ref.png = 17296.jpeg  (530,480,340,340)
   - crop_dd_ref.png = IMG_0387.jpeg (1214,880,1100,1100)
2. 作画参考子框(在规定框内, 仅作画参考): yy (575,527,250,250), dd (1324,900,900,900)
3. 真实有限色量化: 子框缩小到24x24后, 用 PIL quantize 映射到该人
   固定8色调色板(与 avatar_paint.py PALETTES 完全一致, 无抖动)。
   分别保存: yy_24.png/dd_24.png(原生24x24) 与
   yy_24down.png/dd_24down.png(240x240最近邻预览), 均照片衍生、已忽略。
"""
from PIL import Image
from collections import Counter
from avatar_paint import PALETTES

OUT = '过程文件/Kimi开发/'

# 规定裁剪框 (x, y, w, h, 原图路径)
PRESCRIBED = {
 'yy': ('17296.jpeg',    (530, 480, 340, 340)),
 'dd': ('IMG_0387.jpeg', (1214, 880, 1100, 1100)),
}
# 作画参考子框 (均在规定框内)
SUBBOX = {
 'yy': (575, 527, 250, 250),
 'dd': (1324, 900, 900, 900),
}

def save_prescribed_crops():
    for name, (path, (x, y, w, h)) in PRESCRIBED.items():
        img = Image.open(path).convert('RGB').crop((x, y, x + w, y + h))
        img.save(OUT + f'crop_{name}_ref.png')
        print(f'规定裁剪框 {name}: ({x},{y},{w},{h}) -> crop_{name}_ref.png {img.size}')

def quantize_to_palette(name):
    path, (px, py, pw, ph) = PRESCRIBED[name]
    sx, sy, sw, sh = SUBBOX[name]
    assert px <= sx and py <= sy and sx + sw <= px + pw and sy + sh <= py + ph, \
        f'{name} 作画子框超出规定裁剪框'
    img = Image.open(path).convert('RGB').crop((sx, sy, sx + sw, sy + sh))
    small = img.resize((24, 24), Image.BOX)

    # 真实限色量化: 显式调色板 + 无抖动
    colors = [c for k, c in PALETTES[name].items() if c is not None]
    assert len(colors) <= 8
    pal_img = Image.new('P', (1, 1))
    flat = [v for c in colors for v in c] + [0] * (768 - len(colors) * 3)
    pal_img.putpalette(flat)
    q = small.quantize(palette=pal_img, dither=Image.Dither.NONE).convert('RGB')

    cnt = Counter(q.getpixel((x, y)) for y in range(24) for x in range(24))
    assert len(cnt) <= 8, f'{name} 量化后颜色数 {len(cnt)} > 8'
    print(f'== {name} 24x24 真实量化结果: {len(cnt)} 色(<=8) ==')
    for c, n in cnt.most_common():
        print('   #%02X%02X%02X x%d' % (c[0], c[1], c[2], n))
    q.save(OUT + f'{name}_24.png')                                  # 原生24x24
    q.resize((240, 240), Image.NEAREST).save(OUT + f'{name}_24down.png')  # 240x240预览

if __name__ == '__main__':
    save_prescribed_crops()
    quantize_to_palette('yy')
    quantize_to_palette('dd')
    print('完成: crop_*_ref.png(规定框, 已忽略) + *_24.png(原生24x24, 已忽略) + *_24down.png(240x240预览, 已忽略)')
