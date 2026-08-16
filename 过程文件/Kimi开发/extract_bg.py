#!/usr/bin/env python3
"""v3: 背景调色板改为日版gif实际采样主色(top13); 仅输出 BG_COLORS/BG_RLE。"""
from PIL import Image
from collections import Counter, deque

SRC = '过程文件/原版参考/官方截图/jp-action-e.gif'
OUT = '过程文件/Kimi开发/'

gif = Image.open(SRC).convert('RGB')   # 256x192 原生, 第0行为图片边框灰线
GW, GH = gif.size
px = gif.load()

# 远景区 y1..84 实际采样 top13 主色 + 绿篱区(y75..84,x0..60)采样绿
cnt = Counter(px[x, y] for y in range(1, 85) for x in range(GW))
TOP = [c for c, _ in cnt.most_common(13)]
gcnt = Counter(px[x, y] for y in range(75, 85) for x in range(60)
               if px[x, y][1] > 120 and px[x, y][1] > px[x, y][0] + 40)
if gcnt:
    TOP.append(gcnt.most_common(1)[0][0])
print('日版实际采样主色:')
for c in TOP:
    print('  #%02X%02X%02X x%d' % (c[0], c[1], c[2], cnt.get(c, gcnt.get(c, 0))))
COLORS = TOP

def nearest(rgb):
    best, bd = 0, 1 << 62
    for i, c in enumerate(COLORS):
        d = (rgb[0]-c[0])**2 + (rgb[1]-c[1])**2 + (rgb[2]-c[2])**2
        if d < bd:
            bd, best = d, i
    return best

q = [[nearest(px[x, y]) for x in range(GW)] for y in range(GH)]

# 面积去噪: 连通域 <4px 并入四邻最多色
lab = [[-1]*GW for _ in range(GH)]
out = [row[:] for row in q]
for y in range(GH):
    for x in range(GW):
        if lab[y][x] >= 0:
            continue
        c = q[y][x]; cells = [(x, y)]; lab[y][x] = 1
        dq = deque([(x, y)])
        while dq:
            cx, cy = dq.popleft()
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < GW and 0 <= ny < GH and lab[ny][nx] < 0 and q[ny][nx] == c:
                    lab[ny][nx] = 1; dq.append((nx, ny)); cells.append((nx, ny))
        if len(cells) < 4:
            cc = Counter()
            for cx, cy in cells:
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < GW and 0 <= ny < GH and q[ny][nx] != c:
                        cc[q[ny][nx]] += 1
            if cc:
                rep = cc.most_common(1)[0][0]
                for cx, cy in cells:
                    out[cy][cx] = rep
q = out

# gif原生 y1..84 -> 帧 y0..72
GIF_BG_TOP, GIF_BG_END, BG_ROWS = 1, 84, 73
bg_rle = []
for y in range(BG_ROWS):
    gy = GIF_BG_TOP + round(y * (GIF_BG_END - GIF_BG_TOP) / (BG_ROWS - 1))
    src = q[min(GH - 1, gy)]
    row, run, cur = [], src[0], 1
    for x in range(1, GW):
        if src[x] == run:
            cur += 1
        else:
            row.append([run, cur]); run, cur = src[x], 1
    row.append([run, cur])
    bg_rle.append(row)

prev = Image.new('RGB', (GW, BG_ROWS))
for y in range(BG_ROWS):
    gy = GIF_BG_TOP + round(y * (GIF_BG_END - GIF_BG_TOP) / (BG_ROWS - 1))
    src = q[min(GH - 1, gy)]
    for x in range(GW):
        prev.putpixel((x, y), COLORS[src[x]])
prev.resize((GW*3, BG_ROWS*3), Image.NEAREST).save(OUT + 'bg_quantized_preview.png')

def hx(c): return '#%02X%02X%02X' % c
with open(OUT + 'bg_data.js', 'w') as f:
    f.write('const BG_COLORS = [%s];\n' % ','.join("'%s'" % hx(c) for c in COLORS))
    f.write('const BG_RLE = [\n')
    for row in bg_rle:
        f.write('  [%s],\n' % ','.join('[%d,%d]' % (i, l) for i, l in row))
    f.write('];\n')
import os
print('bg_data.js bytes:', os.path.getsize(OUT + 'bg_data.js'))
