#!/usr/bin/env python3
"""像素头像数据 v2: 2人 x 2方向 x 4表情 = 16张 24x24。

调色板: 两人共用主游戏 PAL 的 轮廓#000000 / 白#FCFCFC / 肤#FCB88C / 肤暗#D88A58,
另加一套双方共用的统一阴影肤色 #B06840; 每人再加2档帽/发色。
每人调色板 = 透明 + 共用6色 + 特有2色 = 最多9键(8色+透明)。

方向: right 为基准; left 以逐行镜像为结构基础, 再人工修正:
  - 阳阳泳镜镜片高光 W 固定在光源侧(画面左上), 不随镜像翻转;
  - 镜带结/泳镜带/爸爸镜腿/汗滴随镜像落在正确一侧, 逐行检查后无需额外改动;
  - 爸爸瞳孔为 Od/dO 对称小结构, 镜像后仍成立。
最终全部烘焙为静态像素数组, 运行时不依赖 CSS/Canvas 镜像。
"""
from pathlib import Path
from PIL import Image

# ---------- 共用色 (对齐主游戏 PAL) ----------
SHARED = {
 '.': None,                  # 透明
 'O': (0, 0, 0),             # 轮廓 = PAL.black #000000
 'S': (252, 184, 140),       # 肤亮 = PAL.skin  #FCB88C
 's': (216, 138, 88),        # 肤中 = PAL.skinD #D88A58
 'd': (176, 104, 64),        # 肤影 = 双方共用统一阴影 #B06840
 'W': (252, 252, 252),       # 强调白 = PAL.white #FCFCFC
}
PALETTES = {
 'yy': {**SHARED, 'C': (60, 156, 240), 'c': (30, 90, 168)},   # 泳帽蓝2档
 'dd': {**SHARED, 'H': (56, 36, 26), 'h': (92, 64, 48)},      # 发/镜框棕2档
}

# ---------- 阳阳 RIGHT (基准) ----------
YY_RIGHT_NORMAL = [
"........................",
"........................",
"........OOOOOOO.........",
"......OOCCCCCCCOO.......",
".....OCCCcCCcCCCCO......",
"....OCCCCCCCCCCCCO......",
"....OCWWWWCCWWWWCO......",
"....OCWccWWWWccWCO......",
"....OCWWWWCCWWWWCO......",
"....OCCCCCCCCCCCCO......",
"..OWWCCCCCCCCCCCCCOO....",
"..OOSSSSSSSSSSSSSSOO....",
"..OOSSSSSSSSSSSSSSOO....",
"..OSSSSSSSSSSSSSSSO.....",
"..OSddSSSSSSSSddSSO.....",
"..OSOdOSSSSSSdOdSO......",
"..OSOWdSSSSSSWOdSO......",
"..OSSSSSSSSSSSSSSO......",
"...OSSSSSSSSSSSSO.......",
"...sSSSSSSdddSSSs.......",
"....sSSSSSSSSSSs........",
".....sSSSSSSSSs.........",
"......ssSSSSss..........",
"........ssss............",
]

# ---------- 爸爸 RIGHT (基准; 镜腿右侧延伸) ----------
DD_RIGHT_NORMAL = [
"........................",
"......OOOOOOOOO.........",
"....OOHHHHHHHHHHOO......",
"...OHHHHHHHHHHHHHHO.....",
"..OHHHHHSSSSHHHHHHO.....",
"..OHHHSSSSSSSSHHHO......",
"..OHHSSSSSSSSSSHHSO.....",
"..OSSSSSSSSSSSSSSSO.....",
"..OSSSSSSSSSSSSSSSO.....",
"..hhhhhhhhhhhhhhhhhhOOhh",
"OhhSSSSSSShhSSSSSSShhO..",
".OhSOdSSSShhSSSdOShO....",
".OhSSSSSSShhSSSSSShO....",
"..OOhSSSSSSSSSSShOO.....",
"...OSSSSSSSSSSSSO.......",
"....SSSSSSdddSSSS.......",
"....sSSSSSSSSSSSs.......",
"....sSSSWWWWWWWWSs......",
"....sSSSSSSSSSSSs.......",
".....sSSSSSSSSs.........",
"......sSSSSSSs..........",
".......ssssss...........",
"........................",
"........................",
]

def patch(base, changes):
    rows = base[:]
    for y, row in changes.items():
        assert len(row) == 24, f'patch行{y}长度{len(row)}: {row!r}'
        rows[y] = row
    return rows

# ---------- RIGHT 表情变体 ----------
# 汗滴 = 3像素泪滴形: 顶1px(x20) + 底2px(x19..20), 不再用孤立白点
YY_R_HIT = patch(YY_RIGHT_NORMAL, {
13: "..OSSSSSSSSSSSSSSSO.W...",   # 汗滴顶
14: "..OSddddSSSSddddSO.WW...",   # 紧锁眉 + 汗滴底
15: "..OSO.OSSSSSSO.OSO......",   # X眼(上)
16: "..OS.O.SSSSSS.O.SO......",   # X眼(下)
19: "...sSSSSSSWWWSSSs.......",   # 咬牙露齿
})
YY_R_DIZZY = patch(YY_RIGHT_NORMAL, {
16: "..OSdOdSSSSSSOdOSO......",   # 漩涡眼
19: "...sSSSSOOOOOOSSSSs.....",   # 张黑嘴(上)
20: "....sSSSOOOOOOSSs.......",   # 张黑嘴(下)
})
YY_R_DOWN = patch(YY_RIGHT_NORMAL, {
13: "..OSSSSSSSSSSSSSSSO.W...",   # 汗滴顶
14: "..OSddSSSSSSSSddSSOWW...",   # 汗滴底
15: "..OSdddSSSSSSdddSO......",   # 闭眼低垂
16: "..OSSSSSSSSSSSSSSO......",
19: "...sSSSSSddddSSSs.......",   # 下撇嘴
})
DD_R_HIT = patch(DD_RIGHT_NORMAL, {
 5: "..OHHHSSSSSSSSHHHO..W...",   # 汗滴顶
 6: "..OHHSSSSSSSSSSHHSOWW...",   # 汗滴底
11: ".OhSO.OSSShhSO.OSShO....",   # X眼(上)
12: ".OhSSO.OSShhSO.OSShO....",   # X眼(下)
16: "....sSSSSdddddSSSs......",   # 咬牙上沿
17: "....sSSWWWWWWWWSSs......",   # 咬紧牙关
})
DD_R_DIZZY = patch(DD_RIGHT_NORMAL, {
11: ".OhSOOSSSShhSOOSSShO....",   # 呆滞方块眼(上)
12: ".OhSOOSSSShhSOOSSShO....",   # 呆滞方块眼(下)
17: "....sSSSOOOOOOOOSs......",   # 张黑嘴(上)
18: "....sSSSOOOOOOOOSs......",   # 张黑嘴(下)
})
DD_R_DOWN = patch(DD_RIGHT_NORMAL, {
 5: "..OHHHSSSSSSSSHHHO..W...",   # 汗滴顶
 6: "..OHHSSSSSSSSSSHHSOWW...",   # 汗滴底
11: ".OhSSdddSShhSdddSShO....",   # 闭眼低垂
17: "....sSSSOOOOOOOOSs......",   # 败北大口(上)
18: "....sSSSddddddddSs......",   # 败北大口(下/暗)
})

# ---------- LEFT = 镜像 + 人工修正 ----------
def mirror(rows):
    return [r[::-1] for r in rows]

def to_left(right_rows, fixes=None):
    rows = mirror(right_rows)
    for y, row in (fixes or {}).items():
        assert len(row) == 24, f'left修正行{y}长度{len(row)}'
        rows[y] = row
    return rows

# 人工修正(固定左上光源, 左向稿不等于右向稿的精确镜像):
#  - 阳阳正常: 泳镜镜片高光 W 固定在画面左上光源侧, 不随镜像翻转
#  - 阳阳挨打/败北: 画面右侧(背光侧)脸颊边缘 S→s 阴影
#  - 阳阳气绝: 张黑嘴右下沿 s→d 加深(背光侧)
#  - 爸爸全部4表情: 画面左侧发际 H→h 受光 + 左镜片上沿 S→W 高光
YY_L_NORMAL = to_left(YY_RIGHT_NORMAL, {16: "......OSOWdSSSSSSWOdSO.."})
YY_L_HIT    = to_left(YY_R_HIT, {
17: "......OSSSSSSSSSSSSSsO..",   # 右颊阴影
18: ".......OSSSSSSSSSSSsO...",
})
YY_L_DIZZY  = to_left(YY_R_DIZZY, {
19: ".....sSSSSOOOOOOSSSSd...",   # 嘴右沿加深
20: ".......sSSOOOOOOSSSd....",   # 嘴右下沿加深
})
YY_L_DOWN   = to_left(YY_R_DOWN, {
17: "......OSSSSSSSSSSSSSsO..",   # 右颊阴影
18: ".......OSSSSSSSSSSSsO...",
})
DD_LEFT_FIXES = {
 4: ".....OhHHHHHSSSSHHHHHO..",   # 左侧发际受光 H→h
10: "..OhhWSSSSSShhSSSSSSShhO",    # 左镜片上沿高光 S→W
}
DD_L_NORMAL = to_left(DD_RIGHT_NORMAL, DD_LEFT_FIXES)
DD_L_HIT    = to_left(DD_R_HIT, DD_LEFT_FIXES)
DD_L_DIZZY  = to_left(DD_R_DIZZY, DD_LEFT_FIXES)
DD_L_DOWN   = to_left(DD_R_DOWN, DD_LEFT_FIXES)

# ---------- 总表: 人物 → 方向 → 表情 ----------
FACES = {
 'yy': {
   'right': {'正常': YY_RIGHT_NORMAL, '挨打': YY_R_HIT, '气绝': YY_R_DIZZY, '败北': YY_R_DOWN},
   'left':  {'正常': YY_L_NORMAL,     '挨打': YY_L_HIT, '气绝': YY_L_DIZZY, '败北': YY_L_DOWN},
 },
 'dd': {
   'right': {'正常': DD_RIGHT_NORMAL, '挨打': DD_R_HIT, '气绝': DD_R_DIZZY, '败北': DD_R_DOWN},
   'left':  {'正常': DD_L_NORMAL,     '挨打': DD_L_HIT, '气绝': DD_L_DIZZY, '败北': DD_L_DOWN},
 },
}
EXPRS = ['正常', '挨打', '气绝', '败北']
DIRS = ['right', 'left']

def validate():
    for person, dirs in FACES.items():
        pal = PALETTES[person]
        for d, exprs in dirs.items():
            assert set(exprs.keys()) == set(EXPRS), (person, d, exprs.keys())
            for e, rows in exprs.items():
                assert len(rows) == 24, (person, d, e, '行数', len(rows))
                used = set()
                for i, r in enumerate(rows):
                    assert len(r) == 24, (person, d, e, i, len(r))
                    used |= set(r)
                bad = used - set(pal.keys())
                assert not bad, (person, d, e, '色键越界', bad)
        # 左向稿不得等于右向稿的逐像素精确镜像
        for e in EXPRS:
            exact = [r[::-1] for r in dirs['right'][e]]
            assert dirs['left'][e] != exact, (person, e, 'left 等于 right 的精确镜像')
    print('校验通过: 2人 x 2方向 x 4表情 = 16张, 全部24x24, 色键在调色板内, 左右稿均非精确镜像')

def diff_vs_mirror():
    """每组左右稿相对"精确镜像"的差异像素数(验收记录用), 必须全部>0。"""
    report = []
    for p in ['yy', 'dd']:
        for e in EXPRS:
            m = [r[::-1] for r in FACES[p]['right'][e]]
            l = FACES[p]['left'][e]
            n = sum(a != b for ra, rb in zip(m, l) for a, b in zip(ra, rb))
            assert n > 0, (p, e)
            report.append((p, e, n))
    return report

def render_sheet(path=None, scale=6, gap=6, bg=(40, 40, 48)):
    if path is None:
        path = Path(__file__).parent / 'avatar_draft.png'   # 始终输出到脚本所在目录
    cols, rows_n = 8, 2   # 每行: 一人 2方向x4表情
    w = cols * 24 * scale + (cols + 1) * gap
    h = rows_n * 24 * scale + (rows_n + 1) * gap
    img = Image.new('RGB', (w, h), bg)
    for r, person in enumerate(['yy', 'dd']):
        c = 0
        for d in DIRS:
            for e in EXPRS:
                face = FACES[person][d][e]
                px = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
                pal = PALETTES[person]
                for yy_, row in enumerate(face):
                    for xx_, ch in enumerate(row):
                        col = pal[ch]
                        if col:
                            px.putpixel((xx_, yy_), col + (255,))
                big = px.resize((24 * scale, 24 * scale), Image.NEAREST)
                img.paste(big, (gap + c * (24 * scale + gap), gap + r * (24 * scale + gap)), big)
                c += 1
    img.save(path)
    print('草稿图 ->', path, img.size)

if __name__ == '__main__':
    validate()
    render_sheet()
    for p, e, n in diff_vs_mirror():
        print(f'差异像素 {p} {e}: {n}')
