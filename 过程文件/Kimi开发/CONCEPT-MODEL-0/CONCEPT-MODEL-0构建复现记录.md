# CONCEPT-MODEL-0 构建复现记录

## 环境

- macOS，bash
- Python：`过程文件/Kimi开发/.venv/bin/python3`（项目本地虚拟环境，Pillow 11.3.0）
- 无网络、无随机数、无外部图像输入；两张本地概念参考图仅供人工观察，不是构建输入。

## 构建命令

```bash
过程文件/Kimi开发/.venv/bin/python3 过程文件/Kimi开发/CONCEPT-MODEL-0/build_concept_model_0.py
```

标准输出：

```text
sprites: 12
checks: {"headMinSize": true, "bodyHeight": true, "headBodyRatio": true, "mainHtmlUnchanged": true}
blind order: [7, 2, 10, 4, 0, 9, 5, 11, 3, 8, 1, 6]
```

生成器内部强制检查（任一失败即非零退出）：

1. 全部 19 张 PNG 逐像素 alpha∈{0,255}；
2. 头部最小尺寸（yy≥约24px，dd≥约28px，容差2px）；
3. 全身高度（yy 60–72px，dd 70–84px，容差2px；实测 yy 65 / dd 78）；
4. 头身比 2.3–3.2（实测 yy 2.41 / dd 2.69）；
5. 主 HTML SHA-256 = `412416e95bfe4c98f4b039dc4a24fd9b28c2c23989254f22ee494d2e7bcde306`，不符即中止。

## 双跑确定性

同一工作区连续构建两次，对全部 21 个产物文件（12 精灵 + 7 审核图 + manifest + 生成器）比较 SHA-256：

```bash
find . -type f ! -name "*.md" | sort | xargs shasum -a 256   # 两轮各一次
diff run1.sha run2.sha
```

结果：两轮 21 个文件逐字节一致，diff 无输出。**确定性构建 PASS**。

## 边界确认

- 新增文件全部位于 `过程文件/Kimi开发/CONCEPT-MODEL-0/`（21 个产物 + 3 份记录）；
- 主 HTML 未改动（构建时钉值校验）；
- 未执行任何 git add / commit / branch / switch；
- CONCEPT-1A 失败稿目录原样保留、未改动、未复用其画法；
- 两张概念参考图与家庭照片未复制、未嵌入任何产物、未作为构建输入。
