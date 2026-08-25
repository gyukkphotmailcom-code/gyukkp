#!/bin/bash
# 双击这个文件就能玩最新版本（带真实美术）。
#
# 它做两件事：把当前代码和美术合成一份本地游戏文件，然后用浏览器打开。
# 这份本地文件含家人外貌，只留在你电脑上，不会被提交。
#
# 操作方式：
#   ← →   移动 / 选跳跃方向
#   ↑ ↓   上浮 / 下潜
#   Z 空格 水面跳跃 / 水下加速
#   X     水面换气 / 水下踢击 / 肩组出拳（被抓住时连打挣脱）
#   回车   重新开始

cd "$(dirname "$0")" || exit 1

echo ""
echo "正在生成最新的游戏文件……"

if ! command -v python3 >/dev/null 2>&1; then
  echo "  没找到 python3。把这句话告诉 AI 就行。"
  echo ""
  echo "按回车键关闭。"; read -r _; exit 1
fi

if ! python3 过程文件/Claude重启规划/bake.py --out; then
  echo ""
  echo "  生成失败。把上面的报错整段复制给 AI。"
  echo ""
  echo "按回车键关闭。"; read -r _; exit 1
fi

GAME="阳阳水泳大乱斗-本地美术勿提交.html"
if [ ! -f "$GAME" ]; then
  echo "  没找到 $GAME，生成似乎没成功。把这句话告诉 AI。"
  echo ""
  echo "按回车键关闭。"; read -r _; exit 1
fi

echo ""
echo "  正在打开游戏……玩得开心。"
echo ""
echo "  ← →  移动          ↑ ↓  上浮/下潜"
echo "  Z    跳跃/加速      X    换气/踢击/出拳/挣脱"
echo "  回车  重新开始"
echo ""
open "$GAME"

echo "按回车键关闭这个窗口（游戏会继续开着）。"
read -r _
