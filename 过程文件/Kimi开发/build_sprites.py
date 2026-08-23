#!/usr/bin/env python3
# 阶段3 R6: 脚底中心锚点(全姿态统一, 删除UWV头颈位例外) + 16x16身体(深色轮廓) + BREATH三帧身体
#          + DIVE三过程姿态(横卧/转向/垂直) + UW三态(H横卧/U头朝上/D头朝下蜷身)
#          + JUMP空中帧=横向飞扑(jp-action-c) + UW/DIVE侧脸头(HEAD_SIDE)与垂直头(HEAD_DOWN)
#          双人左右, 左向=翻转+人工修正(非精确镜像)
# 头像数据直接取自已跟踪的 avatar_paint.py/FACES (不依赖被忽略的 avatar_baked.js)
# 输出 sprites_baked.js + 校验(16x16/连通/轮廓/有效高度/脚底锚点边界/左右非镜像) + 组合预览PNG
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from avatar_paint import FACES

AVATAR = {who: {d: FACES[who][d]['正常'] for d in ('right', 'left')} for who in ('yy', 'dd')}

EMPTY16 = '.' * 16
EMPTY24 = '.' * 24

def rows(*rs):
    out = []
    for r in rs:
        assert len(r) == 16, f'row len {len(r)}: {r!r}'
        out.append(r)
    assert len(out) == 16, f'need 16 rows, got {len(out)}'
    return out

def rows24(*rs):
    out = []
    for r in rs:
        assert len(r) == 24, f'row24 len {len(r)}: {r!r}'
        out.append(r)
    assert len(out) == 24, f'need 24 rows, got {len(out)}'
    return out

# ---------------- BODY 全部 16x16 (O=深色轮廓 S=肤 s=肤暗 T=队色泳衣 W=白) ----------------
BODY = {}

# SURF: 水面漂浮划水两帧。颈/肩/胸+可读的手臂划水; 仅row0..5(水线以上), 以下没入水中。
# 身体放在组合(4,24), 组合顶=脚底-40; 脚底y=108时身体顶abs y=92, 水线≈96。
BODY['SURF'] = [
 rows('....OOOOOO......',   # 颈/肩 (接下巴)
      '...OSSSSSSO.....',
      '..OSSSTTTSSO....',   # 胸(T泳衣)
      '.OSSTTTTTTSOOOO.',   # 右臂前伸划水(带轮廓)
      '.OSTTTTTTSSSSSO.',
      '..OOOOOOOOOOOOO.',   # 水线底轮廓
      EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16),
 rows('....OOOOOO......',
      '...OSSSSSSO.....',
      '..OSSSTTTSSO....',
      '.OSOSSTTTTTTSO..',   # 左臂后摆划水
      'OSSSSTTTTTTTSO..',
      '.OOOOOOOOOOOOO..',
      EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16)]

# JUMP三帧 (JC/JF直立, 躯干+双臂+双腿, 有效高≥12; JA=横向飞扑, 见下)
BODY['JC'] = [   # 起跳蹲 (屈身, 臂后摆, 膝弯)
 rows('....OOOOOO......',
      '...OSSSSSSO.....',
      '..OOSSSSSSOO....',
      '..OSSTTTTTSO....',
      '.OSSSTTTTTSSO...',   # 臂在体侧
      '.OOTTTTTTTTOO...',
      '...OTTTTTTO.....',
      '...OSSSSSSO.....',   # 腿根
      '..OOSSSSSSOO....',   # 屈膝
      '..OSSO..OSSO....',
      '..OSO....OSO....',
      '..OOO....OOO....',   # 脚
      EMPTY16,EMPTY16,EMPTY16,EMPTY16)]
BODY['JA'] = [   # 滞空横向飞扑 (jp-action-c官方截图: 头前伸, 躯干水平, 臂前伸, 双腿前后分开)
                 # 组合38x24, head[14,0]=HEAD_SIDE侧脸头, body[0,6]; 身体col15/abs行13接头左缘
 rows('...OO...........',   # abs y6: 上踢脚跟
      '..OSSO..........',   # 上腿(向后上方)
      '..OSSSO.........',
      '..OSSSSO........',   # 双腿并到髋
      '.OSSSSTTTTO.....',   # 髋/泳裤
      '.OSSTTTTTTTO....',   # 躯干T(水平, 6行厚)
      '.OSTTTTTTTTO....',
      '.OSSSSSSSSSSSSSO',  # abs y13: 臂前伸至col15 接头(头左缘content abs x15)
      '.OSSSSSSSSSSSO..',  # 臂/腹
      '..OOOOOOOOOOOO..',   # 腹下轮廓
      '..OSSSSO........',   # 下伸腿根(向后下方)
      '..OSSSO.........',
      '.OSSO...........',   # 下踢小腿
      '.OOO............',
      EMPTY16,EMPTY16)]
BODY['JF'] = [   # 下落 (臂平伸, 腿半收) 有效高12
 rows('....OOOOOO......',
      '...OOSSSSOO.....',
      '.OOOOSSSSOOOO...',
      '.SSSSTTTTSSSSO..',
      '.OOOTTTTTTTOOO..',
      '....TTTTTTTT....',
      '....TTTTTTTT....',
      '...OSSSSSSSSO...',
      '...OSSSSSSSO....',   # 腿收拢
      '..OSS....SSO....',
      '..OSO....OSO....',
      '..OOO....OOO....',
      EMPTY16,EMPTY16,EMPTY16,EMPTY16)]

# DIVE 三过程姿态 (实测 f15615..f15620: 横卧准备→转向→垂直下沉):
# [0] 横卧准备 (组合38x24, head[14,0]=HEAD_SIDE, body[0,6]): 腿后伸, 躯干水平, 臂前伸
BODY_DIVE0 = rows(EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,EMPTY16,
      '..OO............',   # abs y6: 脚尖(后)
      '.OSSOOOO........',
      '.OSSSSOOOOO.....',   # 双腿并拢
      '.OSSSSTTTTTTO...',   # 躯干T
      '..OSSTTTTTTTTO..',
      '..O' + 'S'*12 + 'O',   # 臂前伸至col15 接头(abs y17)
      '..OSSSSSSSSSSO..',
      '..OOOOOOOOOOOO..',
      EMPTY16,EMPTY16)
# [1] 转向 (组合38x32, head[14,8]=HEAD_SIDE, body[0,6]): 腿后上翘起, 躯干斜向右下
BODY_DIVE1 = rows('..O.............',   # abs y6: 脚尖(后上)
      '.OSSO...........',   # 小腿
      '.OSSO...........',
      '.OSSSO..........',
      '..OSSSO.........',
      '..OSSSSO........',   # 双腿并
      '...OSSSSO.......',
      '...OSSSSO.......',   # 大腿
      '....OSSSOO......',   # 髋
      '....OSSTTTTO....',   # 躯干T 斜向右下
      '.....SSTTTTTO...',
      '......SSTTTTTOO.',
      '.......SSSTTTSSO',   # abs y18: 肩 → col15接头(16,18)
      '......OSSSSSSSSO',   # abs y19: 臂前伸至头下 col15接(16,19)
      '......OOOOOOOO..',   # 臂下轮廓
      EMPTY16)
# [2] 垂直下沉 (组合24x40, head[0,14]=HEAD_DOWN, body[4,0]): 腿上举, 躯干垂直, 肩下接头
BODY_DIVE2 = rows(
      '......OOOO......',   # abs y0: 双脚(并)
      '.....OSSSSO.....',   # 小腿
      '.....OSSSSO.....',
      '....OSSSSSSO....',
      '....OSSSSSO.....',   # 大腿
      '....OSSTTSO.....',   # 髋/泳裤
      '....OSTTTSO.....',
      '....OSTTTSO.....',   # 躯干
      '...OOSTTTSOO....',
      '...OSTTTTTSO....',
      '...OSTTTTTSO....',
      '...OSSSSSSSO....',   # 肩
      '...OSSSSSSSO....',
      '...OSSSSSSSO....',
      '..OSSSSSSSSSO...',   # 肩底 → abs y14 (头content起abs y16, 相邻)
      '..OOOOOOOOOOO...',   # 底轮廓 abs y15
      )
BODY['DIVE'] = [BODY_DIVE0, BODY_DIVE1, BODY_DIVE2]

# UW 普通水下游动两帧 (组合38x24, head[14,0]=HEAD_SIDE, body[0,7])
# 头有效像素最左在组合x=15..16, abs y7..21 → 身体col14..15在abs y11..17有像素即相接
BODY['UW'] = [
 rows(EMPTY16,
      '..OO............',   # abs y8: 脚尖上踢
      '.OSSO...........',
      '.OSSSO..........',
      '..OSSSO.........',   # 大腿
      '.....OOOOOOOOOOO',   # abs y12: 躯干上轮廓 cols5..15
      '....OSSSTTTTTTSO',   # 躯干(肤+T泳衣) cols4..15 — col15邻头
      '...OSSTTTTTTTTSO',
      '...OSSTTTTTTTTSO',
      '..OSSSSSSSSSSSSO',   # 腹
      '..OOOOOOOOOOOOOO',   # 下轮廓
      '........OOOOO...',   # 前伸臂(划水)
      '.......OSSSSSO..',
      EMPTY16,EMPTY16,EMPTY16),
 rows(EMPTY16,EMPTY16,EMPTY16,EMPTY16,
      '.....OOOOOOOOOOO',   # abs y11: 躯干上轮廓
      '....OSSSTTTTTTSO',
      '...OSSTTTTTTTTSO',
      '...OSSTTTTTTTTSO',
      '..OSSSSSSSSSSSSO',
      '..OOOOOOOOOOOOOO',   # 下轮廓 abs y16
      '...OOOOO........',   # 腿根下伸
      '..OSSSSO........',
      '..OSSSSO........',   # 腿下踢
      '.OSSSO..........',
      '.OSSO...........',
      '.OOO............')]

# UW 加速两帧: 流线型(双臂前伸过肩, 腿并拢直), 与普通帧明显不同
BODY['UWB'] = [
 rows(EMPTY16,EMPTY16,
      '..........OOOOO.',   # abs y9: 双臂前伸(头下方)
      '.........OSSSSSO',
      '....OOOOOSSSSSOO',   # 躯干上轮廓+臂
      '....SSTTTTTTTTSO',
      '...OSSTTTTTTTTSO',
      '...SSTTTTTTTTSO.',
      '..OSSSSSSSSSSO..',   # 腹
      '.OSSSSSSOOOOO...',   # 腿并拢直伸(与腹相连)
      '.OSSSSSO........',
      '..OOOOO.........',
      EMPTY16,EMPTY16,EMPTY16,EMPTY16),
 rows(EMPTY16,EMPTY16,
      '..........OOOOO.',
      '.........OSSSSSO',
      '....OOOOOSSSSSOO',
      '....SSTTTTTTTTSO',
      '...OSSTTTTTTTTSO',
      '...SSTTTTTTTTSO.',
      '..OSSSSSSSSSSO..',
      '..OSSSSOOOOO....',   # 腿剪刀踢(上分)
      '.OSSSO..........',
      '.OSSSO..........',   # 下分
      '..OOO...........',
      EMPTY16,EMPTY16,EMPTY16)]

# UW 竖直悬浮/垂直移动身体 (实测 f15668..f15680: 无横向输入时水下呈竖直俯身团+气泡):
# 组合24x30, head[0,6]=HEAD_DOWN(头朝下), body[4,0]在上: 背朝上, 双腿向后上方蜷起
BODY['UWV'] = [
 rows('......OOO.......',   # abs y0: 脚尖(向后翘起)
      '.....OSSSO......',   # 小腿(向后上方)
      '.....OSSSO......',
      '....OSSSSO......',
      '....OSSSSO......',   # 大腿(蜷收)
      '....OSSTSO......',   # 髋/泳裤
      '...OSSTTSSO.....',   # 躯干(微弓)
      '...OSTTTTSO.....',
      '...OSTTTTSO.....',
      '...OSTTTTSSO....',   # 肩(略宽)
      '...OSSSSSSSO....',
      '...OSSSSSSSO....',   # 肩底 → abs y11 (头content起abs y9, 相交相接)
      '....OSSSSSO.....',   # 臂贴体前
      '....OOOOOOO.....',   # 底轮廓 abs y13
      EMPTY16,EMPTY16)]

# EMERGE 上浮出水 (直立仰身, 臂半张, 有效高13)
BODY['EMERGE'] = [
 rows('....OOOOOO......',
      '...OOSSSSOO.....',
      '..OOSSSSSSOO....',
      '.OSSSTTTTSSSO...',   # 臂半张
      '.OSOTTTTTTOSO...',
      '..OSTTTTTTTSO...',
      '..OOTTTTTTTOO...',
      '....TTTTTTTT....',
      '...OSSSSSSSSO...',
      '...OSSSSSSO.....',
      '...OSS..SSO.....',
      '...OSO..OSO.....',
      '...OOO..OOO.....',
      EMPTY16,EMPTY16,EMPTY16)]

# BREATH 超级换气三帧身体 (独立): 挺起/展臂大口/回落 (有效高≥12)
BODY['BREATH'] = [
 rows('....OOOOOO......',   # f0 挺起: 臂弯举, 胸挺
      '...OOSSSSOO.....',
      '..OOSSSSSSOO....',
      '.OSSSTTTTSSSO...',
      '.OSSTTTTTTSSO...',
      '..OTTTTTTTTO....',
      '...TTTTTTTT.....',
      '...TTTTTTTT.....',
      '...OSSSSSSO.....',
      '...OSSSSSO......',
      '...OSS.SSO......',
      '...OOO.OOO......',
      EMPTY16,EMPTY16,EMPTY16,EMPTY16),
 rows('....OOOOOO......',   # f1 顶峰: 双臂完全水平展开(T-pose), 大口
      '...OOSSSSOO.....',
      '.OOOOSSSSOOOO...',
      'OSSSSTTTTTSSSSSO',   # 全宽展臂
      '.OOOTTTTTTTOOO..',
      '....TTTTTTTT....',
      '....TTTTTTTT....',
      '...OSSSSSSSSO...',
      '...OSSSSSSO.....',
      '...OSS..SSO.....',
      '...OSO..OSO.....',
      '...OOO..OOO.....',
      EMPTY16,EMPTY16,EMPTY16,EMPTY16),
 rows('....OOOOOO......',   # f2 回落: 臂落下, 体略收
      '...OOSSSSOO.....',
      '..OOSSSSSSOO....',
      '.OSSSTTTTSSSO...',
      '.OSOTTTTTTOSO...',
      '..OOTTTTTTOO....',
      '....TTTTTTTT....',
      '...TTTTTTTT.....',
      '...OSSSSSSO.....',
      '...OSSSSO.......',
      '...OOSSOO.......',
      '....OOOO........',
      EMPTY16,EMPTY16,EMPTY16,EMPTY16)]

# SPLASH 独立 8x4
SPLASH = [
 ['..W..W..',
  '.WW..WW.',
  'W..WW..W',
  'W......W'],
 ['W......W',
  'W..WW..W',
  '........',
  '........']]

# ---------------- 水下/下潜用头 (24x24, 右向基准; 阶段2身份特征+同调色板) ----------------
# HEAD_SIDE: 侧脸游泳头(脸朝右); 泳帽/头发在后(左), 脸在前(右); UW与DIVE[0]/DIVE[1]用
# HEAD_DOWN: 垂直下潜头(脸朝下, 只见头顶); 泳帽/头顶发+头带/镜腿, 下颌肤收于底部; DIVE[2]用
# 段构建器: (列,文本) 填入24列行, 杜绝手工数列出错
def R24(*segs):
    row = ['.'] * 24
    for col, text in segs:
        for i, ch in enumerate(text):
            assert 0 <= col + i < 24, f'col overflow: {col}+{i}'
            row[col + i] = ch
    return ''.join(row)

def H24(*rs):
    out = list(rs)
    assert len(out) <= 24, f'need <=24 rows, got {len(out)}'
    out = ['.' * 24] * (24 - len(out)) + [] and (['.' * 24] * (24 - len(out)) + out)  # 头部内容画在前面的行, 尾部补空行? 不: 内容应在顶部
    return out

HEAD_SIDE, HEAD_DOWN = {}, {}

HEAD_SIDE['yy'] = [
 R24(), R24(),
 R24((5,'OOOOOOOOO')),                            # 泳帽顶(偏后)
 R24((3,'OO'), (5,'C'*9), (14,'OO')),
 R24((2,'O'), (3,'C'*12), (15,'OO')),
 R24((2,'O'), (3,'CCCc'), (7,'C'*8), (15,'S'), (16,'O')),   # 脸前沿
 R24((1,'O'), (2,'C'*13), (15,'SS'), (17,'O')),
 R24((1,'O'), (2,'C'*13), (15,'SS'), (17,'O')),
 R24((1,'O'), (2,'W'*13), (15,'dd'), (17,'O')),   # 泳镜带W横贯+镜框d
 R24((1,'O'), (2,'W'*13), (15,'dd'), (17,'O')),
 R24((1,'O'*15), (16,'S'), (17,'O')),             # 带下沿轮廓
 R24((1,'O'), (2,'S'*14), (16,'O')),              # 脸颊
 R24((1,'O'), (2,'S'), (3,'s'), (4,'S'*11), (15,'O')),
 R24((1,'O'), (2,'S'*13), (15,'O')),
 R24((1,'O'), (2,'S'*10), (12,'d'), (13,'SS'), (15,'O')),   # 鼻/嘴
 R24((1,'O'), (2,'s'), (3,'S'*12), (15,'O')),
 R24((1,'O'), (2,'S'*11), (13,'O')),
 R24((2,'S'*10), (12,'s'), (13,'O')),             # 下颚
 R24((2,'s'), (3,'S'*8), (11,'s'), (12,'O')),
 R24((3,'s'), (4,'S'*5), (9,'s'), (10,'O')),
 R24((4,'s'), (5,'S'*3), (8,'s'), (9,'O')),
 R24((5,'sss'), (8,'O')),
 R24(), R24()]

HEAD_SIDE['dd'] = [
 R24(), R24(),
 R24((5,'O'*10)),                                 # 头发顶(偏后)
 R24((3,'OO'), (5,'H'*9), (14,'OOO')),
 R24((2,'O'), (3,'H'*13), (16,'O')),
 R24((2,'O'), (3,'HHh'), (6,'H'*10), (16,'S'), (17,'O')),
 R24((1,'O'), (2,'H'*14), (16,'SS'), (18,'O')),
 R24((1,'O'), (2,'H'*14), (16,'SS'), (18,'O')),
 R24((1,'O'), (2,'h'*14), (16,'dd'), (18,'O')),   # 眼镜腿(h暗)横贯到镜框
 R24((1,'O'), (2,'H'*13), (15,'W'), (16,'S'), (17,'d'), (18,'O')),   # 镜片W高光
 R24((1,'O'*15), (16,'S'), (17,'O')),
 R24((1,'O'), (2,'S'*14), (16,'O')),              # 脸颊
 R24((1,'O'), (2,'S'*13), (15,'O')),
 R24((1,'O'), (2,'S'), (3,'s'), (4,'S'*11), (15,'O')),
 R24((1,'O'), (2,'S'*13), (15,'O')),
 R24((1,'O'), (2,'S'*7), (9,'dd'), (11,'S'*4), (15,'O')),   # 微笑(爸爸特征)
 R24((1,'O'), (2,'s'), (3,'S'*11), (14,'O')),
 R24((2,'S'*10), (12,'s'), (13,'O')),
 R24((2,'s'), (3,'S'*8), (11,'s'), (12,'O')),
 R24((3,'s'), (4,'S'*5), (9,'s'), (10,'O')),
 R24((4,'ssss'), (8,'O')),
 R24((5,'sss'), (8,'O')),
 R24(), R24()]

HEAD_DOWN['yy'] = [
 R24(), R24(), R24(),
 R24((6,'O'*7)),                                  # 头顶(泳帽)
 R24((4,'OO'), (6,'C'*7), (13,'OO')),
 R24((3,'O'), (4,'C'*11), (15,'O')),
 R24((2,'O'), (3,'C'*3), (6,'c'), (7,'C'*3), (10,'c'), (11,'C'*4), (15,'O')),
 R24((2,'O'), (3,'C'*12), (15,'O')),
 R24((2,'O'), (3,'W'*12), (15,'O')),              # 泳镜带环绕
 R24((2,'O'), (3,'C'*12), (15,'O')),
 R24((2,'O'), (3,'C'*12), (15,'O')),
 R24((2,'O'), (3,'C'*12), (15,'O')),
 R24((2,'O'), (3,'CC'), (5,'O'*9), (14,'C'), (15,'O')),   # 帽底缘
 R24((2,'O'), (3,'SS'), (5,'O'*9), (14,'S'), (15,'O')),   # 颌侧肤(脸朝下, 只见底缘)
 R24((2,'O'), (3,'S'*12), (15,'O')),
 R24((2,'O'), (3,'S'*11), (14,'O')),
 R24((3,'O'), (4,'S'*9), (13,'O')),
 R24((4,'O'), (5,'ss'), (7,'S'*5), (12,'s'), (13,'O')),
 R24((5,'O'), (6,'s'*6), (12,'O')),
 R24((6,'O'), (7,'s'*4), (11,'O')),
 R24((7,'O'), (8,'ss'), (10,'O')),
 R24((8,'O'), (9,'sO')),
 R24(), R24()]

HEAD_DOWN['dd'] = [
 R24(), R24(), R24(),
 R24((6,'O'*7)),                                  # 头顶发
 R24((4,'OO'), (6,'H'*7), (13,'OOO')),
 R24((3,'O'), (4,'H'*12), (16,'O')),
 R24((2,'O'), (3,'H'*4), (7,'h'), (8,'H'*3), (11,'h'), (12,'H'*4), (16,'O')),
 R24((2,'O'), (3,'H'*13), (16,'O')),
 R24((2,'O'), (3,'h'), (4,'H'*11), (15,'h'), (16,'O')),   # 眼镜腿两端
 R24((2,'O'), (3,'H'*13), (16,'O')),
 R24((2,'O'), (3,'H'*13), (16,'O')),
 R24((2,'O'), (3,'H'*13), (16,'O')),
 R24((2,'O'), (3,'HH'), (5,'O'*9), (14,'HH'), (16,'O')),  # 发底缘
 R24((2,'O'), (3,'SS'), (5,'O'*9), (14,'SS'), (16,'O')),  # 颌侧肤
 R24((2,'O'), (3,'S'*13), (16,'O')),
 R24((2,'O'), (3,'S'*12), (15,'O')),
 R24((3,'O'), (4,'S'*9), (13,'O')),
 R24((4,'O'), (5,'ss'), (7,'S'*5), (12,'s'), (13,'O')),
 R24((5,'O'), (6,'s'*6), (12,'O')),
 R24((6,'O'), (7,'s'*4), (11,'O')),
 R24((7,'O'), (8,'ss'), (10,'O')),
 R24((8,'O'), (9,'sO')),
 R24(), R24()]

for who in ('yy','dd'):
    for nm, HS in (('HEAD_SIDE',HEAD_SIDE), ('HEAD_DOWN',HEAD_DOWN)):
        m = HS[who]
        assert len(m) == 24, f'{nm}.{who}: {len(m)} rows'
        for i, r in enumerate(m):
            assert len(r) == 24, f'{nm}.{who} row{i} len={len(r)}'

# 左向 = 逐像素翻转 + 人工修正(高光/明暗, 禁止精确镜像); 修正点在填充色格上切换明暗
def mirror(m): return [r[::-1] for r in m]
def fix(m, ops):
    g = [list(r) for r in m]
    for (r, c, ch) in ops:
        assert g[r][c] not in ('.', 'O'), f'fix on empty/outline: r{r}c{c}={g[r][c]!r}'
        g[r][c] = ch
    return [''.join(r) for r in g]

FIX_SIDE = {   # 固定左上来光: 翻转后修正帽/发/肤明暗与镜高光, 使左向稿光源一致
 'yy': [(5,19,'c'),(6,20,'C'),(11,20,'s'),(14,11,'d'),(18,20,'s')],
 'dd': [(5,20,'h'),(6,21,'H'),(9,20,'W'),(12,20,'s'),(15,13,'d')],
}
FIX_DOWN = {
 'yy': [(6,13,'c'),(6,9,'C'),(8,10,'W'),(17,12,'s')],
 'dd': [(6,12,'h'),(6,8,'H'),(8,9,'h'),(17,11,'s')],
}
for who in ('yy','dd'):
    HEAD_SIDE[who] = {'right': HEAD_SIDE[who],
                      'left': fix(mirror(HEAD_SIDE[who]), FIX_SIDE[who])}
    HEAD_DOWN[who] = {'right': HEAD_DOWN[who],
                      'left': fix(mirror(HEAD_DOWN[who]), FIX_DOWN[who])}

# ---------------- LAY: 锚点=脚底中心(组合底缘中心), 全姿态统一 ----------------
# 水平/竖直姿态统一: anchor=组合底缘中心(删除R5的UWV头颈位例外); 状态切换只改绘制原点, 逻辑锚点不动
LAY = {
 'SURF':   dict(w=24,h=40,anchorX=12,anchorY=40,head=[0,0], body=[4,24]),
 'JUMP':  [dict(w=24,h=40,anchorX=12,anchorY=40,head=[0,0], body=[4,24]),    # JC 起跳蹲(直立)
           dict(w=38,h=24,anchorX=19,anchorY=24,head=[14,0],body=[0,6]),    # JA 横向飞扑(侧脸头+水平身, jp-action-c)
           dict(w=24,h=40,anchorX=12,anchorY=40,head=[0,0], body=[4,24])],   # JF 下落(直立)
 'BREATH': dict(w=24,h=40,anchorX=12,anchorY=40,head=[0,0], body=[4,24]),
 'DIVE':  [dict(w=38,h=24,anchorX=19,anchorY=24,head=[14,0],body=[0,6]),    # 横卧准备
           dict(w=38,h=32,anchorX=19,anchorY=32,head=[14,8],body=[0,6]),    # 转向
           dict(w=24,h=40,anchorX=12,anchorY=40,head=[0,13],body=[4,0])],   # 垂直下沉
 'UW':     dict(w=38,h=24,anchorX=19,anchorY=24,head=[14,0],body=[0,7]),
 'UWV':    dict(w=24,h=40,anchorX=12,anchorY=40,head=[0,16],body=[4,5]),   # 头朝下蜷身(纯↓/悬浮); 统一脚底锚点24x40; 头身abs行18/19相接
 'EMERGE': dict(w=24,h=40,anchorX=12,anchorY=40,head=[0,0], body=[4,24]),   # 兼作UW纯↑头朝上姿态(水下青蓝)
}
HEAD_DY = {'yy':0, 'dd':2}   # 仅正脸头: dd下巴有效行短2px, 下移2px与身体相接; 侧脸/垂直头直接按组合设计, 不加

# 各状态/帧选用的头: ('AV'=正脸, 'BR0/BR1'=换气帧, 'SIDE'=侧脸, 'DOWN'=垂直)
def head_for(state, fi=0):
    if state == 'UW': return 'SIDE'
    if state == 'DIVE': return 'DOWN' if fi == 2 else 'SIDE'
    if state == 'JUMP': return 'SIDE' if fi == 1 else 'AV'   # 空中帧=横向飞扑(侧脸头)
    return 'AV'

def get_head(kind, who, d):
    if kind == 'SIDE': return HEAD_SIDE[who][d]
    if kind == 'DOWN': return HEAD_DOWN[who][d]
    return AVATAR[who][d]

# 脚底锚点纵向域(与状态机一致): SURF脚底y=108(水线≈96, 没入12px); UW全姿态统一域[120,166](删uwVert例外)
AY_RANGE = {'SURF':(108,108),'BREATH':(96,108),'JUMP':(80,108),
            'DIVE':(108,120),'UW':(120,166),'UWV':(120,166),'EMERGE':(108,120)}

# ---------------- AVATAR_BREATH: 嘴部patch两帧 (与R3相同, 双人左右) ----------------
def patch(rows_in, ops):
    g = [list(r) for r in rows_in]
    for (r, c0, c1, ch) in ops:
        for c in range(c0, c1+1):
            g[r][c] = ch
    return [''.join(r) for r in g]

PATCH = {
 ('yy','right'): [
   [(19,9,11,'O'),(20,9,11,'O')],
   [(19,8,12,'O'),(20,9,11,'O')],
 ],
 ('yy','left'): [
   [(19,11,13,'O'),(20,11,13,'O')],
   [(19,10,14,'O'),(20,11,13,'O')],
 ],
 ('dd','right'): [
   [(16,9,12,'O'),(17,8,15,'S'),(17,10,11,'O')],
   [(15,10,12,'O'),(16,8,12,'O'),(17,8,15,'S'),(17,9,12,'O')],
 ],
 ('dd','left'): [
   [(16,11,14,'O'),(17,8,15,'S'),(17,12,13,'O')],
   [(15,11,13,'O'),(16,11,15,'O'),(17,8,15,'S'),(17,11,14,'O')],
 ],
}
AVATAR_BREATH = {}
for who in ('yy','dd'):
    AVATAR_BREATH[who] = {}
    for d in ('right','left'):
        base = AVATAR[who][d]
        AVATAR_BREATH[who][d] = [patch(base, PATCH[(who,d)][0]),
                                 patch(base, PATCH[(who,d)][1])]

# ---------------- 校验 ----------------
errs = []

def eff_bbox(m):
    xs=[]; ys=[]
    for r in range(len(m)):
        for q in range(len(m[r])):
            if m[r][q] != '.': xs.append(q); ys.append(r)
    if not xs: return None
    return (min(xs),min(ys),max(xs),max(ys))

# 0) 新头: 24x24 + 左右非精确镜像 + 与正脸不同
for name, HS in (('HEAD_SIDE',HEAD_SIDE), ('HEAD_DOWN',HEAD_DOWN)):
    for who in ('yy','dd'):
        for d in ('right','left'):
            m = HS[who][d]
            for i, r in enumerate(m):
                if len(r) != 24: errs.append(f'{name}.{who}.{d} row{i} len={len(r)}')
        if mirror(HS[who]['right']) == HS[who]['left']:
            errs.append(f'{name}.{who} 左右互为精确镜像')
        ndiff = sum(1 for r in range(24) for q in range(24)
                    if mirror(HS[who]['right'])[r][q] != HS[who]['left'][r][q])
        print(f'{name}.{who}: 左右差异={ndiff}px (须>0)')
        if HS[who]['right'] == AVATAR[who]['right'] or HS[who]['left'] == AVATAR[who]['left']:
            errs.append(f'{name}.{who} 与正脸相同')

# 1) 每帧: 16x16(行断言已保证) + 深色轮廓O存在 + 有效像素高度达标 + 不做机械填满
EFF_MIN = {'SURF':5,'JC':12,'JA':12,'JF':12,'UW':8,'UWB':8,'UWV':12,'EMERGE':12,'BREATH':12}
EFF_MIN_DIVE = [6,12,14]   # 横卧/转向/垂直
O_MIN   = {'SURF':8,'JC':14,'JA':14,'JF':14,'UW':10,'UWB':10,'UWV':12,'EMERGE':12,'BREATH':12}
O_MIN_DIVE = [8,10,12]
print('== 身体帧有效包围盒/轮廓 ==')
for k, frames in BODY.items():
    for i, m in enumerate(frames):
        bb = eff_bbox(m)
        h = bb[3]-bb[1]+1; wdt = bb[2]-bb[0]+1
        oc = sum(r.count('O') for r in m)
        tot = sum(1 for r in m for ch in r if ch != '.')
        print(f'{k}[{i}]: bbox x{bb[0]}..{bb[2]} y{bb[1]}..{bb[3]} w{wdt} h{h} O={oc} 有效={tot}')
        th = EFF_MIN_DIVE[i] if k=='DIVE' else EFF_MIN[k]
        oth = O_MIN_DIVE[i] if k=='DIVE' else O_MIN[k]
        if h < th: errs.append(f'{k}[{i}] 有效高{h}<{th}')
        if oc < oth: errs.append(f'{k}[{i}] 轮廓O={oc}<{oth}')

def composite_lay(lay, who, d, bodym, headm, head_dy=0):
    grid = [[None]*lay['w'] for _ in range(lay['h'])]
    hx, hy = lay['head']; bx, by = lay['body']
    if d == 'left':
        hx = lay['w'] - hx - 24
        bx = lay['w'] - bx - 16
        bodym = mirror(bodym)
    hy += head_dy
    hc=set(); bc=set()
    for r in range(24):
        for q in range(24):
            k = headm[r][q]
            if k != '.':
                x,y = hx+q, hy+r
                if 0<=x<lay['w'] and 0<=y<lay['h']: grid[y][x]=k; hc.add((x,y))
                else: errs.append(f'{who}/{d}: head px out {x},{y}')
    for r in range(16):
        for q in range(16):
            k = bodym[r][q]
            if k != '.':
                x,y = bx+q, by+r
                if 0<=x<lay['w'] and 0<=y<lay['h']:
                    if grid[y][x] is None: grid[y][x]=k
                    bc.add((x,y))
                else: errs.append(f'{who}/{d}: body px out {x},{y}')
    return grid, hc, bc

def connected(cells):
    cells = set(cells); n = 0
    while cells:
        n += 1
        stack = [cells.pop()]
        while stack:
            x,y = stack.pop()
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    p = (x+dx,y+dy)
                    if p in cells: cells.discard(p); stack.append(p)
    return n

# 2) 组合连通: (状态,帧,身体,布局,头) 全组合 x 双人 x 左右
print('== 组合连通 ==')
checks = []
def add(state, fi, bodym, lay, headkind):
    checks.append((state, fi, bodym, lay, headkind))
for fi, bm in enumerate(BODY['SURF']): add('SURF', fi, bm, LAY['SURF'], 'AV')
for fi, bk in enumerate(('JC','JA','JF')): add('JUMP', fi, BODY[bk][0], LAY['JUMP'][fi], head_for('JUMP', fi))
for fi, bm in enumerate(BODY['DIVE']): add('DIVE', fi, bm, LAY['DIVE'][fi], head_for('DIVE', fi))
for fi, bm in enumerate(BODY['UW']): add('UW', fi, bm, LAY['UW'], 'SIDE')
for fi, bm in enumerate(BODY['UWB']): add('UW', f'B{fi}', bm, LAY['UW'], 'SIDE')
add('UW', 'V', BODY['UWV'][0], LAY['UWV'], 'DOWN')   # 头朝下蜷身: HEAD_DOWN+蜷腿身(统一脚底锚点)
add('EMERGE', 0, BODY['EMERGE'][0], LAY['EMERGE'], 'AV')   # 兼UW纯↑头朝上姿态
for fi, bm in enumerate(BODY['BREATH']): add('BREATH', fi, bm, LAY['BREATH'], 'AV')
for state, fi, bm, lay, hk in checks:
    for who in ('yy','dd'):
        for d in ('right','left'):
            hdy = HEAD_DY[who] if hk == 'AV' else 0
            grid, hc, bc = composite_lay(lay, who, d, bm, get_head(hk, who, d), hdy)
            nc = connected(hc | bc)
            touch = any((x+dx,y+dy) in bc for (x,y) in hc for dx in (-1,0,1) for dy in (-1,0,1))
            tag = f'{state}[{fi}]/{who}/{d}'
            if nc != 1: errs.append(f'{tag}: 连通域={nc}')
            if not touch: errs.append(f'{tag}: 头身不相邻')
print(f'组合连通检查 {len(checks)*4} 例完成')

# BREATH头像 差异断言
for who in ('yy','dd'):
    for d in ('right','left'):
        base = AVATAR[who][d]
        for fi in range(2):
            fr = AVATAR_BREATH[who][d][fi]
            diff = sum(1 for r in range(24) for q in range(24) if base[r][q]!=fr[r][q])
            if diff == 0: errs.append(f'breath {who}/{d}/f{fi} 与normal无差异')
            print(f'breath {who}.{d} f{fi}: diff={diff}px')
        d01 = sum(1 for r in range(24) for q in range(24)
                  if AVATAR_BREATH[who][d][0][r][q]!=AVATAR_BREATH[who][d][1][r][q])
        if d01 == 0: errs.append(f'breath {who}/{d} 两帧相同')
        print(f'breath {who}.{d} 帧间差异={d01}px')

# 3) 脚底锚点边界: ax∈[20,236], ay按AY_RANGE → origin∈[0,256-w]x[0,168-h]
print('== 脚底锚点边界 ==')
for state,lay in LAY.items():
    lays = lay if isinstance(lay, list) else [lay]
    for li, ly in enumerate(lays):
        ay0,ay1 = AY_RANGE[state]
        ox0 = 20-ly['anchorX']; ox1 = 236-ly['anchorX']
        oy0 = ay0-ly['anchorY']; oy1 = ay1-ly['anchorY']
        ok = (0<=ox0 and ox1+ly['w']<=256 and 0<=oy0 and oy1+ly['h']<=168)
        tag = f'{state}[{li}]' if isinstance(lay, list) else state
        print(f"{tag}: origin x {ox0}..{ox1} y {oy0}..{oy1} +w/h {ly['w']}x{ly['h']} -> {'OK' if ok else 'CLIP!'}")
        if not ok: errs.append(f'{tag} 越界')

# ---------------- 预览PNG ----------------
PALV = {'O':'#000000','S':'#FCB88C','s':'#D88A58','d':'#B06840','W':'#FCFCFC',
        'C':'#3C9CF0','c':'#1E5AA8','H':'#38241A','h':'#5C4030','T':'#F83800'}
S=6
def panel(lay, bodym, headkind, label):
    sh=Image.new('RGB',(lay['w']*S*2+40, lay['h']*S+22),(24,24,32))
    dr=ImageDraw.Draw(sh)
    for i,who in enumerate(('yy','dd')):
        hdy = HEAD_DY[who] if headkind == 'AV' else 0
        grid,_,_=composite_lay(lay,who,'right',bodym,get_head(headkind,who,'right'),hdy)
        ox = i*(lay['w']*S+20)+10
        for y in range(lay['h']):
            for x in range(lay['w']):
                k=grid[y][x]
                if k: dr.rectangle([ox+x*S, 20+y*S, ox+x*S+S-1, 20+y*S+S-1], fill=PALV[k])
        dr.rectangle([ox,20,ox+lay['w']*S-1,20+lay['h']*S-1],outline=(60,60,80))
        ax, ay = lay['anchorX'], lay['anchorY']
        dr.line([ox+ax*S-4, 20+ay*S-1, ox+ax*S+4, 20+ay*S-1], fill=(255,0,0))
        dr.line([ox+ax*S, 20+ay*S-5, ox+ax*S, 20+ay*S+3], fill=(255,0,0))
    dr.text((4,4),f'{label} {lay["w"]}x{lay["h"]} foot-anchor({lay["anchorX"]},{lay["anchorY"]}) yy|dd',fill=(255,255,0))
    return sh

def head_panel(headset, label):
    sh=Image.new('RGB',(24*S*4+50, 24*S+22),(24,24,32))
    dr=ImageDraw.Draw(sh)
    i=0
    for who in ('yy','dd'):
        for d in ('right','left'):
            m = headset[who][d]
            ox = i*(24*S+10)+10
            for y in range(24):
                for x in range(24):
                    k=m[y][x]
                    if k!='.': dr.rectangle([ox+x*S, 20+y*S, ox+x*S+S-1, 20+y*S+S-1], fill=PALV[k])
            dr.rectangle([ox,20,ox+24*S-1,20+24*S-1],outline=(60,60,80))
            i+=1
    dr.text((4,4),f'{label} yyR yyL ddR ddL',fill=(255,255,0))
    return sh

panels = []
for fi,bm in enumerate(BODY['SURF']): panels.append(panel(LAY['SURF'],bm,'AV',f'SURF[{fi}]'))
for fi,bk in enumerate(('JC','JA','JF')): panels.append(panel(LAY['JUMP'][fi],BODY[bk][0],head_for('JUMP',fi),f'JUMP[{bk}]'))
for fi,bm in enumerate(BODY['DIVE']): panels.append(panel(LAY['DIVE'][fi],bm,head_for('DIVE',fi),f'DIVE[{fi}]'))
for fi,bm in enumerate(BODY['UW']): panels.append(panel(LAY['UW'],bm,'SIDE',f'UW[{fi}]'))
for fi,bm in enumerate(BODY['UWB']): panels.append(panel(LAY['UW'],bm,'SIDE',f'UW-BOOST[{fi}]'))
panels.append(panel(LAY['UWV'],BODY['UWV'][0],'DOWN','UW-DOWN(纯↓/悬浮)'))
panels.append(panel(LAY['EMERGE'],BODY['EMERGE'][0],'AV','EMERGE/UW-UP(纯↑)'))
for fi,bm in enumerate(BODY['BREATH']): panels.append(panel(LAY['BREATH'],bm,'AV',f'BREATH[{fi}]'))
panels.append(head_panel(HEAD_SIDE,'HEAD_SIDE'))
panels.append(head_panel(HEAD_DOWN,'HEAD_DOWN'))
W=max(p.size[0] for p in panels); H=sum(p.size[1] for p in panels)+8*len(panels)
out=Image.new('RGB',(W,H),(16,16,20))
y=0
for p in panels: out.paste(p,(0,y)); y+=p.size[1]+8
out.save(HERE/'sprites_preview.png')

# ---------------- 输出 JS ----------------
def js_body():
    o='const BODY = {\n'
    for k,frames in BODY.items():
        o+=f'{k}: [\n'
        for m in frames:
            o+=' ['+',\n '.join(json.dumps(r) for r in m)+'],\n'
        o+='],\n'
    o+='};\nconst SPLASH = [\n'
    for m in SPLASH:
        o+=' ['+',\n '.join(json.dumps(r) for r in m)+'],\n'
    o+='];\n'
    return o

def js_lay1(k, v):
    return f"  {k}: {{ w:{v['w']}, h:{v['h']}, anchorX:{v['anchorX']}, anchorY:{v['anchorY']}, head:[{v['head'][0]},{v['head'][1]}], body:[{v['body'][0]},{v['body'][1]}] }},\n"

def js_lay():
    o='const LAY = {\n'
    for k,v in LAY.items():
        if isinstance(v, list):
            o+=f'  {k}: [\n'
            for vv in v:
                o+='   '+js_lay1('', vv).lstrip().replace(': {',':{',1).replace('  ', ' ', 1).replace(',', '', 1) if False else '   { w:%d, h:%d, anchorX:%d, anchorY:%d, head:[%d,%d], body:[%d,%d] },\n' % (vv['w'],vv['h'],vv['anchorX'],vv['anchorY'],vv['head'][0],vv['head'][1],vv['body'][0],vv['body'][1])
            o+='  ],\n'
        else:
            o+=js_lay1(k, v)
    o+='};\nconst HEAD_DY = { yy:0, dd:2 };\n'
    return o

open(HERE/'sprites_baked.js','w').write(
    js_body()+js_lay()
    +'const HEAD_SIDE = '+json.dumps(HEAD_SIDE)+';\n'
    +'const HEAD_DOWN = '+json.dumps(HEAD_DOWN)+';\n'
    +'const AVATAR_BREATH = '+json.dumps(AVATAR_BREATH)+';\n')
print('\nwrote sprites_baked.js, sprites_preview.png')
if errs:
    print('\nERRORS:'); [print(' -',e) for e in errs]; sys.exit(1)
print('ALL CHECKS PASS')
