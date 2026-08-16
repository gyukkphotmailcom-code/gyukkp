#!/usr/bin/env python3
"""生成 过程文件/Kimi开发/头像预览.html (阶段2返修版)。

- 像素数据以字符串数组静态烘焙进HTML, 渲染仅用Canvas drawImage最近邻放大,
  不做任何CSS/Canvas镜像(左右方向数据已在 avatar_paint.py 中分别烘焙)。
- 禁止 data:image / base64: 原照片裁剪一律引用本地已忽略文件 crop_*_ref.png。
- 每头像三栏: 24x24(1x) / 72x72(3x 正式验收) / 192x192(8x)。
- 匿名A/B区: 中性灰底, 无姓名/照片/队伍标识。
- URL 加 #safe 时隐藏全部照片栏 -> 供Git安全截图(只显示像素头像)。
"""
import json
from avatar_paint import FACES, PALETTES, EXPRS, DIRS

OUT = '过程文件/Kimi开发/头像预览.html'
NAMES = {'yy': '阳阳', 'dd': '爸爸'}
CROP = {'yy': ('crop_yy_ref.png', '规定裁剪框 530,480,340,340'),
        'dd': ('crop_dd_ref.png', '规定裁剪框 1214,880,1100,1100')}
DIR_CN = {'right': '右', 'left': '左'}

faces_json = json.dumps(FACES, ensure_ascii=False)
pal_json = json.dumps({p: {k: ('#%02X%02X%02X' % v if v else None)
                           for k, v in pal.items()} for p, pal in PALETTES.items()},
                      ensure_ascii=False)

person_sections = []
for p in ['yy', 'dd']:
    src, label = CROP[p]
    cards = []
    for d in DIRS:
        for e in EXPRS:
            cid = f'{p}-{d}-{EXPRS.index(e)}'
            cards.append(f'''
      <div class="card">
        <div class="cap">{DIR_CN[d]} · {e}</div>
        <div class="scales">
          <div class="scale"><canvas id="c-{cid}-1" width="24" height="24"></canvas><i>1x 24×24</i></div>
          <div class="scale"><canvas id="c-{cid}-3" width="72" height="72"></canvas><i>3x 72×72 验收</i></div>
          <div class="scale"><canvas id="c-{cid}-8" width="192" height="192"></canvas><i>8x 192×192</i></div>
        </div>
      </div>''')
    person_sections.append(f'''
  <section class="person">
    <h2>{NAMES[p]}</h2>
    <div class="prow">
      <div class="photo-cell">
        <img src="{src}" alt="{NAMES[p]}原照片裁剪">
        <div class="cap">原照片裁剪（{label}，本地引用，已忽略不进Git）</div>
      </div>
      <div class="grid">{''.join(cards)}
      </div>
    </div>
  </section>''')

ab_rows = []
for ab, p in [('A', 'yy'), ('B', 'dd')]:
    cells = []
    for d in DIRS:
        for e in EXPRS:
            cid = f'{ab}-{d}-{EXPRS.index(e)}'
            cells.append(f'<div class="abcell"><canvas id="ab-{cid}" width="72" height="72"></canvas></div>')
    ab_rows.append(f'<div class="abrow"><span class="abtag">{ab}</span>{"".join(cells)}</div>')

html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>阶段2 头像预览（返修版）</title>
<style>
  body {{ font-family: -apple-system, "PingFang SC", monospace; background:#202028; color:#E8E8F0; margin:16px; }}
  h1 {{ font-size:18px; }} h2 {{ font-size:15px; margin:14px 0 6px; }}
  .note {{ font-size:12px; color:#9A9AA8; max-width:1100px; line-height:1.7; }}
  .person {{ border-top:1px solid #3A3A48; padding-top:6px; }}
  .prow {{ display:flex; gap:14px; align-items:flex-start; }}
  .photo-cell img {{ width:216px; height:216px; image-rendering:auto; border:1px solid #555; display:block; }}
  .photo-cell .cap {{ font-size:11px; color:#9A9AA8; width:216px; margin-top:4px; line-height:1.5; }}
  .grid {{ display:grid; grid-template-columns:repeat(4, auto); gap:10px; }}
  .card {{ background:#2A2A34; border:1px solid #3A3A48; padding:6px; }}
  .card .cap {{ font-size:12px; margin-bottom:4px; }}
  .scales {{ display:flex; gap:8px; align-items:flex-end; }}
  .scale {{ text-align:center; }}
  .scale i {{ display:block; font-size:10px; color:#9A9AA8; font-style:normal; margin-top:2px; }}
  canvas {{ image-rendering:pixelated; background:transparent; }}
  .scale canvas {{ background:#585860; }}
  #ab section, .ab {{ border-top:1px solid #3A3A48; margin-top:14px; padding-top:6px; }}
  .abrow {{ display:flex; gap:8px; align-items:center; margin:6px 0; }}
  .abtag {{ font-size:14px; width:20px; }}
  .abcell {{ background:#8C8C8C; padding:4px; line-height:0; }}
  body.safe .photo-cell {{ display:none; }}
  .palette {{ font-size:11px; color:#9A9AA8; margin:4px 0 0; }}
</style>
</head>
<body>
<h1>阶段2 像素头像预览（返修版：统一调色板 / 左右朝向 / 3x验收 / 匿名A/B）</h1>
<p class="note">
调色板对齐主游戏 PAL：轮廓 #000000、白 #FCFCFC、肤 #FCB88C、肤暗 #D88A58，双方共用统一阴影 #B06840；
阳阳另加泳帽蓝2档，爸爸另加发/镜框棕2档（每人 透明+8色 以内）。<br>
左/右朝向为分别烘焙的静态像素数组，镜像仅作结构基础，已人工修正泳镜高光侧；运行时不使用 CSS/Canvas 镜像。
本页不含任何内嵌图片二进制；照片为本地已忽略文件外链。URL 加 <b>#safe</b> 隐藏照片栏，供 Git 安全截图。
</p>
{''.join(person_sections)}
  <section class="ab">
    <h2>匿名 A/B（中性背景，无姓名/照片/队伍标识）</h2>
    {''.join(ab_rows)}
  </section>
<script>
const FACES = {faces_json};
const PAL = {pal_json};
const EXPRS = {json.dumps(EXPRS, ensure_ascii=False)};
const DIRS = {json.dumps(DIRS)};
const ORDER = {{ yy: 'A', dd: 'B' }};
if (location.hash === '#safe') document.body.classList.add('safe');
function draw(canvas, person, dir, expr, scale) {{
  const rows = FACES[person][dir][expr], pal = PAL[person];
  const off = document.createElement('canvas'); off.width = 24; off.height = 24;
  const octx = off.getContext('2d');
  const im = octx.createImageData(24, 24);
  for (let y = 0; y < 24; y++) for (let x = 0; x < 24; x++) {{
    const hex = pal[rows[y][x]];
    if (!hex) continue;
    const i = (y * 24 + x) * 4;
    im.data[i] = parseInt(hex.slice(1, 3), 16);
    im.data[i+1] = parseInt(hex.slice(3, 5), 16);
    im.data[i+2] = parseInt(hex.slice(5, 7), 16);
    im.data[i+3] = 255;
  }}
  octx.putImageData(im, 0, 0);
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off, 0, 0, canvas.width, canvas.height);
}}
for (const p of ['yy', 'dd']) for (const d of DIRS) EXPRS.forEach((e, i) => {{
  for (const s of [1, 3, 8]) draw(document.getElementById(`c-${{p}}-${{d}}-${{i}}-${{s}}`), p, d, e, s);
  draw(document.getElementById(`ab-${{ORDER[p]}}-${{d}}-${{i}}`), p, d, e, 3);
}});
</script>
</body>
</html>'''

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print('生成', OUT, len(html), 'bytes')
low = html.lower()
assert 'data:image' not in low and 'base64' not in low, '禁止内嵌照片二进制'
print('自检: 无 data:image / base64 (html.lower() 检查)')
