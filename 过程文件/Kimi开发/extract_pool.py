#!/usr/bin/env python3
"""烘焙 06m45s.png 池体区 y72..165 为 调色板+索引RLE; 三帧投票修补偶发像素。"""
from PIL import Image

DIR = '过程文件/原版参考/视频帧/usa-swim-frames/'
OUT = '过程文件/Kimi开发/'
Y0, Y1 = 72, 165

main = Image.open(DIR + '06m45s.png').convert('RGB')
prev = Image.open(DIR + '06m44s.png').convert('RGB')
nxt  = Image.open(DIR + '06m46s.png').convert('RGB')
assert main.size == (256, 224) and prev.size == (256, 224) and nxt.size == (256, 224), \
    (main.size, prev.size, nxt.size)

def close(a, b, th=30):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2 <= th*th

W = 256
fixed, patched = [], 0
for y in range(Y0, Y1 + 1):
    row = []
    for x in range(W):
        m, p, n = main.getpixel((x, y)), prev.getpixel((x, y)), nxt.getpixel((x, y))
        if not close(m, p) and not close(m, n) and close(p, n):
            row.append(p); patched += 1          # 45与两邻帧均不同、两邻帧一致 -> 偶发, 用邻帧补
        else:
            row.append(m)
    fixed.append(row)
print('修补偶发像素:', patched)

# 视频帧有压缩噪声: MedianCut 量化到16色(调色板=帧实际采样色)
region = Image.new('RGB', (W, Y1 - Y0 + 1))
for i, row in enumerate(fixed):
    for x, c in enumerate(row):
        region.putpixel((x, i), c)
qimg = region.quantize(colors=16, method=Image.MEDIANCUT)
pal_raw = qimg.getpalette()[:16*3]
palette = [tuple(pal_raw[i*3:i*3+3]) for i in range(16)]
qpx = qimg.load()

# 小连通域去噪 (<3px 并入邻域主色), 保边
from collections import Counter, deque
q = [[qpx[x, y] for x in range(W)] for y in range(Y1 - Y0 + 1)]
H2 = Y1 - Y0 + 1
lab = [[-1]*W for _ in range(H2)]
for y in range(H2):
    for x in range(W):
        if lab[y][x] >= 0:
            continue
        c = q[y][x]; cells = [(x, y)]; lab[y][x] = 1
        dq = deque([(x, y)])
        while dq:
            cx, cy = dq.popleft()
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < W and 0 <= ny < H2 and lab[ny][nx] < 0 and q[ny][nx] == c:
                    lab[ny][nx] = 1; dq.append((nx, ny)); cells.append((nx, ny))
        if len(cells) < 3:
            cnt = Counter()
            for cx, cy in cells:
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < W and 0 <= ny < H2 and q[ny][nx] != c:
                        cnt[q[ny][nx]] += 1
            if cnt:
                rep = cnt.most_common(1)[0][0]
                for cx, cy in cells:
                    q[cy][cx] = rep

rows_idx = q
print('池体区颜色数:', len(palette))
print('调色板:', ['#%02X%02X%02X' % c for c in palette])

# 索引RLE
rle = []
for ri in rows_idx:
    segs, cur, ln = [], ri[0], 1
    for v in ri[1:]:
        if v == cur:
            ln += 1
        else:
            segs.append([cur, ln]); cur, ln = v, 1
    segs.append([cur, ln])
    rle.append(segs)

def hx(c): return '#%02X%02X%02X' % c
with open(OUT + 'pool_data.js', 'w') as f:
    f.write('const POOL_COLORS = [%s];\n' % ','.join("'%s'" % hx(c) for c in palette))
    f.write('const POOL_RLE = [\n')
    for segs in rle:
        f.write('  [%s],\n' % ','.join('[%d,%d]' % (i, l) for i, l in segs))
    f.write('];\n')

# 烘焙预览
prev_img = Image.new('RGB', (W, Y1 - Y0 + 1))
for i, ri in enumerate(rows_idx):
    for x, ci in enumerate(ri):
        prev_img.putpixel((x, i), palette[ci])
prev_img.resize((W*3, (Y1 - Y0 + 1)*3), Image.NEAREST).save(OUT + 'pool_baked_preview.png')
import os
print('pool_data.js bytes:', os.path.getsize(OUT + 'pool_data.js'))
