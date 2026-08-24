# CONCEPT-1A 构建复现记录

## 环境

- macOS，bash
- Python：`过程文件/Kimi开发/.venv/bin/python3`（项目本地虚拟环境，Pillow 11.3.0）
- 无网络访问、无随机数、无外部图像输入；两张本地概念参考图仅供人工观察，不作为构建输入。

## 构建命令

```bash
过程文件/Kimi开发/.venv/bin/python3 过程文件/Kimi开发/CONCEPT-1A/build_concept_1a.py
```

标准输出：

```text
sprites: 18
checks: {"headMinSize": true, "cellSize": true, "alphaBinary": true, "mainHtmlUnchanged": true}
blind order: [5, 11, 0, 8, 14, 2, 17, 6, 9, 13, 1, 16, 4, 10, 7, 15, 3, 12]
```

生成器内部强制检查（任一失败即非零退出、不落盘新产物）：

1. 每张精灵与每张审核图逐像素检查 alpha∈{0,255}；
2. 头部最小尺寸门槛（yy≥约24×24，dd≥约28×28，容差2px）；
3. 单元格规格（横向动作 112/128 宽，其余 96×96）；
4. 主 HTML SHA-256 必须等于 `412416e95bfe4c98f4b039dc4a24fd9b28c2c23989254f22ee494d2e7bcde306`，否则立即中止。

## 双跑确定性

同一工作区连续构建两次，对全部 25 个产物文件（18 精灵 + 5 审核图 + manifest + 清单外无其他）比较 SHA-256：

```bash
find . -type f ! -name "*.md" | sort | xargs shasum -a 256   # 两轮各一次
diff run1.sha run2.sha
```

结果：两轮 25 个文件逐字节一致，diff 无输出。**确定性构建 PASS**。

## 产物清单与哈希

见 `CONCEPT-1A精灵清单.md` 与 `concept_1a_manifest.json`（两者哈希一致，可互相核对）。

## 边界确认

- 本轮未修改、未新增 CONCEPT-1A 目录以外的任何文件；
- 主 HTML 未改动（生成器构建时实时钉值校验）；
- 未执行任何 git add / commit / branch / switch；
- 两张概念参考图与家庭照片未被读取为构建输入、未复制、未嵌入任何产物。
