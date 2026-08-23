# FORK-0-R1 精确提交清单（FORK-0-R2 修订版）

生成时间：2026-08-23（FORK-0-R1）；**2026-08-23 经 FORK-0-R2 按 Codex review 修订**
执行人：Kimi（唯一执行代理，未建 subagent）
性质：清单与建议草案。**截至 R2 修订时未执行任何 git add / commit / branch / switch，下列 git 命令仅供 Codex 审核，未执行。**

R2 修订内容：① 8 张含原版游戏画面的证据图/审核表从 A 类移入 B 类（Codex review 第 2 条）；② 修正第 9 节提交后模拟的 Git 常识错误（Codex review 第 5 条）；③ 统计与 add 草案同步更新；④ FORK-0 旧检查点清单已加作废标注（Codex review 第 4 条）；⑤ Git 不可达对象库的隐私问题记录于 `FORK-0-R2验收记录.md`（Codex review 第 3 条）。

---

## 1. 基线信息

- 当前分支：`main`
- 当前 HEAD：`679cb3615862eb233f6a219e56dbfc15aaac90be`（stage3b-m-identity-mask-approved）
- staged 文件数：**0**（`git diff --cached --name-only` 为空）
- 工作区已修改（未暂存）：4 个已跟踪文件（`.gitignore`、`开发规格书.md`、`输出/给Kimi的分阶段执行指令.md`、`阳阳水泳大乱斗-原版复刻.html`；`输出/概念画风版开发路线草案.md` 为未跟踪新增，不计入修改，见 4.1）
- 未跟踪且未忽略：81 个文件（含 FORK-0 目录下 4 份报告；R2 将 8 张原版画面图移入忽略后由 88 减至 80，再加本轮新建的本文件修订版与 R2 验收记录）
- 未跟踪且已忽略：7,486 个文件（约 493MB，绝大多数为 .venv、st3_shots、原版参考帧）
- 分支列表：仅 `main`；`fc-replica`、`concept-style-game` 均不存在（未创建）

## 2. 分类汇总

| 分类 | 含义 | 数量 | 大小 |
|---|---|---|---|
| A-修改 | 进入暂停点提交的已跟踪修改 | 4 | 约 186KB（按新 blob 全量） |
| A-新增 | 进入暂停点提交的未跟踪文件 | 81 | 约 1.35MB |
| B | 只留本地、由 .gitignore 保护 | 7,486 | 约 493MB |
| C | 暂时无法判断、待 Codex 决定 | 5 组 | 见第 6 节 |

**建议暂停点提交合计：85 个路径，约 1.5MB。**（R1 为 92 个路径约 2.9MB；R2 移出 8 张原版画面图共 1,356,176 字节，新增 1 份 R2 验收记录。）

## 3. A 类：已修改文件（4 个，逐项）

| 文件 | 分类 | 原因 |
|---|---|---|
| `.gitignore` | A | 忽略规则本身必须入库，否则干净环境无法复现同一忽略边界；R1 追加 8 条 + R2 追加 8 条（见第 5.2 节） |
| `开发规格书.md` | A | FC 复刻验收标准的当前版本，分叉决策的依据文档 |
| `输出/给Kimi的分阶段执行指令.md` | A | 阶段 1-7 执行框架的当前版本 |
| `阳阳水泳大乱斗-原版复刻.html` | A | 当前主程序（+1,115 行），FC 路线暂停点的实际游戏状态；经 grep 验证零外部资源引用、完全自足 |

## 4. A 类：未跟踪文件（81 个，逐文件）

> 说明：本节是**分类清单**，第 8 节是**操作草案**，同一文件在两节各出现一次属正常设计；第 8 节 add 草案内每个路径仅出现一次（已用 `sort | uniq -c` 机器核验，无重复行）。

### 4.1 输出/（1 个）
- `输出/概念画风版开发路线草案.md` — 记录分叉决策与概念版参数，按指令必须入库（R2 已修订人物尺寸参数）

### 4.2 过程文件/Codex开发/R3B-I-P2/（13 个）— Codex 概念人物实验阶段
- `build_concept_sprites_r3bip2.py` — 生成器（自足，无外部输入依赖）
- `concept_sprites_r3bip2.json` — 生成数据（P3 生成器不依赖它；但作为该阶段正式数据产物入库）
- `sprites/BREATH_dad_L.png`、`sprites/BREATH_yy_L.png`、`sprites/JUMP_dad_L.png`、`sprites/JUMP_yy_L.png`、`sprites/SURFACE_dad_L.png`、`sprites/SURFACE_yy_L.png`、`sprites/SWIM_dad_L.png`、`sprites/SWIM_yy_L.png` — 正式精灵产物
- `阶段R3B-I-P2人物动作对照表.png`、`阶段R3B-I-P2游戏场景效果图.png` — 正式审核材料
- `阶段R3B-I-P2说明.md` — 阶段记录

### 4.3 过程文件/Codex开发/R3B-I-P3/（17 个）— Codex 身份强化实验阶段
- `build_identity_enhanced_r3bip3.py` — 生成器；**依赖证据**：其 `SOURCE` 指向 `R3B-I/identity_sprites_r3bi.json`，该输入在本清单 4.5 节入库，干净环境可重建
- `identity_enhanced_r3bip3.json` — 生成数据
- `sprites/JUMP_AIR_dd_L.png`、`JUMP_AIR_dd_R.png`、`JUMP_AIR_yy_L.png`、`JUMP_AIR_yy_R.png`、`SURF0_dd_L.png`、`SURF0_dd_R.png`、`SURF0_yy_L.png`、`SURF0_yy_R.png`、`UW_NORMAL_dd_L.png`、`UW_NORMAL_dd_R.png`、`UW_NORMAL_yy_L.png`、`UW_NORMAL_yy_R.png`（均位于 `sprites/`）— 正式精灵产物
- `阶段R3B-I-P3游戏尺寸预览.png`、`阶段R3B-I-P3身份强化对照表.png` — 正式审核材料
- `阶段R3B-I-P3说明.md` — 阶段记录

### 4.4 过程文件/Kimi开发/FORK-0/（4 个）
- `FORK-0-Git检查点清单.md` — 上一轮审计报告（顶部已加"已由 FORK-0-R1 替代"作废标注，仅作历史存档）
- `FORK-0-R1精确提交清单.md` — 本文件（R2 修订版）
- `FORK-0-R1验收记录.md` — R1 轮验收记录
- `FORK-0-R2验收记录.md` — 本轮（R2）验收记录

### 4.5 过程文件/Kimi开发/R3B-I/（19 个）— R3B-I 身份稿阶段（视觉未通过，作为失败对照与下游输入保留）
- `build_identity_sprites_r3bi.py` — 生成器；输入全部已跟踪（sprites_r3a_human_baked.js、build_sprites_r3a.py、avatar_paint.py、R3B-M 三件套），干净环境可确定性重建
- `identity_sprites_r3bi.json` — 生成数据；**依赖证据**：R3B-I-P1 生成器与 Codex P3 生成器均直接读取它，缺了会崩，必须入库
- `sprites/` 下 12 张：`SURF0_yy_L/R.png`、`SURF0_dd_L/R.png`、`JUMP_AIR_yy_L/R.png`、`JUMP_AIR_dd_L/R.png`、`UW_NORMAL_yy_L/R.png`、`UW_NORMAL_dd_L/R.png`；**依赖证据**：R3B-I-P1 生成器读取其中 4 张 L 向旧稿作对照基线，缺了会崩，必须入库
- `阶段R3B-I构建复现记录.md`、`阶段R3B-I身份稿清单.md`、`阶段R3B-I验收记录.md` — 正式记录
- `阶段R3B-I身份稿审核表.png`、`阶段R3B-I身份稿盲审图.png` — 正式审核材料（内容为自研人物稿，不含原版画面）

### 4.6 过程文件/Kimi开发/R3B-I-P1/（12 个）— 本人特征小范围验证阶段
- `build_likeness_sprites_r3bip1.py` — 生成器；输入为 R3B-I json + 4 张 L 向旧稿 PNG（均在 4.5 节入库）
- `likeness_sprites_r3bip1.json`、`blind_map.json` — 生成数据与盲审编号映射
- `sprites/SURF0_yy_L.png`、`SURF0_dd_L.png`、`JUMP_AIR_yy_L.png`、`JUMP_AIR_dd_L.png` — 正式精灵产物
- `阶段R3B-I-P1本人特征对照表.png`、`阶段R3B-I-P1盲审图.png` — 正式审核材料
- `阶段R3B-I-P1身份稿清单.md`、`阶段R3B-I-P1构建复现记录.md`、`阶段R3B-I-P1验收记录.md` — 正式记录

### 4.7 过程文件/Kimi开发/ 根目录（12 个）— 阶段3/3A0/3A 的生成器与正式记录
- `build_sprites.py` — 当前主HTML 16×16 身体的生成器（自足）
- `build_sprites_3a.py`、`build_sprites_3a0.py` — 3A/3A0 生成器；注意：二者依赖被忽略的原版参考帧，干净环境不可重建（见第 7 节风险 R2），但作为源码存档
- `阶段3验收记录.md`、`阶段3A0构建复现记录.md`、`阶段3A0精灵清单.md`、`阶段3A0-R1返修验收记录.md`、`阶段3A0-R2接手验收记录.md`、`阶段3A精灵清单.md` — 正式文字记录
- `阶段3演示.gif`、`阶段3A0场景验收图.png`、`阶段3A0场景验收图-8x.png` — 自研游戏画面验收证据（R2 已逐张目检：内容为自研场景与自研人物，不含原版游戏画面）

### 4.8 过程文件/Kimi开发/阶段3/（3 个）— 阶段3 正式验收证据
- `证据-DIVE-UW连续.png`、`证据-纯上升-EMERGE连续.png`、`证据-跳跃三帧.png`
- R2 已逐张目检：三张均为自研游戏画面的连续帧拼接（阳阳/爸爸在自研 FC 风泳池中），不含原版游戏画面，保留 A 类

## 5. B 类：只留本地、由 .gitignore 保护（7,486 个）

### 5.1 原 .gitignore 已覆盖（R1/R2 未改动这些规则）

- 家庭照片 3 张（根目录 `17296.jpeg`、`IMG_0387.jpeg`、`IMG_0806.jpeg`，共 6.15MB）— 私人隐私，已具名忽略
- 私人概念图/含照片预览 3 张（2.89MB）：
  - `过程文件/Kimi开发/R3B-I-LikenessTest/阳阳爸爸头像方向参考-本地勿提交.png`
  - `过程文件/Codex开发/R3B-I-P2/阳阳爸爸多动作概念参考-本地勿提交.png`
  - `过程文件/Kimi开发/阶段2头像预览-本地含照片.png`
- 照片派生中间产物（已具名忽略，check-ignore 验证命中）：`crop_yy_ref.png`、`crop_dd_ref.png`、`yy_24.png`、`dd_24.png`、`yy_24down.png`、`dd_24down.png`（均由已跟踪的 `avatar_gen.py` 从家庭照片机械生成，可再生成且含身份特征）
- `过程文件/原版参考/`（73 个，89.25MB）— 原版视频、提取帧、截图
- `过程文件/Kimi开发/st3_shots/`（5,222 个，293.32MB）、`action_scan/`（317 个，8.17MB）— 调试/扫描截图
- `过程文件/Kimi开发/.venv/`（1,725 个，87.46MB）— 虚拟环境
- 可再生成 baked/preview/扫描件：`pool_data.js`、`bg_data.js`、`avatar_baked.js`、`sprites_baked.js`、`sprites_3a_baked.js`、`ref_frames_sheet.png`、`scan_a.png`、`scan_b.png`、`jump_frames.png`、`jump_scan.png`、`redtrack.csv`、`*_preview.png` 等
- 一次性迁移/调试脚本：`migrate_r3.py`、`migrate_r4.py`、`migrate_r5.py`、`migrate_r6.py`、`oxy_scan.py`、`shoot_r6.py`
- 根目录 4 张 `阶段3证据-*-f?????.png` 单帧细节图（具名规则，R1 前已存在）
- `.DS_Store` ×2

### 5.2 R1 追加的 8 条规则（已写入 .gitignore）

- `过程文件/Kimi开发/R3B-I/diff/` — 36 张 diff 图，生成器可确定性重建
- `过程文件/Kimi开发/R3B-I/identity_sprites_r3bi_baked.js` — 无消费者（指令禁止被主程序引用），可确定性重建
- `过程文件/Kimi开发/R3B-I-P1/diff/`、`过程文件/Kimi开发/R3B-I-P1/masks/` — 可确定性重建
- `过程文件/Kimi开发/阶段3/s*.png`、`过程文件/Kimi开发/阶段3/z_*.png` — 37 张开发诊断截图
- `过程文件/Kimi开发/阶段3A0参考/` — 10 个原版帧派生蒙版/subject json（见 C 类第 1 项）
- `过程文件/Kimi开发/sprites_3a0_baked.js` — 无消费者（见 C 类第 2 项）

### 5.3 R2 追加的 8 条规则（已写入 .gitignore 末尾，Codex review 第 2 条要求）

含原版游戏画面的证据图/审核表，只留本地，不再入库：

- `过程文件/Kimi开发/阶段3证据-下潜-f15615-f15620.png`
- `过程文件/Kimi开发/阶段3证据-换气-f16044-f16066.png`
- `过程文件/Kimi开发/阶段3证据-水下方向-f15554-f15680.png`
- `过程文件/Kimi开发/阶段3证据-跳跃-官方截图.png`
- `过程文件/Kimi开发/阶段3A0精灵审核表-1.png`
- `过程文件/Kimi开发/阶段3A0精灵审核表-2.png`
- `过程文件/Kimi开发/阶段3A精灵审核表-1.png`
- `过程文件/Kimi开发/阶段3A精灵审核表-2.png`

R1 曾把这 8 张列为 A 类并声称"A 类基本不含原版游戏画面"，该分类错误；R2 已逐张 check-ignore 验证命中。对应阶段的文字验收记录仍入库，证据图本地留存。

## 6. C 类：暂时无法判断，待 Codex 决定（5 组）

1. **`过程文件/Kimi开发/阶段3A0参考/`（10 个，约 112KB）**
   - 用途：`build_sprites_3a0.py` 的输入（原版视频帧提取的蒙版与 subject 数据）
   - 依赖它的代码：`build_sprites_3a0.py`
   - 矛盾：入库则 3A0 可重建，但内容属原版帧派生素材；不入库则 3A0 与阶段3（依赖 IMG_4628.mov）一样不可干净重建
   - 我的推荐：**B（只留本地）**。理由：3A0 是被 R3A 取代的已作废实验，其文字验收记录已入库存档；阶段3 已有同样不可重建的先例；且与 R2 确立的"原版画面素材不入库"边界一致。已按 B 加忽略规则。

2. **`过程文件/Kimi开发/sprites_3a0_baked.js`（31KB）**
   - 用途：3A0 精灵烘焙输出，无任何运行时消费者
   - 依赖：由 `build_sprites_3a0.py` 生成；若第 1 项不入库则不可重建
   - 我的推荐：**B**。已加忽略规则。

3. **`过程文件/Kimi开发/R3B-I/identity_sprites_r3bi_baked.js`（33KB）**
   - 用途：R3B-I 烘焙 JS 输出；指令明确"不能被主程序引用"，grep 验证主HTML 无引用，无任何消费者
   - 依赖：由 `build_identity_sprites_r3bi.py` 从已跟踪输入确定性生成（双跑 SHA 一致已有记录）
   - 我的推荐：**B**。已加忽略规则。

4. **`过程文件/Kimi开发/R3B-I/diff/`（36 张 PNG）**
   - 用途：12 张身份稿逐张的 changed-pixel 二值图/彩色差异图/蒙版外差异证明图；R3B-I 验收记录引用了其中 9 张作为证据
   - 依赖：由生成器确定性重建
   - 矛盾：可重建 → B；但验收记录引用了具体图 → 若 Codex 要求证据随库存档，应挑 9 张被引用图入库
   - 我的推荐：**B（整体忽略）**，备选方案：仅将验收记录点名的 9 张移入 A。

5. **`过程文件/Kimi开发/R3B-I-P1/diff/` 与 `masks/`（12 张 PNG）**
   - 用途：P1 四张稿的区域内/外差异证明与头部例外蒙版；P1 验收记录引用
   - 依赖：可确定性重建
   - 我的推荐：**B**，同第 4 项理由。

> 若 Codex 对以上 5 组全部同意 B，则本清单无需改动即可执行；若任一组改判 A，需在第 8 节 add 草案中追加对应具名路径并回退相应 .gitignore 规则。

## 7. 主要风险

- R1：**私人/原版素材入库风险——已排除（R2 加强）。** 3 张家庭照片、2 张概念图、1 张含照片预览、6 个照片派生中间文件全部被具名忽略规则命中（check-ignore 逐一验证）；原版视频/帧/截图 89.25MB 被目录规则忽略；R2 再将 8 张含原版画面的证据图/审核表移入 B。A 类 85 个路径中无任何含真人身份特征或原版游戏画面的文件（4.7/4.8 节保留的 6 张图均已逐张目检确认为自研画面）。
- R2：**不可干净重建的阶段。** 阶段3（依赖被忽略的 IMG_4628.mov）、3A0/3A（依赖被忽略的原版参考帧）在干净环境无法重建，仅源码+文字验收记录入库。R3B-I、R3B-I-P1、P2、P3 四个最新阶段输入链路完整、可确定性重建。
- R3：`阶段3演示.gif`（约 0.14MB）为自研游戏演示动画，属正式验收证据，已列 A。
- R4：**Git 不可达对象库隐私残留**（Codex review 第 3 条）：三张家庭照片及原版视频的内容仍存在于本地 `.git` 不可达对象中（历史上曾被 add 后移除）。它们不在任何可达提交、仓库无远程，未发现外泄；但不能宣称 Git 层面已隐私干净。清除（`git gc --prune=now` 等）属不可恢复操作，需用户和 Codex 单独批准，本轮未执行，详见 `FORK-0-R2验收记录.md` 第 6 节。

## 8. 建议的 git 操作（草案，仅供 Codex 审核，未执行）

逐文件添加，禁止 `git add .` / `-A` / 目录整包 / 通配符：

```bash
# 第 1 步：修改类（4 个）
git add -- ".gitignore" "开发规格书.md" "输出/给Kimi的分阶段执行指令.md" "阳阳水泳大乱斗-原版复刻.html"

# 第 2 步：输出/（1 个）
git add -- "输出/概念画风版开发路线草案.md"

# 第 3 步：Codex R3B-I-P2（13 个）
git add -- "过程文件/Codex开发/R3B-I-P2/build_concept_sprites_r3bip2.py" \
  "过程文件/Codex开发/R3B-I-P2/concept_sprites_r3bip2.json" \
  "过程文件/Codex开发/R3B-I-P2/sprites/BREATH_dad_L.png" \
  "过程文件/Codex开发/R3B-I-P2/sprites/BREATH_yy_L.png" \
  "过程文件/Codex开发/R3B-I-P2/sprites/JUMP_dad_L.png" \
  "过程文件/Codex开发/R3B-I-P2/sprites/JUMP_yy_L.png" \
  "过程文件/Codex开发/R3B-I-P2/sprites/SURFACE_dad_L.png" \
  "过程文件/Codex开发/R3B-I-P2/sprites/SURFACE_yy_L.png" \
  "过程文件/Codex开发/R3B-I-P2/sprites/SWIM_dad_L.png" \
  "过程文件/Codex开发/R3B-I-P2/sprites/SWIM_yy_L.png" \
  "过程文件/Codex开发/R3B-I-P2/阶段R3B-I-P2人物动作对照表.png" \
  "过程文件/Codex开发/R3B-I-P2/阶段R3B-I-P2游戏场景效果图.png" \
  "过程文件/Codex开发/R3B-I-P2/阶段R3B-I-P2说明.md"

# 第 4 步：Codex R3B-I-P3（17 个）
git add -- "过程文件/Codex开发/R3B-I-P3/build_identity_enhanced_r3bip3.py" \
  "过程文件/Codex开发/R3B-I-P3/identity_enhanced_r3bip3.json" \
  "过程文件/Codex开发/R3B-I-P3/sprites/JUMP_AIR_dd_L.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/JUMP_AIR_dd_R.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/JUMP_AIR_yy_L.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/JUMP_AIR_yy_R.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/SURF0_dd_L.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/SURF0_dd_R.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/SURF0_yy_L.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/SURF0_yy_R.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/UW_NORMAL_dd_L.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/UW_NORMAL_dd_R.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/UW_NORMAL_yy_L.png" \
  "过程文件/Codex开发/R3B-I-P3/sprites/UW_NORMAL_yy_R.png" \
  "过程文件/Codex开发/R3B-I-P3/阶段R3B-I-P3游戏尺寸预览.png" \
  "过程文件/Codex开发/R3B-I-P3/阶段R3B-I-P3说明.md" \
  "过程文件/Codex开发/R3B-I-P3/阶段R3B-I-P3身份强化对照表.png"

# 第 5 步：FORK-0 报告（4 个）
git add -- "过程文件/Kimi开发/FORK-0/FORK-0-Git检查点清单.md" \
  "过程文件/Kimi开发/FORK-0/FORK-0-R1精确提交清单.md" \
  "过程文件/Kimi开发/FORK-0/FORK-0-R1验收记录.md" \
  "过程文件/Kimi开发/FORK-0/FORK-0-R2验收记录.md"

# 第 6 步：Kimi R3B-I（19 个）
git add -- "过程文件/Kimi开发/R3B-I/build_identity_sprites_r3bi.py" \
  "过程文件/Kimi开发/R3B-I/identity_sprites_r3bi.json" \
  "过程文件/Kimi开发/R3B-I/sprites/JUMP_AIR_dd_L.png" \
  "过程文件/Kimi开发/R3B-I/sprites/JUMP_AIR_dd_R.png" \
  "过程文件/Kimi开发/R3B-I/sprites/JUMP_AIR_yy_L.png" \
  "过程文件/Kimi开发/R3B-I/sprites/JUMP_AIR_yy_R.png" \
  "过程文件/Kimi开发/R3B-I/sprites/SURF0_dd_L.png" \
  "过程文件/Kimi开发/R3B-I/sprites/SURF0_dd_R.png" \
  "过程文件/Kimi开发/R3B-I/sprites/SURF0_yy_L.png" \
  "过程文件/Kimi开发/R3B-I/sprites/SURF0_yy_R.png" \
  "过程文件/Kimi开发/R3B-I/sprites/UW_NORMAL_dd_L.png" \
  "过程文件/Kimi开发/R3B-I/sprites/UW_NORMAL_dd_R.png" \
  "过程文件/Kimi开发/R3B-I/sprites/UW_NORMAL_yy_L.png" \
  "过程文件/Kimi开发/R3B-I/sprites/UW_NORMAL_yy_R.png" \
  "过程文件/Kimi开发/R3B-I/阶段R3B-I构建复现记录.md" \
  "过程文件/Kimi开发/R3B-I/阶段R3B-I身份稿审核表.png" \
  "过程文件/Kimi开发/R3B-I/阶段R3B-I身份稿清单.md" \
  "过程文件/Kimi开发/R3B-I/阶段R3B-I身份稿盲审图.png" \
  "过程文件/Kimi开发/R3B-I/阶段R3B-I验收记录.md"

# 第 7 步：Kimi R3B-I-P1（12 个）
git add -- "过程文件/Kimi开发/R3B-I-P1/blind_map.json" \
  "过程文件/Kimi开发/R3B-I-P1/build_likeness_sprites_r3bip1.py" \
  "过程文件/Kimi开发/R3B-I-P1/likeness_sprites_r3bip1.json" \
  "过程文件/Kimi开发/R3B-I-P1/sprites/JUMP_AIR_dd_L.png" \
  "过程文件/Kimi开发/R3B-I-P1/sprites/JUMP_AIR_yy_L.png" \
  "过程文件/Kimi开发/R3B-I-P1/sprites/SURF0_dd_L.png" \
  "过程文件/Kimi开发/R3B-I-P1/sprites/SURF0_yy_L.png" \
  "过程文件/Kimi开发/R3B-I-P1/阶段R3B-I-P1本人特征对照表.png" \
  "过程文件/Kimi开发/R3B-I-P1/阶段R3B-I-P1构建复现记录.md" \
  "过程文件/Kimi开发/R3B-I-P1/阶段R3B-I-P1盲审图.png" \
  "过程文件/Kimi开发/R3B-I-P1/阶段R3B-I-P1身份稿清单.md" \
  "过程文件/Kimi开发/R3B-I-P1/阶段R3B-I-P1验收记录.md"

# 第 8 步：Kimi开发 根目录 阶段3/3A0/3A（12 个；R2 已移除 8 张含原版画面的证据图/审核表）
git add -- "过程文件/Kimi开发/build_sprites.py" \
  "过程文件/Kimi开发/build_sprites_3a.py" \
  "过程文件/Kimi开发/build_sprites_3a0.py" \
  "过程文件/Kimi开发/阶段3A0-R1返修验收记录.md" \
  "过程文件/Kimi开发/阶段3A0-R2接手验收记录.md" \
  "过程文件/Kimi开发/阶段3A0场景验收图-8x.png" \
  "过程文件/Kimi开发/阶段3A0场景验收图.png" \
  "过程文件/Kimi开发/阶段3A0构建复现记录.md" \
  "过程文件/Kimi开发/阶段3A0精灵清单.md" \
  "过程文件/Kimi开发/阶段3A精灵清单.md" \
  "过程文件/Kimi开发/阶段3演示.gif" \
  "过程文件/Kimi开发/阶段3验收记录.md"

# 第 9 步：阶段3 证据目录（3 个，自研画面，R2 已目检）
git add -- "过程文件/Kimi开发/阶段3/证据-DIVE-UW连续.png" \
  "过程文件/Kimi开发/阶段3/证据-纯上升-EMERGE连续.png" \
  "过程文件/Kimi开发/阶段3/证据-跳跃三帧.png"

# 第 10 步：核验后提交与分支（命令草案，待批准）
git status --short           # 预期：显示 85 行 staged 条目（"A "/"M " 开头），无未跟踪未忽略文件
git diff --cached --stat     # 预期：85 个路径
git commit -m "wip-fc-route-before-concept-fork"   # 提交名待 Codex/用户确认
git branch fc-replica        # 保留 FC 路线指针（若已存在同名分支则停止，不得强制覆盖）
git switch -c concept-style-game   # 若已存在同名分支则停止
```

## 9. 提交后工作区模拟（R2 修正）

- 执行第 8 节全部 `git add` 之后、`git commit` 之前：`git status --short` **不会为空**，而是显示 85 行暂存条目（新增为 `A `、修改为 `M `）；未跟踪未忽略文件应为 0。
- 执行 `git commit` 之后：`git status --short` 预期输出为**空**（无 modified、无 staged、无未跟踪未忽略）。
- 剩余本地文件全部为 ignored（7,486 个），只在 `git status --ignored` 下可见——**注意：ignored 文件在物理目录中仍存在，切分支时保留在原位，这是期望行为**（私人素材和可再生成缓存本来就不跨分支移动，也不会造成脏工作区）。
- 结论：**commit 之后工作区可达到完全干净**，前提是期间不新增/不修改任何文件。

## 10. 0 字节文件恢复核验（R1 已完成，R2 复核仍一致）

- 文件：`过程文件/Kimi开发/R3B-M/阶段R3B-M构建复现记录.md`
- 恢复前：工作区 0 字节，SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（空文件特征值）
- 操作：`git restore --source=HEAD -- "过程文件/Kimi开发/R3B-M/阶段R3B-M构建复现记录.md"`（指令明确授权）
- 恢复后：6,558 字节，SHA-256 `bfaf9e8598bf7c99cb5f49d8a755e68545a28d32ab17f22831091e904c1265da`，与 HEAD 版本一致
- 正文未做任何修改；git status 已不再显示该文件
