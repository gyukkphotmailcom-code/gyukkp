#!/usr/bin/env python3
# 历史失败稿：禁止运行或接入。其f15625 UW证据为两人合体，24×24 socket工艺也未通过。
# 当前入口仅为 build_sprites_3a0.py；本文件保留用于审计旧迭代。
# 阶段3A: 身体精灵重建 — 取消16x16统一约束, 逐动作可变尺寸完整人体轮廓
#   16张动作精灵: SURF×2 / JUMP×3 / DIVE×3 / UW×2 / BOOST×2 / UWUP / UWDN / EMERGE / BREATH×3
#   脸=完整精灵中的可替换区域(face_rect 24x24 socket), 身体逐像素作画, 锚点统一=脚底中心(w//2,h)
#   入水/出水调色: 审核表8倍演示栏按演示footY摆放后, 逐像素判断 世界y>96 → UW_MAP (非整状态变蓝)
#   复用阶段3数据: import build_sprites as bs (AVATAR/HEAD_SIDE/HEAD_DOWN/mirror/fix/PALV)
#   输出: sprites_3a_baked.js + 阶段3A精灵审核表-1/2.png + 阶段3A精灵清单.md
#   本轮不接主程序。任意目录可运行, 重复运行幂等。
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_sprites as bs   # import 即执行其自检并重写 sprites_baked.js/sprites_preview.png (幂等)

AVATAR, HEAD_SIDE, HEAD_DOWN = bs.AVATAR, bs.HEAD_SIDE, bs.HEAD_DOWN
mirror, HEAD_DY = bs.mirror, bs.HEAD_DY

# ---------------- 段构建器 (列,文本) + 帧收集器, 杜绝手数列宽 ----------------
def RB(w):
    def build(*segs):
        row = ['.'] * w
        for col, text in segs:
            for i, ch in enumerate(text):
                assert 0 <= col + i < w, f'col overflow: {col}+{i} w={w}'
                row[col + i] = ch
        return ''.join(row)
    return build

def FR(w, h):
    def build(*rs):
        out = list(rs)
        assert len(out) == h, f'need {h} rows, got {len(out)}'
        for i, r in enumerate(out):
            assert len(r) == w, f'row{i} len {len(r)} != {w}: {r!r}'
        return out
    return build

# ---------------- BODY 逐帧作画 (可变尺寸; O=深色轮廓 S=肤 s=肤暗 T=队色泳衣) ----------------
BODY = {}   # name -> rows (右向基准)

# SURF0: 水面俯泳划水相1 (ref f16063) 16x16: 胸+双臂划水+并腿没入水(腿向后下斜伸)
BODY['SURF0'] = FR(16,16)(
 '....OOOOOO......',   # 颈/肩 (垫在下巴下)
 '...OSSSSSSO.....',
 '..OSSSTTTSSO....',   # 胸(T泳衣)
 '.OSSTTTTTTSOOOO.',   # 右臂前伸划水(带轮廓)
 '.OSTTTTTTSSSSSO.',
 '..OOTTTTTTOOOO..',   # 腹(水线附近)
 '...OTTTTTTTO....',   # 髋/泳裤
 '...OTTTTTTO.....',
 '...OSSSSSSO.....',   # 并腿(没入水)
 '..OSSSSSSO......',
 '..OSSSSSO.......',
 '..OSSSSO........',   # 小腿斜向后
 '..OSSSO.........',
 '..OSSO..........',
 '..OSO...........',   # 脚
 '..OOO...........')
# SURF1: 划水相2 (ref f16045) 左臂后摆
BODY['SURF1'] = FR(16,16)(
 '....OOOOOO......',
 '...OSSSSSSO.....',
 '..OSSSTTTSSO....',
 '.OSOSSTTTTTTSO..',   # 左臂后摆划水
 'OSSSSTTTTTTTSO..',
 '.OOOTTTTTTOOOO..',
 '...OTTTTTTTO....',
 '...OTTTTTTO.....',
 '...OSSSSSSO.....',
 '..OSSSSSSO......',
 '..OSSSSSO.......',
 '..OSSSSO........',
 '..OSSSO.........',
 '..OSSO..........',
 '..OSO...........',
 '..OOO...........')

# JUMP0(JC): 起跳蹲 (ref jpc_view) 16x18, 腿+2行
BODY['JUMP0'] = FR(16,18)(
 '....OOOOOO......',   # 颈/肩
 '...OSSSSSSO.....',
 '..OOSSSSSSOO....',
 '..OSSTTTTTSO....',
 '.OSSSTTTTTSSO...',   # 臂在体侧
 '.OOTTTTTTTTOO...',
 '...OTTTTTTO.....',
 '...OSSSSSSO.....',   # 腿根
 '..OOSSSSSSOO....',   # 屈膝
 '..OSSSSSSSSO....',
 '..OSSO..OSSO....',   # 小腿分开
 '..OSSO..OSSO....',
 '..OSO....OSO....',
 '..OOO....OOO....',   # 脚
 '................',
 '................',
 '................',
 '................')

# JUMP1(JA): 空中横向飞扑 (ref jpc_view 官方截图 jp-action-c) 18x16
# 组合40x26, side头@(16,0), body@(0,8): 头前伸/躯干水平/臂前伸至头左缘/双腿前后分开
BODY['JUMP1'] = FR(18,16)(
 '...OO.............',   # 上踢脚跟(后上方)
 '..OSSO............',
 '..OSSSO...........',
 '..OSSSSO..........',   # 上腿并到髋
 '.OSSSSTTTTOO......',   # 髋/泳裤
 '.OSSTTTTTTTTO.....',   # 躯干T(水平,+2列)
 '.OSTTTTTTTTTTO....',
 '.OSSSSSSSSSSSSSSO.',   # 臂前伸至col16 接头左缘(canvas x17)
 '.OSSSSSSSSSSSSSO..',   # 臂/腹
 '..OOOOOOOOOOOOOO..',   # 腹下轮廓
 '..OSSSSO..........',   # 下伸腿根(后下方)
 '..OSSSO...........',
 '.OSSO.............',   # 下踢小腿
 '.OOO..............',
 '..................',
 '..................')

# JUMP2(JF): 下落 (ref jpc_view) 16x18: 臂平伸腿半收, 腿+2行
BODY['JUMP2'] = FR(16,18)(
 '....OOOOOO......',
 '...OOSSSSOO.....',
 '.OOOOSSSSOOOO...',   # 臂平伸
 'OSSSSTTTTSSSSSO.',   # 全宽展臂(端部O)
 '.OOOTTTTTTTOOO..',
 '....TTTTTTTT....',
 '....TTTTTTTT....',
 '...OSSSSSSSSO...',   # 腿根
 '...OSSSSSSSO....',   # 腿半收
 '..OSS....SSO....',
 '..OSO....OSO....',
 '..OSO....OSO....',
 '..OSO....OSO....',
 '..OOO....OOO....',
 '................',
 '................',
 '................',
 '................')

# DIVE0: 入水横卧准备 (ref f15615) 18x16: 组合40x26, side头@(16,0), body@(0,6)
# 腿后伸/躯干水平(+2列)/臂前伸至col17接头
BODY['DIVE0'] = FR(18,16)(
 '..................',
 '..................',
 '..................',
 '..................',
 '..................',
 '..................',
 '..OO..............',   # 脚尖(后)
 '.OSSOOOO..........',
 '.OSSSSOOOOO.......',   # 双腿并拢
 '.OSSSSTTTTTTTO....',   # 躯干T(+2列)
 '..OSSTTTTTTTTTO...',
 '..OSSSSSSSSSSSSSSO',   # 臂前伸至col17 接头下缘
 '..OSSSSSSSSSSSSSO.',   # 臂/腹
 '..OOOOOOOOOOOOO...',
 '..................',
 '..................')

# DIVE1: 入水转向弓背 (ref f15616) 18x20: 组合40x34, side头@(16,8), body@(0,6)
# 腿后上翘/躯干斜向右下/臂前伸至头下(col16-17)
BODY['DIVE1'] = FR(18,20)(
 '..O...............',   # 脚尖(后上)
 '.OSSO.............',
 '.OSSO.............',
 '.OSSO.............',   # 小腿
 '.OSSSO............',
 '..OSSSO...........',
 '..OSSSSO..........',   # 双腿并
 '...OSSSSO.........',
 '...OSSSSO.........',   # 大腿
 '....OSSSSO........',
 '....OSSSOO........',   # 髋
 '....OSSTTTTO......',   # 躯干T 斜向右下
 '.....SSTTTTTO.....',
 '......SSTTTTTOO...',
 '.......SSTTTTTTO..',
 '.......SSSTTTTSSO.',   # 肩 → col16 接头(canvas x17 邻)
 '......OSSSSSSSSSSO',   # 臂前伸至头下 col17
 '......OOOOOOOOOO..',   # 臂下轮廓
 '..................',
 '..................')

# DIVE2: 入水垂直下沉 (ref f15618, 原为USA录像帧) 16x18: 组合26x38, down头@(1,14), body@(5,0)
# 腿上举(+2行)/躯干垂直/肩下接头
BODY['DIVE2'] = FR(16,18)(
 '......OOOO......',   # 双脚(并)
 '.....OSSSSO.....',
 '.....OSSSSO.....',   # 小腿
 '.....OSSSSO.....',
 '....OSSSSSSO....',
 '....OSSSSSSO....',   # 大腿
 '....OSSTTSO.....',   # 髋/泳裤
 '....OSTTTSO.....',
 '....OSTTTSO.....',   # 躯干
 '....OSTTTSO.....',
 '...OOSTTTSOO....',
 '...OSTTTTTSO....',
 '...OSTTTTTSO....',
 '...OSSSSSSSO....',   # 肩
 '...OSSSSSSSO....',
 '...OSSSSSSSO....',
 '..OSSSSSSSSSO...',   # 肩底 → canvas y17 与头(content起y17)相交相接
 '..OOOOOOOOOOO...')

# UW0: 水下横游打腿相1 (ref f15625) 18x16: 组合40x26, side头@(16,0), body@(0,7)
BODY['UW0'] = FR(18,16)(
 '..................',
 '..OO..............',   # 脚尖上踢
 '.OSSO.............',
 '.OSSSO............',
 '..OSSSO...........',   # 大腿
 '.....OOOOOOOOOOOO.',   # 躯干上轮廓 cols5..16
 '....OSSSTTTTTTTSO.',   # 躯干 cols4..16 — col16邻头(canvas x17)
 '...OSSTTTTTTTTTSO.',
 '...OSSTTTTTTTTTSO.',
 '..OSSSSSSSSSSSSSO.',   # 腹 cols2..16
 '..OOOOOOOOOOOOOOO.',   # 下轮廓
 '........OOOOO.....',   # 前伸臂(划水)
 '.......OSSSSSO....',
 '..................',
 '..................',
 '..................')
# UW1: 打腿相2 (ref f15633)
BODY['UW1'] = FR(18,16)(
 '..................',
 '..................',
 '..................',
 '..................',
 '.....OOOOOOOOOOOO.',   # 躯干上轮廓
 '....OSSSTTTTTTTSO.',
 '...OSSTTTTTTTTTSO.',
 '...OSSTTTTTTTTTSO.',
 '..OSSSSSSSSSSSSSO.',
 '..OOOOOOOOOOOOOOO.',   # 下轮廓
 '...OOOOO..........',   # 腿根下伸
 '..OSSSSO..........',
 '..OSSSSO..........',   # 腿下踢
 '.OSSSO............',
 '.OSSO.............',
 '.OOO..............')

# BOOST0: 水下加速流线型 (ref f15625; 原版未见独立加速演出, 帧形为设计稿) 18x16
BODY['BOOST0'] = FR(18,16)(
 '..................',
 '..................',
 '..........OOOOOOO.',   # 双臂前伸过肩(头下方) cols10..16
 '.........OSSSSSSO.',
 '....OOOOOSSSSSSSO.',   # 躯干上轮廓+臂 cols4..16
 '....SSTTTTTTTTTSO.',
 '...OSSTTTTTTTTTSO.',
 '...SSTTTTTTTTSO...',
 '..OSSSSSSSSSSO....',   # 腹
 '.OSSSSSSOOOOO.....',   # 腿并拢直伸(与腹相连)
 '.OSSSSSO..........',
 '..OOOOO...........',
 '..................',
 '..................',
 '..................',
 '..................')
# BOOST1: 流线型+剪刀腿
BODY['BOOST1'] = FR(18,16)(
 '..................',
 '..................',
 '..........OOOOOOO.',
 '.........OSSSSSSO.',
 '....OOOOOSSSSSSSO.',
 '....SSTTTTTTTTTSO.',
 '...OSSTTTTTTTTTSO.',
 '...SSTTTTTTTTSO...',
 '..OSSSSSSSSSSO....',
 '..OSSSSOOOOO......',   # 腿剪刀踢(上分)
 '.OSSSO............',
 '.OSSSO............',   # 下分
 '..OOO.............',
 '..................',
 '..................',
 '..................')

# UWUP: 上游头朝上 (ref f15558) 16x18: 组合24x40, front头@(0,0), body@(4,22)
# 臂交替划/腿分踢; 顶部肩线绕下巴(头行22-23与身体行0-1交叠, 身体只补空)
BODY['UWUP'] = FR(16,18)(
 '....OOOOOOOOOO..',   # 肩线(绕下巴)
 '..OOOOOOOOOOOOOO',
 '..OOSSSSSSSSSSOO',   # 颈/胸上
 '.OSSSSTTTTSSSSO.',    # 胸+肩
 'OOSSTTTTTTTTSSO.',    # 左臂弯举(手上至肩上方)
 '.OSSTTTTTTTTSSO.',    # 右臂下摆
 '..OTTTTTTTTTTO..',
 '...TTTTTTTTTT...',    # 泳衣下摆
 '...OSSSSSSSSO...',    # 髋/腿根
 '..OSSSSSSSSO....',
 '..OSSS...SSO....',    # 腿分踢
 '..OSS....OSO....',
 '..OSO....OSO....',
 '..OSO....OSO....',
 '..OSO....OSO....',
 '.OSSO....OSO....',    # 左小腿外摆
 '.OSO.....OOO....',    # 左脚/右脚(右脚下收回)
 '.OOO............')

# UWDN: 下游头朝下蜷身团 (ref f15670; 以 build_sprites.py UWV 身体为底) 16x16
# 组合24x38, down头@(0,14), body@(4,4): 背朝上, 双腿向后上方蜷起
BODY['UWDN'] = FR(16,16)(
 '......OOO.......',   # 脚尖(向后翘起)
 '.....OSSSO......',
 '.....OSSSO......',   # 小腿(向后上方)
 '....OSSSSO......',
 '....OSSSSO......',   # 大腿(蜷收)
 '....OSSTSO......',   # 髋/泳裤
 '...OSSTTSSO.....',   # 躯干(微弓)
 '...OSTTTTSO.....',
 '...OSTTTTSO.....',
 '...OSTTTTSSO....',   # 肩(略宽)
 '...OSSSSSSSO....',
 '...OSSSSSSSO....',   # 肩底
 '....OSSSSSO.....',   # 臂贴体前
 '....OOOOOOO.....',   # 底轮廓 → canvas y17 接头content顶
 '................',
 '................')

# EMERGE: 挺身出水 (ref f15561) 16x18: 臂半张/腿伸直(+2行)
BODY['EMERGE'] = FR(16,18)(
 '....OOOOOO......',
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
 '...OSO..OSO.....',
 '...OSO..OSO.....',
 '...OOO..OOO.....',
 '................',
 '................',
 '................')

# BREATH0: 换气低姿 (ref f16045) 16x18: 臂弯举/胸挺, 腿+2行
BODY['BREATH0'] = FR(16,18)(
 '....OOOOOO......',
 '...OOSSSSOO.....',
 '..OOSSSSSSOO....',
 '.OSSSTTTTSSSO...',   # 臂弯举
 '.OSSTTTTTTSSO...',
 '..OTTTTTTTTO....',
 '...TTTTTTTT.....',
 '...TTTTTTTT.....',
 '...OSSSSSSO.....',
 '...OSSSSSO......',
 '...OSS.SSO......',
 '...OSS.SSO......',
 '...OSO.OSO......',
 '...OOO.OOO......',
 '................',
 '................',
 '................',
 '................')
# BREATH1: 换气顶峰 (ref f16056) 双臂完全水平展开T-pose
BODY['BREATH1'] = FR(16,18)(
 '....OOOOOO......',
 '...OOSSSSOO.....',
 '.OOOOSSSSOOOO...',
 'OSSSSTTTTTSSSSSO',   # 全宽展臂(T-pose)
 '.OOOTTTTTTTOOO..',
 '....TTTTTTTT....',
 '....TTTTTTTT....',
 '...OSSSSSSSSO...',
 '...OSSSSSSO.....',
 '...OSS..SSO.....',
 '...OSS..SSO.....',
 '...OSO..OSO.....',
 '...OSO..OSO.....',
 '...OOO..OOO.....',
 '................',
 '................',
 '................',
 '................')
# BREATH2: 换气回落 (ref f16063) 臂落下/体略收
BODY['BREATH2'] = FR(16,18)(
 '....OOOOOO......',
 '...OOSSSSOO.....',
 '..OOSSSSSSOO....',
 '.OSSSTTTTSSSO...',
 '.OSOTTTTTTOSO...',   # 臂落下
 '..OOTTTTTTOO....',
 '....TTTTTTTT....',
 '...TTTTTTTT.....',
 '...OSSSSSSO.....',
 '...OSSSSO.......',
 '...OSSSSO.......',
 '...OOSSOO.......',
 '...OOSSOO.......',
 '....OOOO........',
 '................',
 '................',
 '................',
 '................')

# ---------------- 精灵规格表 (锚点统一=脚底中心=(w//2,h)) ----------------
# headkind: AV=正脸(socket, yy@(hx,hy)/dd@(hx,hy+2)) SIDE=侧脸 DOWN=垂直头顶
# ref=来源帧  footY=演示脚底世界y  omin=身体轮廓O下限  effmin=身体有效高下限
def SP(w,h,headkind,hx,hy,bx,by,bw,bh,ref,footY,omin,effmin,desc,note=''):
    return dict(w=w,h=h,anchorX=w//2,anchorY=h,headkind=headkind,head=(hx,hy),
                body=(bx,by),bw=bw,bh=bh,ref=ref,footY=footY,omin=omin,effmin=effmin,
                desc=desc,note=note)

BREATH_NOTE = '姿态参考；该段时序参数仍待标定'
BOOST_NOTE = '原版未见独立加速演出，以划水节奏区分，帧形为设计稿'
SPEC = {
 'SURF0':  SP(24,36,'AV', 0,0, 4,20,16,16,'f16063',108,20,16,'水面俯泳·划水相1',BREATH_NOTE),
 'SURF1':  SP(24,36,'AV', 0,0, 4,20,16,16,'f16045',108,20,16,'水面俯泳·划水相2',BREATH_NOTE),
 'JUMP0':  SP(24,42,'AV', 0,0, 4,24,16,18,'jpc_view',108,30,14,'起跳蹲(JC)'),
 'JUMP1':  SP(40,26,'SIDE',16,0, 0,8, 18,16,'jpc_view', 90,30,14,'空中横向飞扑(JA)'),
 'JUMP2':  SP(24,42,'AV', 0,0, 4,24,16,18,'jpc_view', 96,28,14,'下落(JF)：臂平伸腿半收'),
 'DIVE0':  SP(40,26,'SIDE',16,0, 0,6, 18,16,'f15615',108,25, 8,'入水·横卧俯姿准备'),
 'DIVE1':  SP(40,34,'SIDE',16,8, 0,6, 18,20,'f15616',114,30,18,'入水·转向弓背'),
 'DIVE2':  SP(26,38,'DOWN',1,14, 5,0, 16,18,'f15618',120,35,18,'入水·垂直下沉','f15618 原为 USA 录像帧'),
 'UW0':    SP(40,26,'SIDE',16,0, 0,7, 18,16,'f15625',130,35,12,'水下横游·打腿相1'),
 'UW1':    SP(40,26,'SIDE',16,0, 0,7, 18,16,'f15633',130,35,12,'水下横游·打腿相2'),
 'BOOST0': SP(40,26,'SIDE',16,0, 0,7, 18,16,'f15625',130,25,10,'水下加速·流线型',BOOST_NOTE),
 'BOOST1': SP(40,26,'SIDE',16,0, 0,7, 18,16,'f15625',130,25,11,'水下加速·剪刀腿',BOOST_NOTE),
 'UWUP':   SP(24,40,'AV', 0,0, 4,22,16,18,'f15558',110,28,18,'上游(头朝上竖直,臂交替划,腿分踢)'),
 'UWDN':   SP(24,38,'DOWN',0,14, 4,4, 16,16,'f15670',130,25,14,'下游(头朝下蜷身团)'),
 'EMERGE': SP(24,42,'AV', 0,0, 4,24,16,18,'f15561',112,30,15,'挺身出水：臂半张腿伸直'),
 'BREATH0':SP(24,42,'AV', 0,0, 4,24,16,18,'f16045',108,25,14,'换气·低姿(臂弯举胸挺)',BREATH_NOTE),
 'BREATH1':SP(24,42,'AV', 0,0, 4,24,16,18,'f16056', 96,30,14,'换气·顶峰(双臂水平展开T-pose)',BREATH_NOTE),
 'BREATH2':SP(24,42,'AV', 0,0, 4,24,16,18,'f16063',102,25,14,'换气·回落水面',BREATH_NOTE),
}
ORDER = ['SURF0','SURF1','JUMP0','JUMP1','JUMP2','DIVE0','DIVE1','DIVE2',
         'UW0','UW1','BOOST0','BOOST1','UWUP','UWDN','EMERGE','BREATH0','BREATH1','BREATH2']
UPRIGHT = {'SURF0','SURF1','JUMP0','JUMP2','DIVE2','UWUP','UWDN','EMERGE','BREATH0','BREATH1','BREATH2'}

# ---------------- 中性木偶头 (去脸轮廓版用): 椭圆O轮廓+S肤填充, 无身份特征 ----------------
# 轮廓包围盒对齐真头(front下巴到row23 / side左缘col1 / down顶row3底row21), 保证连接关系一致
R24 = bs.R24
PUPPET = {}
PUPPET['AV'] = [
 R24(), R24(), R24(),
 R24((8,'O'*8)),
 R24((6,'OO'),(8,'S'*8),(16,'OO')),
 R24((4,'OO'),(6,'S'*12),(18,'OO')),
 R24((3,'O'),(4,'S'*16),(20,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((2,'O'),(3,'S'*18),(21,'O')),
 R24((3,'O'),(4,'S'*16),(20,'O')),
 R24((4,'O'),(5,'s'),(6,'S'*12),(18,'s'),(19,'O')),
 R24((4,'O'),(5,'s'),(6,'S'*10),(16,'s'),(17,'O')),
 R24((5,'O'),(6,'s'*2),(8,'S'*6),(14,'s'*2),(15,'O')),
 R24((6,'O'),(7,'s'*2),(9,'S'*4),(13,'s'*2),(14,'O')),
 R24((8,'O'),(9,'s'*4),(12,'O'))]
PUPPET['SIDE'] = [   # 侧脸轮廓(脸朝右), 中性无特征
 R24(), R24(),
 R24((5,'O'*9)),
 R24((3,'OO'),(5,'S'*9),(14,'OOO')),
 R24((2,'O'),(3,'S'*14),(17,'O')),
 R24((2,'O'),(3,'S'*15),(18,'O')),
 R24((1,'O'),(2,'S'*16),(18,'O')),
 R24((1,'O'),(2,'S'*16),(18,'O')),
 R24((1,'O'),(2,'S'*16),(18,'O')),
 R24((1,'O'),(2,'S'*16),(18,'O')),
 R24((1,'O'),(2,'S'*16),(18,'O')),
 R24((1,'O'),(2,'S'*16),(18,'O')),
 R24((1,'O'),(2,'S'*16),(18,'O')),
 R24((1,'O'),(2,'S'*15),(17,'O')),
 R24((1,'O'),(2,'S'*15),(17,'O')),
 R24((1,'O'),(2,'S'*14),(16,'O')),
 R24((1,'O'),(2,'S'*13),(15,'O')),
 R24((2,'O'),(3,'S'*11),(14,'O')),
 R24((2,'O'),(3,'s'),(4,'S'*9),(13,'O')),
 R24((3,'O'),(4,'s'),(5,'S'*7),(12,'O')),
 R24((4,'O'),(5,'s'),(6,'S'*5),(11,'O')),
 R24((5,'O'),(6,'s'*4),(10,'O')),
 R24(), R24()]
PUPPET['DOWN'] = [   # 垂直头顶轮廓(脸朝下), 中性无特征
 R24(), R24(), R24(),
 R24((6,'O'*7)),
 R24((4,'OO'),(6,'S'*7),(13,'OO')),
 R24((3,'O'),(4,'S'*11),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*12),(15,'O')),
 R24((2,'O'),(3,'S'*11),(14,'O')),
 R24((3,'O'),(4,'S'*9),(13,'O')),
 R24((5,'O'),(6,'s'*6),(12,'O')),
 R24((6,'O'),(7,'s'*4),(11,'O')),
 R24((7,'O'),(8,'s'*2),(10,'O')),
 R24((8,'O'),(9,'sO')),
 R24(), R24()]
for k, m in PUPPET.items():
    assert len(m) == 24, f'PUPPET {k}: {len(m)} rows'
    for i, r in enumerate(m): assert len(r) == 24, f'PUPPET {k} row{i} len={len(r)}'

# ---------------- 左向身体 = 翻转 + 人工修正明暗 (确定性, 非精确镜像) ----------------
def body_left(rows):
    m = mirror(rows)
    g = [list(r) for r in m]
    S_pos = [(r, c) for r in range(len(g)) for c in range(len(g[r])) if g[r][c] == 'S']
    s_pos = [(r, c) for r in range(len(g)) for c in range(len(g[r])) if g[r][c] == 's']
    for r, c in (S_pos[len(S_pos)//5], S_pos[len(S_pos)//2], S_pos[4*len(S_pos)//5]):
        g[r][c] = 's'   # 受光面转暗(固定左上来光)
    if s_pos:
        r, c = s_pos[len(s_pos)//2]; g[r][c] = 'S'
    out = [''.join(r) for r in g]
    assert out != m, 'left 不得等于精确镜像'
    return out

BODY_L = {k: body_left(v) for k, v in BODY.items()}

# ---------------- 组合: 先画头, 身体只填空(沿用 bs.composite_lay 规则) ----------------
def get_head(kind, who, d):
    if kind == 'SIDE': return HEAD_SIDE[who][d]
    if kind == 'DOWN': return HEAD_DOWN[who][d]
    return AVATAR[who][d]

def composite(name, who, d, puppet=False):
    sp = SPEC[name]
    w, h = sp['w'], sp['h']
    grid = [[None]*w for _ in range(h)]
    hx, hy = sp['head']; bx, by = sp['body']
    kind = sp['headkind']
    headm = PUPPET[kind] if puppet else get_head(kind, who, d)
    bodym = BODY[name] if d == 'right' else BODY_L[name]
    if d == 'left':
        hx = w - hx - 24
        bx = w - bx - sp['bw']
    if kind == 'AV' and not puppet:
        hy += HEAD_DY[who]
    hc, bc = set(), set()
    for r in range(24):
        for q in range(24):
            k = headm[r][q]
            if k != '.':
                x, y = hx+q, hy+r
                assert 0 <= x < w and 0 <= y < h, f'{name}/{who}/{d}: head px out {x},{y}'
                grid[y][x] = k; hc.add((x, y))
    for r in range(sp['bh']):
        for q in range(sp['bw']):
            k = bodym[r][q]
            if k != '.':
                x, y = bx+q, by+r
                assert 0 <= x < w and 0 <= y < h, f'{name}/{who}/{d}: body px out {x},{y}'
                if grid[y][x] is None: grid[y][x] = k
                bc.add((x, y))
    fr = (hx, hy, 24, 24)
    return grid, hc, bc, fr

def eff_bbox_cells(cells):
    xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
    return (min(xs), min(ys), max(xs), max(ys))

def connected(cells):
    cells = set(cells); n = 0
    while cells:
        n += 1; stack = [cells.pop()]
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    p = (x+dx, y+dy)
                    if p in cells: cells.discard(p); stack.append(p)
    return n

# ---------------- 自检 (每张精灵 × yy/dd × right/left, 任一失败即非零退出) ----------------
errs = []
print('== 3A 身体帧有效包围盒/轮廓 ==')
for name in ORDER:
    sp = SPEC[name]
    m = BODY[name]
    assert len(m) == sp['bh'], f'{name}: 行数{len(m)}!={sp["bh"]}'
    for i, r in enumerate(m):
        assert len(r) == sp['bw'], f'{name} row{i} 行宽{len(r)}!={sp["bw"]}'
    bb = bs.eff_bbox(m)
    eh = bb[3]-bb[1]+1; ew = bb[2]-bb[0]+1
    oc = sum(r.count('O') for r in m)
    tot = sum(1 for r in m for ch in r if ch != '.')
    print(f'{name}: 身体{sp["bw"]}x{sp["bh"]} bbox x{bb[0]}..{bb[2]} y{bb[1]}..{bb[3]} w{ew} h{eh} O={oc} 有效={tot}')
    if oc < sp['omin']: errs.append(f'{name} 轮廓O={oc}<{sp["omin"]}')
    if eh < sp['effmin']: errs.append(f'{name} 身体有效高{eh}<{sp["effmin"]}')
    if name in UPRIGHT and eh < 12: errs.append(f'{name} 直立帧有效高{eh}<12')
    if bs.connected({(q, r) for r in range(len(m)) for q in range(len(m[r])) if m[r][q] != '.'}) != 1:
        errs.append(f'{name} 身体非单连通域')

print('== 3A 组合校验 (精灵×双人×左右) ==')
for name in ORDER:
    sp = SPEC[name]
    gridR = {}
    for who in ('yy', 'dd'):
        for d in ('right', 'left'):
            grid, hc, bc, fr = composite(name, who, d)
            tag = f'{name}/{who}/{d}'
            # 1) 行数/行宽 = 规格 w×h
            if len(grid) != sp['h'] or any(len(r) != sp['w'] for r in grid):
                errs.append(f'{tag}: 画布尺寸不符')
            # 2) 有效像素 8 连通单连通域
            nc = connected(hc | bc)
            if nc != 1: errs.append(f'{tag}: 连通域={nc}')
            # 3) 轮廓 O 阈值 (身体, 上面已查; 组合层面再查含头的总量级)
            oc = sum(1 for r in grid for ch in r if ch == 'O')
            if oc < sp['omin']: errs.append(f'{tag}: 组合轮廓O={oc}<{sp["omin"]}')
            # 4) face_rect 完全在画布内
            fx, fy, fw, fh = fr
            if not (0 <= fx and fx+fw <= sp['w'] and 0 <= fy and fy+fh <= sp['h']):
                errs.append(f'{tag}: face_rect{fr} 越出画布')
            # 5) 头与身体有效像素实际 8 连通相邻
            touch = any((x+dx, y+dy) in bc for (x, y) in hc for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            if not touch: errs.append(f'{tag}: 头身不相邻')
            # 8) 直立帧组合有效高度≥12
            bb = eff_bbox_cells(hc | bc)
            if name in UPRIGHT and bb[3]-bb[1]+1 < 12: errs.append(f'{tag}: 直立帧组合有效高<12')
            gridR[(who, d)] = grid
    # 7) 左右两版差异>0 (非精确镜像)
    for who in ('yy', 'dd'):
        mr = mirror([''.join('.' if c is None else c for c in r) for r in gridR[(who, 'right')]])
        ml = [''.join('.' if c is None else c for c in r) for r in gridR[(who, 'left')]]
        ndiff = sum(1 for r in range(sp['h']) for q in range(sp['w']) if mr[r][q] != ml[r][q])
        if ndiff == 0: errs.append(f'{name}/{who}: 左右互为精确镜像')
    print(f'{name}: 组合连通/头身相邻/face_rect/左右差异 OK ({sp["w"]}x{sp["h"]} 锚点({sp["anchorX"]},{sp["anchorY"]}))')

print('== 3A 脚底锚点边界 (ax∈[20,236] × 演示footY → [0,256]×[0,168]) ==')
for name in ORDER:
    sp = SPEC[name]
    ox0 = 20 - sp['anchorX']; ox1 = 236 - sp['anchorX']
    oy = sp['footY'] - sp['anchorY']
    ok = (0 <= ox0 and ox1 + sp['w'] <= 256 and 0 <= oy and oy + sp['h'] <= 168)
    print(f'{name}: origin x {ox0}..{ox1} y {oy} +{sp["w"]}x{sp["h"]} -> {"OK" if ok else "CLIP!"}')
    if not ok: errs.append(f'{name} 越界')

# 木偶头连接 sanity (去脸轮廓版头身相邻)
for name in ORDER:
    grid, hc, bc, fr = composite(name, 'yy', 'right', puppet=True)
    if connected(hc | bc) != 1: errs.append(f'{name}: 木偶版非单连通域')
    if not any((x+dx, y+dy) in bc for (x, y) in hc for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
        errs.append(f'{name}: 木偶版头身不相邻')
print('木偶头(去脸轮廓版)连接 OK')

if errs:
    print('\nERRORS:'); [print(' -', e) for e in errs]; sys.exit(1)

# ---------------- 调色: 正常色 / 水下逐像素映射 (水线 y=96) ----------------
def hex2rgb(s): return tuple(int(s[i:i+2], 16) for i in (1, 3, 5))
PAL = {who: {k: hex2rgb(v) for k, v in bs.PALV.items()} for who in ('yy', 'dd')}
PAL['yy']['T'] = hex2rgb('#3C9CF0')   # 阳阳队色
PAL['dd']['T'] = hex2rgb('#F83800')   # 爸爸队色
PAL['np'] = {k: hex2rgb(v) for k, v in bs.PALV.items()}; PAL['np']['T'] = (168, 168, 168)  # 去脸轮廓版中性色
UW_MAP = {'O':'#004058','W':'#FCFCFC','S':'#A4E4FC','s':'#3CBCFC','d':'#004058',
          'C':'#3CBCFC','c':'#004058','H':'#004058','h':'#3CBCFC','T':'#3CBCFC','L':'#A4E4FC'}
UW_RGB = {k: hex2rgb(v) for k, v in UW_MAP.items()}
WATER_Y = 96

CJK = False
for _fp in ('/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/Supplemental/Songti.ttc',
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'):
    try:
        FONT   = ImageFont.truetype(_fp, 14)
        FONT_S = ImageFont.truetype(_fp, 12)
        FONT_B = ImageFont.truetype(_fp, 16)
        CJK = True; _FONT_USED = _fp
        break
    except Exception:
        continue
if not CJK:
    FONT = FONT_S = FONT_B = ImageFont.load_default()
print('CJK font:', _FONT_USED if CJK else 'FALLBACK(default, 英文标签)')

def T(zh, en):
    """CJK 字体可用用中文标签, 否则退化英文标签 (禁止默认字体出方框)"""
    return zh if CJK else en

REF_DIR = HERE/'st3_shots'/'ref3a'
CROPS = {   # 推荐裁剪框(已验证); f16056 人物在画面顶缘, 向上扩展以纳入人物
 'f15615': (45,52,110,110), 'f15616': (45,52,110,110), 'f15618': (50,45,115,115),
 'f15625': (75,92,150,140), 'f15633': (75,92,150,140), 'f15670': (50,95,130,145),
 'f15558': (40,85,110,140), 'f15561': (40,85,110,140),
 'f16045': (140,80,200,125), 'f16056': (90,15,165,80), 'f16063': (55,80,115,125),
 'jpc_view': (135,25,260,170),   # 官方截图 jp-action-c 人物区
}

def ref_image(name):
    ref = SPEC[name]['ref']
    im = Image.open(REF_DIR/f'{ref}.png').convert('RGB').crop(CROPS[ref])
    return im.resize((im.width*3, im.height*3), Image.NEAREST)

def draw_grid(dr, grid, ox, oy, s, pal):
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch:
                dr.rectangle([ox+x*s, oy+y*s, ox+x*s+s-1, oy+y*s+s-1], fill=pal[ch])

def panel_sprite(name, who, s, puppet=False):
    grid, _, _, _ = composite(name, who, 'right', puppet=puppet)
    sp = SPEC[name]
    im = Image.new('RGB', (sp['w']*s+8, sp['h']*s+8), (24, 24, 32))
    dr = ImageDraw.Draw(im)
    draw_grid(dr, grid, 4, 4, s, PAL['np'] if puppet else PAL[who])
    dr.rectangle([3, 3, 4+sp['w']*s, 4+sp['h']*s], outline=(70, 70, 90))
    return im

def panel_demo(name):
    """8倍演示: yy|dd 并排, 按演示footY摆放, 世界y>96 逐像素 UW_MAP, 画水线/锚点/脸区"""
    sp = SPEC[name]; S = 8
    w, h = sp['w'], sp['h']
    ax_yy = 128 - sp['anchorX'] - 8; ax_dd = 128 + (w - sp['anchorX']) + 8
    oy = sp['footY'] - sp['anchorY']
    x0 = ax_yy - sp['anchorX'] - 8; x1 = ax_dd + (w - sp['anchorX']) + 8
    y0 = min(oy, WATER_Y) - 8;      y1 = max(oy + h, WATER_Y + 1) + 6
    Wp, Hp = (x1-x0)*S, (y1-y0)*S + 16
    im = Image.new('RGB', (Wp, Hp), (24, 24, 32))
    dr = ImageDraw.Draw(im)
    for wy in range(y0, y1):   # 背景: 水上深灰 / 水下深蓝
        c = (30, 34, 46) if wy <= WATER_Y else (0, 56, 92)
        dr.rectangle([0, 16+(wy-y0)*S, Wp-1, 16+(wy-y0)*S+S-1], fill=c)
    for who, ax in (('yy', ax_yy), ('dd', ax_dd)):
        grid, _, _, fr = composite(name, who, 'right')
        ox = ax - sp['anchorX']
        for cy in range(h):
            wy = oy + cy
            for cx in range(w):
                ch = grid[cy][cx]
                if ch:
                    col = UW_RGB[ch] if wy > WATER_Y else PAL[who][ch]   # 逐像素水线调色
                    dr.rectangle([(ox+cx-x0)*S, 16+(wy-y0)*S, (ox+cx-x0)*S+S-1, 16+(wy-y0)*S+S-1], fill=col)
        fx, fy = fr[0]+ox, fr[1]+oy   # 脸部替换区域(黄框)
        for i in range(0, 24*S, 4):
            dr.point([(fx-x0)*S+i, 16+(fy-y0)*S], fill=(252, 220, 60)); dr.point([(fx-x0)*S+i, 16+(fy+24-y0)*S-1], fill=(252, 220, 60))
            dr.point([(fx-x0)*S, 16+(fy-y0)*S+i], fill=(252, 220, 60)); dr.point([(fx+24-x0)*S-1, 16+(fy-y0)*S+i], fill=(252, 220, 60))
        axs, ays = (ax-x0)*S, 16+(sp['footY']-y0)*S   # 脚底锚点(红十字)
        dr.line([axs-10, ays-1, axs+10, ays-1], fill=(240, 40, 40), width=2)
        dr.line([axs, ays-12, axs, ays+2], fill=(240, 40, 40), width=2)
        dr.text(((ox-x0)*S, 2), T('阳阳','YY') if who == 'yy' else T('爸爸','DD'), font=FONT_S, fill=(255, 255, 120))
    wl = 16 + (WATER_Y-y0)*S   # 水线标记(青白虚线)
    for x in range(0, Wp, 8):
        dr.rectangle([x, wl, x+4, wl+1], fill=(160, 240, 255))
    dr.text((Wp//2-45, wl-13), T('水线 y=96','waterline y=96'), font=FONT_S, fill=(160, 240, 255))
    return im

DESC_EN = {
 'SURF0':'surface prone stroke ph.1','SURF1':'surface prone stroke ph.2',
 'JUMP0':'takeoff crouch (JC)','JUMP1':'mid-air horizontal leap (JA)','JUMP2':'falling (JF): arms out, legs half-tucked',
 'DIVE0':'dive: prone prep','DIVE1':'dive: arched turn','DIVE2':'dive: vertical sinking',
 'UW0':'underwater swim kick ph.1','UW1':'underwater swim kick ph.2',
 'BOOST0':'boost: streamline','BOOST1':'boost: streamline+scissor kick',
 'UWUP':'swim up (head-up vertical)','UWDN':'swim down (head-down tuck)','EMERGE':'emerge: arms half-spread, legs straight',
 'BREATH0':'breath: low prep','BREATH1':'breath: peak T-pose','BREATH2':'breath: falling back',
}
NOTE_EN = {
 'SURF0':'pose ref only; timing TBD','SURF1':'pose ref only; timing TBD',
 'DIVE2':'f15618 from USA footage',
 'BOOST0':'no boost anim in original; design draft','BOOST1':'no boost anim in original; design draft',
 'BREATH0':'pose ref only; timing TBD','BREATH1':'pose ref only; timing TBD','BREATH2':'pose ref only; timing TBD',
}

def text_panel(names, W, H):
    im = Image.new('RGB', (W, H), (18, 18, 26))
    dr = ImageDraw.Draw(im)
    maxw = W - 10
    def wrap(t, font):
        out, cur = [], ''
        for ch in t:
            if dr.textlength(cur + ch, font=font) <= maxw: cur += ch
            else: out.append(cur); cur = ch
        out.append(cur)
        return out
    y = 6
    for name in names:
        sp = SPEC[name]
        hx, hy = sp['head']
        dy = HEAD_DY['dd'] if sp['headkind'] == 'AV' else 0
        lines = []
        for i, t in enumerate(wrap(f"{name} {T(sp['desc'], DESC_EN[name])}", FONT_B)):
            lines.append((t, FONT_B, (255, 230, 120)))
        lines += [
            (T(f"源: {sp['ref']}", f"src: {sp['ref']}"), FONT_S, (220, 220, 220)),
            (T(f"画布 {sp['w']}×{sp['h']} 锚点({sp['anchorX']},{sp['anchorY']})",
               f"canvas {sp['w']}x{sp['h']} anchor({sp['anchorX']},{sp['anchorY']})"), FONT_S, (180, 220, 255)),
            (T(f"脸区 yy({hx},{hy},24,24)", f"face yy({hx},{hy},24,24)"), FONT_S, (180, 220, 255)),
            (f"     dd({hx},{hy+dy},24,24)", FONT_S, (180, 220, 255)),
            (T(f"演示 footY={sp['footY']}", f"demo footY={sp['footY']}"), FONT_S, (180, 255, 180)),
        ]
        note = T(sp['note'], NOTE_EN.get(name, ''))
        if note:
            for t in wrap(note, FONT_S): lines.append((t, FONT_S, (255, 160, 120)))
        for t, f, c in lines:
            dr.text((6, y), t, font=f, fill=c); y += 19 if f is not FONT_B else 23
        y += 6
    return im

def make_row(names):
    """一行 = [文字栏][原版参考帧3x][去脸轮廓3x][阳阳1x][爸爸1x][8x演示]; names 1或3帧"""
    demos = [panel_demo(n) for n in names]
    refs  = [ref_image(n) for n in names]
    pups  = [panel_sprite(n, 'yy', 3, puppet=True) for n in names]
    yys   = [panel_sprite(n, 'yy', 1) for n in names]
    dds   = [panel_sprite(n, 'dd', 1) for n in names]
    rowH = max(p.height for p in demos+refs+pups) + 26
    cols = []
    for i in range(len(names)):
        cols += [refs[i], pups[i], yys[i], dds[i], demos[i]]
    rowW = 214 + sum(p.width for p in cols) + 10*len(cols) + 8
    im = Image.new('RGB', (rowW, rowH), (14, 14, 20))
    im.paste(text_panel(names, 210, rowH-4), (2, 2))
    x = 214
    for p in cols:
        im.paste(p, (x, 22)); x += p.width + 10
    return im

def make_sheet(row_names, path, title):
    rows = [make_row(ns) for ns in row_names]
    W = max(r.width for r in rows); H = sum(r.height for r in rows) + 46 + 8*len(rows)
    out = Image.new('RGB', (W, H), (10, 10, 14))
    dr = ImageDraw.Draw(out)
    dr.text((10, 8), title, font=FONT_B, fill=(255, 255, 160))
    dr.text((10, 28), T('栏: 动作/参数 | 原版参考帧3× | 去脸人体轮廓3× | 阳阳1× | 爸爸1× | 8×演示(水线y=96逐像素UW_MAP调色; 黄框=脸部替换区域 红十字=脚底锚点)',
                        'cols: action/spec | original ref 3x | faceless outline 3x | YY 1x | DD 1x | 8x demo (per-pixel UW_MAP below waterline y=96; yellow=face_rect red=foot anchor)'),
            font=FONT_S, fill=(180, 180, 200))
    y = 46
    for r in rows:
        out.paste(r, (0, y)); y += r.height + 8
    out.save(path)
    print('wrote', path.name, out.size)

make_sheet([['SURF0'],['SURF1'],['JUMP0'],['JUMP1'],['JUMP2'],['DIVE0'],['DIVE1'],['DIVE2']],
           HERE/'阶段3A精灵审核表-1.png',
           T('阶段3A精灵审核表(1/2): SURF×2 / JUMP×3 / DIVE×3', 'Stage3A sprite review (1/2): SURF x2 / JUMP x3 / DIVE x3'))
make_sheet([['UW0'],['UW1'],['BOOST0'],['BOOST1'],['UWUP'],['UWDN'],['EMERGE'],['BREATH0','BREATH1','BREATH2']],
           HERE/'阶段3A精灵审核表-2.png',
           T('阶段3A精灵审核表(2/2): UW×2 / BOOST×2 / UWUP / UWDN / EMERGE / BREATH×3', 'Stage3A sprite review (2/2): UW x2 / BOOST x2 / UWUP / UWDN / EMERGE / BREATH x3'))

# ---------------- 输出 sprites_3a_baked.js (本轮不接主程序) ----------------
def bake_js():
    head = ('// 阶段3A 可变尺寸身体精灵数据 (生成: build_sprites_3a.py) — 本轮不接主程序\n'
            '// 锚点=脚底中心=(w//2,h); 头socket 24x24: headKind AV=正脸(AVATAR, dd下巴短2px→faceRect.dd y+2) '
            'SIDE=HEAD_SIDE DOWN=HEAD_DOWN\n'
            '// body=[x,y,w,h] 身体在画布的摆放与尺寸; bodyRows=右向基准, bodyRowsLeft=水平翻转+明暗人工修正(非精确镜像)\n'
            '// faceRect=[x,y,24,24] 右向画布坐标的脸部可替换区域(left=整体镜像); footY=审核表演示脚底世界y(水线y=96)\n'
            '// 合成规则: 先画头, 身体只填透明区; 水下逐像素调色: 世界y>96 → UW_MAP\n')
    data = {}
    for name in ORDER:
        sp = SPEC[name]
        hx, hy = sp['head']
        frd = {}
        for who in ('yy', 'dd'):
            fy = hy + (HEAD_DY[who] if sp['headkind'] == 'AV' else 0)
            frd[who] = [hx, fy, 24, 24]
        data[name] = dict(w=sp['w'], h=sp['h'], anchorX=sp['anchorX'], anchorY=sp['anchorY'],
                          headKind=sp['headkind'], head=[hx, hy], body=[sp['body'][0], sp['body'][1], sp['bw'], sp['bh']],
                          faceRect=frd, footY=sp['footY'], ref=sp['ref'], desc=sp['desc'], note=sp['note'],
                          bodyRows=BODY[name], bodyRowsLeft=BODY_L[name])
    js = head + 'const SPRITES_3A = ' + json.dumps(data, ensure_ascii=False, indent=1) + ';\n'
    js += 'const UW_MAP_3A = ' + json.dumps(UW_MAP) + ';\n'
    (HERE/'sprites_3a_baked.js').write_text(js, encoding='utf-8')
    print('wrote sprites_3a_baked.js')

bake_js()

# ---------------- 输出 阶段3A精灵清单.md ----------------
def bake_md():
    L = ['# 阶段3A精灵清单（身体精灵重建，16张动作精灵）', '',
         '锚点统一 = 脚底中心 = (w//2, h)（画布底缘中心）。脸部替换区域 face_rect = 24×24 socket，',
         '坐标为右向画布坐标；left = 整体水平翻转 + 明暗人工修正（非逐像素精确镜像）。',
         '正脸头（AV）：yy 放在 (hx,hy)，dd 放在 (hx,hy+2)（HEAD_DY=2，dd 下巴短 2px）；side/down 头不偏移。',
         '入水/出水调色：逐像素判断 世界y>96 → UW_MAP（非整状态一次性变蓝），演示见审核表 8× 栏。',
         '本轮未接主程序，数据已导出 sprites_3a_baked.js 供未来接入。', '',
         '| 精灵 | 来源帧 | 画布尺寸 | 脚底锚点 | 脸部替换区域 face_rect | 演示footY | 备注 |',
         '|---|---|---|---|---|---|---|']
    for name in ORDER:
        sp = SPEC[name]
        hx, hy = sp['head']
        dy = HEAD_DY['dd'] if sp['headkind'] == 'AV' else 0
        fr = f"yy({hx},{hy},24,24) dd({hx},{hy+dy},24,24)"
        L.append(f"| {name} {sp['desc']} | {sp['ref']} | {sp['w']}×{sp['h']} | ({sp['anchorX']},{sp['anchorY']}) | {fr} | {sp['footY']} | {sp['note'] or '—'} |")
    L += ['',
          '标注说明：',
          '- f16045 / f16056 / f16063 源自一段不完整的换气录像（f16066 后发生人物接触）：姿态参考；该段时序参数仍待标定。',
          '- BOOST0 / BOOST1：原版未见独立加速演出，以划水节奏区分，帧形为设计稿。',
          '- f15618 原为 USA 录像帧。',
          '- f16056 审核表参考栏裁剪向上扩展为 (90,15,165,80)（人物位于画面顶缘，推荐框只含其下缘）。',
          '- 审核表只含游戏截图与像素画，不含真人照片。']
    (HERE/'阶段3A精灵清单.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('wrote 阶段3A精灵清单.md')

bake_md()

if errs:
    print('\nERRORS:'); [print(' -', e) for e in errs]; sys.exit(1)
print('\nALL 3A CHECKS PASS')
