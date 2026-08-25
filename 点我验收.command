#!/bin/bash
# 双击这个文件就能验收当前代码，不需要懂命令行。
# 结果里只看最后一行"结论"就够了。

cd "$(dirname "$0")" || exit 1

echo ""
echo "正在检查游戏代码……"

if ! command -v node >/dev/null 2>&1; then
  echo ""
  echo "  没找到 node（运行检查需要它）。"
  echo "  把这句话告诉 AI 就行，它会帮你装。"
  echo ""
  echo "按回车键关闭这个窗口。"
  read -r _
  exit 1
fi

node 过程文件/Claude重启规划/verify.js
code=$?

echo ""
echo "============================================================"
if [ $code -eq 0 ]; then
  echo "  ✅ 通过了。可以让 Kimi 做下一个阶段。"
else
  echo "  ❌ 没通过。把上面整段内容复制给 Kimi，让它修。"
fi
echo "============================================================"
echo ""
echo "按回车键关闭这个窗口。"
read -r _
