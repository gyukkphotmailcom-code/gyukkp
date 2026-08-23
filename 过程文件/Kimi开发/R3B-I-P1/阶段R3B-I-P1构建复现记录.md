# 阶段 R3B-I-P1 构建复现记录

## 环境

- macOS，bash
- Python：`过程文件/Kimi开发/.venv/bin/python3`（Pillow 11.3.0）
- 基线：HEAD = 679cb36 `stage3b-m-identity-mask-approved`

## 构建命令

```
过程文件/Kimi开发/.venv/bin/python3 过程文件/Kimi开发/R3B-I-P1/build_likeness_sprites_r3bip1.py
```

预期输出：

```
OK R3B-I-P1 构建完成
  SURF0_yy_L: changed=129 insideRGB=99 insideAlpha=30 outside=0/0 belowNeck=0 comp=1
  SURF0_dd_L: changed=116 insideRGB=81 insideAlpha=35 outside=0/0 belowNeck=0 comp=1
  JUMP_AIR_yy_L: changed=156 insideRGB=138 insideAlpha=18 outside=0/0 belowNeck=0 comp=1
  JUMP_AIR_dd_L: changed=119 insideRGB=103 insideAlpha=16 outside=0/0 belowNeck=0 comp=1
```

## 最小复现环境

干净环境下需要：

1. `git archive HEAD | tar -x -C <干净目录>`（提供 R3A 全部批准输入，
   SHA 钉值见清单第 2 节）；
2. 复制生成器 `过程文件/Kimi开发/R3B-I-P1/build_likeness_sprites_r3bip1.py`；
3. 复制参考展示输入（untracked，非批准输入）：
   `R3B-I/identity_sprites_r3bi.json` 与
   `R3B-I/sprites/{SURF0_yy_L,SURF0_dd_L,JUMP_AIR_yy_L,JUMP_AIR_dd_L}.png`；
4. 任一安装了 Pillow 的 python3（构建机用项目 venv 验证）。

生成器不读取主 HTML、不读取家庭照片/概念图、不使用网络、不使用随机数；
全部产物先完成内存验证，再经临时文件原子替换落盘；任一失败非零退出且
旧产物不被覆盖。

## 测试结果（全部实际执行）

| # | 测试 | 命令摘要 | 结果 |
|---|---|---|---|
| 1 | 双跑确定性 | 工作区连续构建两次，比较全部产物 SHA-256 | PASS，两次完全一致 |
| 2 | 干净基线提取 | `git archive HEAD` → /tmp/r3bip1_clean + 生成器 + 参考输入 | PASS |
| 3 | 干净环境重建 | 在 /tmp/r3bip1_clean 重建，与工作区逐字节比较 | PASS，全部产物 SHA 一致 |
| 4 | 篡改 R3A 输入 | sprites_r3a_human_baked.js 追加 1 字节后运行 | PASS，exit=1（FATAL SHA 不匹配），产物未变 |
| 5 | 篡改 Stage2 输入 | avatar_paint.py 追加 1 字节后运行 | PASS，exit=1，产物未变 |
| 6 | 语法编译 | `python3 -m py_compile build_likeness_sprites_r3bip1.py` | PASS |
| 7 | JSON 重解析 | 重新 `json.loads` likeness_sprites_r3bip1.json / blind_map.json | PASS |
| 8 | PNG 逐像素重读 | 重读 4 张 PNG，逐像素映射回调色板字符并与 JSON rows/contentSha256 比对 | PASS，4/4 一致，无调色板外像素 |
| 9 | 空白冲突检查 | `git diff --check` | PASS |

双跑产物 SHA-256 全表见《阶段R3B-I-P1身份稿清单》第 6 节。

## 备注

- 本轮无 baked.js 产物（指令未要求接入运行时），故无 node --check 项。
- 篡改测试在 /tmp 的副本中执行，工作区批准输入未被触碰。
