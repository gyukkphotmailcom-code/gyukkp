#!/usr/bin/env node
/* ============================================================================
   验收脚本 —— 每一轮交付后都跑这个，不要靠人工读代码判断"做完了没有"
   ----------------------------------------------------------------------------
   用法：
     node 过程文件/Claude重启规划/verify.js
   退出码：
     0 = 全部阻塞项通过（可以进下一阶段）
     1 = 有阻塞项失败（必须返修）

   设计原则（这是本项目过去两周踩坑的直接对策）：
   1. 分成【阻塞】和【观察】两类。只有阻塞项能挡住进度。
      观察项只打印数字，永远不影响退出码 —— 它们的去处是《输出/建议台账.md》，
      不是"下一轮必须做掉的任务"。
   2. 不依赖浏览器、不依赖截图、不依赖人眼。任何人任何时候跑都是同一个结果。
   3. 不写死路径。两个 HTML 都从仓库根目录推导；美术版不存在时跳过而不是报错
      （美术版是本地产物，不进 git，别人 clone 下来本来就没有）。
   ========================================================================== */

const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');
const BUILDS = [
  { tag: '占位版', file: '阳阳水泳大乱斗-原版复刻.html', required: true },
  { tag: '美术版', file: '阳阳水泳大乱斗-本地美术勿提交.html', required: false },
];

/* ---------- 把单文件 HTML 里的 <script> 抠出来，在 node 里跑 ---------- */
function loadGame(file, search) {
  const html = fs.readFileSync(file, 'utf8');
  const m = html.match(/<script>([\s\S]*)<\/script>/);
  if (!m) throw new Error('没找到 <script> 段：' + file);

  const ctx = {
    fillStyle: '', imageSmoothingEnabled: false,
    fillRect() {}, drawImage() {}, clearRect() {},
  };
  const canvas = { width: 256, height: 224, style: {}, getContext: () => ctx };
  global.document = {
    getElementById: () => canvas, createElement: () => canvas,
    title: '', body: { appendChild() {}, innerHTML: '' }, addEventListener() {},
  };
  global.window = { innerWidth: 1024, innerHeight: 900, addEventListener() {} };
  global.addEventListener = () => {};
  global.requestAnimationFrame = () => {};
  global.location = { search: search || '' };
  global.URLSearchParams = URLSearchParams;

  // 探针：把内部符号暴露出来供检查。加在末尾，不改动游戏代码本身。
  const probe = `;globalThis.__api = {
    yy, dad, MATCH, tick, ST, SPRITES, Input, Input2, resetMatch, T: ORIGINAL_TUNING,
    CHARACTER_PROFILES: (typeof CHARACTER_PROFILES !== 'undefined' ? CHARACTER_PROFILES : null),
    poolMedals: (typeof poolMedals !== 'undefined' ? poolMedals : null),
    InputSources: (typeof InputSources !== 'undefined' ? InputSources : null),
    interaction: () => (typeof interaction !== 'undefined' ? interaction : null),
    hashState: (typeof hashState !== 'undefined' ? hashState : null),
  };`;
  new Function(m[1] + probe)();
  return { api: globalThis.__api, title: global.document.title };
}

/* ============================ 阻塞项 ============================ */

/* B1. 内置自检必须 PASS（它内部已包含 900 tick 的确定性双跑） */
function checkSelftest(file) {
  try {
    const { title } = loadGame(file, '?selftest');
    if (title.startsWith('PASS')) return { ok: true, note: title.slice(0, 90) };
    return { ok: false, note: title.slice(0, 200) || '(标题为空：自检可能中途抛异常)' };
  } catch (e) {
    return { ok: false, note: '抛异常：' + e.message };
  }
}

/* B2. 水下踢击必须能命中扣血，且全程只产生一个 interaction 对象 */
function checkKick(file) {
  const { api: A } = loadGame(file);
  A.resetMatch();
  const set = (c, dir, x) => {
    c.state = A.ST.UW; c.uwPose = 'H'; c.dir = dir;
    c.axFp = x * 256; c.ayFp = 140 * 256;
  };
  set(A.yy, 1, 120);
  set(A.dad, -1, 138);

  const hp0 = A.dad.hpFp, air0 = A.dad.airFp;
  const iids = new Set();
  let entered = false;
  for (let i = 0; i < 120; i++) {
    if (i === 2) { A.Input.B = 1; A.Input.pB = 1; }
    if (i === 3) { A.Input.B = 0; }
    A.tick();
    const it = A.interaction();
    if (it) iids.add(it.id);
    if (A.yy.state === 'KICK') entered = true;
  }
  const dmg = (hp0 - A.dad.hpFp) / 256;
  const airDmg = (air0 - A.dad.airFp) / 256;
  const ok = entered && dmg > 0 && airDmg >= A.T.kickAirDamageFp / 256 && iids.size === 1;
  return { ok, note: `进KICK=${entered} 扣血=${dmg} 掉氧=${airDmg.toFixed(1)} 交互对象数=${iids.size}（应为1）` };
}

/* B3a. 原版肩组：双方接触后都能连打B互殴，水下持续耗氧，直到一方气绝/败北。
   不允许原创的固定攻守身份、连打挣脱值、无输入超时或强制上限。 */
function checkGrapple(file) {
  const { api: A } = loadGame(file);
  if (!A.ST.GRAPPLE) return { skip: true, note: '未实现（B3 阶段实现后本项自动转为阻塞项）' };

  A.resetMatch();
  const isGrap = s => typeof s === 'string' && s.indexOf('GRAPPLE') >= 0;
  A.yy.state = A.ST.UW; A.yy.uwPose = 'H'; A.yy.dir = 1;
  A.yy.axFp = 110 * 256; A.yy.ayFp = 140 * 256;
  A.dad.state = A.ST.UW; A.dad.uwPose = 'H'; A.dad.dir = -1;
  A.dad.axFp = 130 * 256; A.dad.ayFp = 140 * 256;

  const foe = { L:0,R:0,U:0,D:0,A:0,B:0,pA:0,pB:0 };
  A.InputSources.TEST = () => foe;
  A.dad.input = 'TEST';
  const iids = new Set(), kinds = new Set();
  let bothIn = false;

  // 阶段一：朝对手游过去，应自动进入肩组
  A.Input.R = 1;
  for (let i = 0; i < 180 && !bothIn; i++) {
    A.tick();
    const it = A.interaction();
    if (it) { iids.add(it.id); kinds.add(it.kind); }
    if (isGrap(A.yy.state) && isGrap(A.dad.state)) bothIn = true;
  }
  A.Input.R = 0;

  const hpY0 = A.yy.hpFp, hpD0 = A.dad.hpFp;
  const airY0 = A.yy.airFp, airD0 = A.dad.airFp;

  // 先完全不按键：肩组不能被原创 idle 超时放开，但双方空气必须继续下降。
  let idleReleased = false;
  for (let i = 0; i < 120; i++) {
    A.tick();
    const it = A.interaction();
    if (it) { iids.add(it.id); kinds.add(it.kind); }
    if (!isGrap(A.yy.state) || !isGrap(A.dad.state)) { idleReleased = true; break; }
  }

  // 双方独立连打B，必须互相造成HP/空气伤害；最后由气绝/败北结束肩组。
  let freed = false;
  for (let i = 0; i < 1200 && !freed; i++) {
    const yp = i % 24 === 0 && isGrap(A.yy.state);
    const dp = i % 18 === 0 && isGrap(A.dad.state);
    A.Input.B = A.Input.pB = yp ? 1 : 0;
    foe.B = foe.pB = dp ? 1 : 0;
    A.tick();
    const it = A.interaction();
    if (it) { iids.add(it.id); kinds.add(it.kind); }
    if (!isGrap(A.yy.state) || !isGrap(A.dad.state)) freed = true;
  }
  const dmgY = (hpY0 - A.yy.hpFp) / 256, dmgD = (hpD0 - A.dad.hpFp) / 256;
  const airY = (airY0 - A.yy.airFp) / 256, airD = (airD0 - A.dad.airFp) / 256;
  const ok = bothIn && !idleReleased && dmgY > 0 && dmgD > 0 && airY > 0 && airD > 0 &&
             freed && iids.size === 1 && kinds.has('GRAPPLE');
  return {
    ok,
    note: `双方进入=${bothIn} idle误释放=${idleReleased} 双方扣血=${dmgY}/${dmgD}` +
          ` 双方掉氧=${airY.toFixed(1)}/${airD.toFixed(1)} 气绝后解开=${freed}` +
          ` 交互对象数=${iids.size}`,
  };
}

/* ---- B3b 骑头 / 拉脚（未实现时跳过，实现后自动转为阻塞项）----------------
   与肩组不同，规格书对这两者的脱身方式写得很具体，不存在"没有实机数据"的空白：
     开发规格书:67  骑乘脱身 —— 被骑时按住 ↓ 潜水脱身；**不得设计"↓+B 连打百分比挣脱槽"**
     开发规格书:334 被骑 —— 按住 ↓ 潜入水下逃脱；不显示原创挣脱百分比槽
     开发规格书:444 拉脚 —— **仅**在水面敌人下方使用 ↑+B 才能拉脚下水
   合同附录 A-1 只对肩组具名放行了连打挣脱槽，**不涵盖骑乘**。故这里同时做正向和
   反向验证：按住↓必须能脱身，而连打必须**不**能脱身。 */
function mkTestInput(A, who) {
  const inp = { L:0,R:0,U:0,D:0,A:0,B:0,pA:0,pB:0 };
  A.InputSources.TEST = () => inp;
  who.input = 'TEST';
  return inp;
}
function checkMount(file) {
  const { api: A } = loadGame(file);
  if (!A.ST.MOUNT && !A.ST.MOUNTED) return { skip: true, note: '未实现（B3b 阶段实现后转为阻塞项）' };
  if (!A.InputSources) return { skip: true, note: '未暴露 InputSources，测不了' };
  const isM = s => typeof s === 'string' && s.indexOf('MOUNT') >= 0;

  // 试若干水平间距，只要存在一次"跳过去能踩上头"即算进入条件成立
  const tryMount = gap => {
    const { api: G } = loadGame(file);
    G.resetMatch();
    G.dad.axFp = (120 + gap) * 256;
    G.Input.L = G.Input.R = G.Input.U = G.Input.D = G.Input.A = G.Input.B = 0;
    G.yy.axFp = 120 * 256;
    G.Input.R = 1; G.Input.A = 1; G.Input.pA = 1;
    for (let i = 0; i < 240; i++) {
      if (i === 2) { G.Input.A = 0; G.Input.pA = 0; }
      G.tick();
      if (isM(G.yy.state) || isM(G.dad.state)) return G;
    }
    return null;
  };
  let G = null;
  for (const gap of [8, 12, 16, 20, 24, 28, 32]) { G = tryMount(gap); if (G) break; }
  if (!G) return { ok: false, note: '试了 7 种间距都没能跳到对方头上进入骑乘（若是本检查的场景搭得不对，请说明）' };

  const air0 = G.dad.airFp;
  for (let i = 0; i < 60; i++) G.tick();
  const drains = G.dad.airFp < air0;

  // 反向：连打不该能脱身
  const mash = mkTestInput(G, G.dad);
  let mashEsc = false;
  for (let n = 0; n < 300; n++) {
    mash.B = n % 4 < 2 ? 1 : 0; mash.pB = n % 4 === 0 ? 1 : 0;
    mash.A = n % 6 < 3 ? 1 : 0; mash.pA = n % 6 === 0 ? 1 : 0;
    G.tick();
    if (!isM(G.dad.state)) { mashEsc = true; break; }
  }
  // 正向：按住 ↓ 必须能脱身
  let holdEsc = false;
  if (!mashEsc) {
    mash.A = mash.B = mash.pA = mash.pB = 0; mash.D = 1;
    for (let n = 0; n < 600; n++) { G.tick(); if (!isM(G.dad.state)) { holdEsc = true; break; } }
  }
  const ok = drains && !mashEsc && holdEsc;
  return { ok, note: `踩头成功 持续掉氧=${drains} 连打能脱身=${mashEsc}（应为false）` +
                     ` 按住↓能脱身=${mashEsc ? '未测' : holdEsc}` };
}

function checkLegpull(file) {
  const { api: A } = loadGame(file);
  if (!A.ST.LEGPULL && !A.ST.LEGPULLED) return { skip: true, note: '未实现（B3b 阶段实现后转为阻塞项）' };
  if (!A.InputSources) return { skip: true, note: '未暴露 InputSources，测不了' };
  const isL = s => typeof s === 'string' && s.indexOf('LEGPULL') >= 0;

  const run = below => {
    const { api: G } = loadGame(file);
    G.resetMatch();
    G.dad.axFp = below ? 120 * 256 : 190 * 256;        // below=是否位于水面敌人正下方
    G.yy.state = G.ST.UW; G.yy.uwPose = 'H';
    G.yy.axFp = 120 * 256; G.yy.ayFp = 150 * 256;
    const air0 = G.dad.airFp;
    for (let i = 0; i < 200; i++) {
      G.Input.U = 1; G.Input.B = i % 8 < 4 ? 1 : 0; G.Input.pB = i % 8 === 0 ? 1 : 0;
      G.tick();
      if (isL(G.yy.state) || isL(G.dad.state)) return { hit: true, air0, G };
    }
    return { hit: false };
  };
  const near = run(true), far = run(false);
  if (!near.hit) return { ok: false, note: '在水面敌人正下方 ↑+B 没能触发拉脚（若是本检查的场景搭得不对，请说明）' };
  for (let i = 0; i < 60; i++) near.G.tick();
  const drains = near.G.dad.airFp < near.air0;
  const ok = drains && !far.hit;
  return { ok, note: `正下方触发=true 拖拽掉氧=${drains} 远处也能触发=${far.hit}（应为false）` };
}

/* C2. 池底奖牌：应按原版从池底斜向上浮，水下人物接触后拾取；不改变HP胜负。 */
function checkMedals(file) {
  const { api: A } = loadGame(file);
  if (!A.poolMedals) return { ok: false, note: '没有池底奖牌系统' };
  A.resetMatch();
  A.yy.state = A.ST.UW; A.yy.uwPose = 'H'; A.yy.axFp = 20 * 256; A.yy.ayFp = 140 * 256;
  A.dad.state = A.ST.SURF;
  for (let i = 0; i < A.T.medalFirstTicks + 2; i++) A.tick();
  if (!A.poolMedals.length) return { ok: false, note: '到首枚生成时机仍无奖牌' };
  const m = A.poolMedals[0], y0 = m.yFp, hp0 = A.yy.hpFp;
  A.yy.axFp = m.xFp; A.yy.ayFp = A.T.uwBotFp; // 池底横游, hurtbox覆盖正在上浮的奖牌
  for (let i = 0; i < 60 && A.yy.medals === 0; i++) A.tick();
  const ok = A.yy.medals === 1 && A.yy.hpFp === hp0 && A.poolMedals.length === 0;
  return { ok, note: `生成=true 上浮=${m.yFp < y0} 拾取数=${A.yy.medals} HP未变=${A.yy.hpFp === hp0}` };
}

/* C3. 原版角色属性不能只写在注释里：不同 speed 必须真的产生不同水下位移，HP上限也要不同。 */
function checkProfiles(file) {
  const { api: A } = loadGame(file);
  if (!A.CHARACTER_PROFILES) return { ok: false, note: '没有原版角色性能模板' };
  A.resetMatch();
  A.yy.state = A.dad.state = A.ST.UW;
  A.yy.uwPose = A.dad.uwPose = 'H';
  A.yy.axFp = 40 * 256; A.dad.axFp = 170 * 256;
  A.yy.ayFp = A.dad.ayFp = 140 * 256;
  A.dad.input = '1P';
  const xY = A.yy.axFp, xD = A.dad.axFp;
  A.Input.R = 1;
  for (let i = 0; i < 20; i++) A.tick();
  A.Input.R = 0;
  const dy = A.yy.axFp - xY, dd = A.dad.axFp - xD;
  const hpDifferent = A.yy.maxHpFp !== A.dad.maxHpFp;
  const ok = A.yy.stats.source === 'KUNIO_JP' && A.dad.stats.source === 'TODD_USA' &&
             hpDifferent && dy > dd && dd > 0;
  return { ok, note: `模板=${A.yy.stats.source}/${A.dad.stats.source} HP上限=${A.yy.maxHpFp / 256}/${A.dad.maxHpFp / 256} 20tick位移=${(dy / 256).toFixed(2)}/${(dd / 256).toFixed(2)}` };
}

/* ---- B4 结算：时间到按 HP 判负时，败者必须进入 LOSE（台账 S-02 归此阶段）----
   判据：比赛结束后败者状态为 LOSE、胜者不是 LOSE。当前是"低血但未归零的败者
   会冻结在原状态"，所以本项现在是红的——它就是 B4 的靶子。 */
function checkResultPose(file) {
  const { api: A } = loadGame(file);
  A.resetMatch();
  A.MATCH.ticksLeft = 30;
  A.dad.hpFp = Math.floor(A.T.hpMaxFp / 4);            // 爸爸血少 → 时间到应判他负
  for (let i = 0; i < 400 && A.MATCH.phase === 'FIGHT'; i++) A.tick();
  if (A.MATCH.phase === 'FIGHT') return { ok: false, note: '时间到了但比赛没结束' };
  const ok = A.dad.state === A.ST.LOSE && A.yy.state !== A.ST.LOSE;
  return { ok, note: `败者(爸爸)状态=${A.dad.state}（应为LOSE） 胜者(阳阳)状态=${A.yy.state}` };
}

/* ---- 2P 固定输入回放（2026-08-27 起替代「CPU 对局」）----
   项目只做本地双人 1v1，没有 AI。本项用预先写死的双人按键序列驱动 Input/Input2：
   - 两次运行逐 tick 比较 hashState() 完整状态哈希
     （比赛状态/双方位置·状态·HP·氧气/interaction/奖牌与粒子均已纳入 hashState）；
   - 必须出现至少一次真实的对手攻击命中：HIT 状态只能由对手攻击造成
     （缺氧进的是 DROWN 不是 HIT），且攻击造成的 HP 损失与 DROWN 缺氧掉血分开统计，
     不得用「任意 interaction + 任意 HP 损失」冒充战斗成立；
   - 2P 侧必须有真实输入生效（证明双人输入通道都活着）。 */
function check2PReplay(file) {
  const { api: A } = loadGame(file);
  if (typeof A.hashState !== 'function') return { ok: false, note: '未暴露 hashState，无法做完整状态比对' };
  /* 固定脚本：[tick, side, key, value]，side 1=1P(Input) 2=2P(Input2)。
     场景：双方水下近距离对峙（与踢击检查同布局），1P 先踢，2P 后撤再回踢。
     按键序列为写死的常量，无 AI、无随机决策、无 Math.random。 */
  const SCRIPT = [
    [2,   1, 'B', 1], [3,   1, 'B', 0],        // 1P 踢击 → 应命中 2P（进 HIT）
    [50,  2, 'L', 1], [90,  2, 'L', 0],        // 2P 硬直结束后向左游开
    [100, 1, 'R', 1], [140, 1, 'R', 0],        // 1P 向右追
    [150, 2, 'B', 1], [151, 2, 'B', 0],        // 2P 回踢
  ];
  const TICKS = 200;
  const play = () => {
    const { api: G } = loadGame(file);
    G.resetMatch();
    G.yy.input = '1P'; G.dad.input = '2P';
    G.yy.state = G.ST.UW; G.yy.uwPose = 'H'; G.yy.dir = 1;
    G.yy.axFp = 120 * 256; G.yy.ayFp = 140 * 256;
    G.dad.state = G.ST.UW; G.dad.uwPose = 'H'; G.dad.dir = -1;
    G.dad.axFp = 136 * 256; G.dad.ayFp = 140 * 256;
    const hashes = [], hits = [];
    let drownLoss = 0, totalLossD = 0, prevHpD = G.dad.hpFp;
    const dadX0 = G.dad.axFp;
    for (let i = 0; i < TICKS; i++) {
      for (const [t, side, k, v] of SCRIPT) if (t === i) {
        const I = side === 1 ? G.Input : G.Input2;
        if (k === 'A' && v) I.pA = 1;
        if (k === 'B' && v) I.pB = 1;
        I[k] = v;
      }
      const preD = G.dad.state, preY = G.yy.state;
      G.tick();
      if (G.dad.state === 'HIT' && preD !== 'HIT') hits.push({ t: i, victim: 'dad', by: 'yy' });
      if (G.yy.state === 'HIT' && preY !== 'HIT') hits.push({ t: i, victim: 'yy', by: 'dad' });
      const lostD = prevHpD - G.dad.hpFp;
      if (lostD > 0) { totalLossD += lostD; if (G.dad.state === 'DROWN') drownLoss += lostD; }
      prevHpD = G.dad.hpFp;
      hashes.push(G.hashState());
    }
    return { hashes, hits, attackLoss: totalLossD - drownLoss, drownLoss,
             dadMoved: G.dad.axFp !== dadX0 };
  };
  const a = play(), b = play();
  const same = a.hashes.length === b.hashes.length && a.hashes.every((h, i) => h === b.hashes[i]);
  const ok = same && a.hits.length > 0 && a.attackLoss > 0 && a.dadMoved;
  return { ok, note: `逐tick全态hash一致=${same}(${a.hashes.length}tick) ` +
                     `攻击命中=${a.hits.length}次(${a.hits.map(h => h.by + '→' + h.victim + '@' + h.t).join(',') || '无'}) ` +
                     `攻击致HP损失=${(a.attackLoss / 256).toFixed(1)} DROWN掉血=${(a.drownLoss / 256).toFixed(1)} ` +
                     `2P输入生效=${a.dadMoved}` };
}

/* ---- 第一轮（2026-08-26 新开发计划）：水面锁位—方向预选—跳跃—下潜—上浮 状态链 ----
   依据：用户裁决「水下可以接近，水面上只能跳跃到对面」（动作矩阵§1）；
   说明书 P7–8（A跳跃/方向预选/按住↓潜る/水下十字移动）；diveTicks=10 为录像实测。 */
function checkSurfLock(file) {
  const run = key => {
    const { api: G } = loadGame(file);
    G.resetMatch();
    const x0 = G.yy.axFp;
    G.Input[key] = 1;
    for (let i = 0; i < 600; i++) G.tick();
    return { moved: G.yy.axFp !== x0, dir: G.yy.dir, pref: G.yy.prefDir, st: G.yy.state };
  };
  const r = run('R'), l = run('L');
  const ok = !r.moved && !l.moved && r.dir === 1 && r.pref === 1 && l.dir === -1 && l.pref === -1 &&
             r.st === 'SURF' && l.st === 'SURF';
  return { ok, note: `按R600tick移动=${r.moved}（应false） dir/pref=${r.dir}/${r.pref}` +
                     ` 按L600tick移动=${l.moved}（应false） dir/pref=${l.dir}/${l.pref}` };
}

function checkJumpDir(file) {
  const jump = preset => {
    const { api: G } = loadGame(file);
    G.resetMatch();
    if (preset) { G.Input[preset] = 1; for (let i = 0; i < 20; i++) G.tick(); G.Input[preset] = 0; }
    const x0 = G.yy.axFp;
    G.Input.A = 1; G.Input.pA = 1; G.tick();
    G.Input.A = 0; G.Input.pA = 0;
    const dir = G.yy.jumpDir;
    for (let i = 0; i < 80 && G.yy.state !== 'SURF'; i++) G.tick();
    return { dir, dx: (G.yy.axFp - x0) / 256, st: G.yy.state };
  };
  const v = jump(null), r = jump('R'), l = jump('L');
  /* 机制断言（2026-08-27 返修）：跳跃距离无原版样本，具体数值是 ORIGINAL_TUNING 里的估值，
     不能拿估值区间当通过标准。这里只验证方向预选机制成立：
     垂直跳 dx=0、预选右跳向右位移、预选左跳向左位移、同参数下左右位移镜像对称。 */
  const ok = v.dir === 0 && v.dx === 0 && r.dir === 1 && r.dx > 0 &&
             l.dir === -1 && l.dx < 0 && r.dx === -l.dx &&
             v.st === 'SURF' && r.st === 'SURF' && l.st === 'SURF';
  return { ok, note: `垂直跳dx=${v.dx}（应0） 预选右跳dir=${r.dir} dx=${r.dx}（应>0）` +
                     ` 预选左跳dir=${l.dir} dx=${l.dx}（应<0） 左右对称=${r.dx === -l.dx}（数值为估值，不作判据）` };
}

function checkDiveHold(file) {
  // 按住↓：diveTicks+1±1 个 tick 内必须进 UW（selftest 已钉死精确值，这里守回归）
  const { api: G } = loadGame(file);
  G.resetMatch();
  G.Input.D = 1;
  let uwAt = -1;
  for (let i = 0; i < 40 && uwAt < 0; i++) { G.tick(); if (G.yy.state === 'UW') uwAt = i; }
  G.Input.D = 0;
  const holdOk = uwAt >= 0 && (uwAt + 1) >= G.T.diveTicks && (uwAt + 1) <= G.T.diveTicks + 2;
  // 点按（5 tick 松手）：不得进 UW，必须按 diveBackSpeed 弹回 SURF
  const { api: H } = loadGame(file);
  H.resetMatch();
  H.Input.D = 1;
  let tapUw = false;
  for (let i = 0; i < 5; i++) { H.tick(); if (H.yy.state === 'UW') tapUw = true; }
  H.Input.D = 0;
  for (let i = 0; i < 40; i++) { H.tick(); if (H.yy.state === 'UW') tapUw = true; }
  const backOk = !tapUw && H.yy.state === 'SURF';
  const ok = holdOk && backOk;
  return { ok, note: `按住↓${uwAt + 1}tick进UW（应${G.T.diveTicks + 1}±1） 点按误进UW=${tapUw}（应false）` +
                     ` 点按弹回=${H.yy.state}（应SURF）` };
}

function checkEmerge(file) {
  const { api: G } = loadGame(file);
  G.resetMatch();
  G.yy.state = G.ST.UW; G.yy.uwPose = 'U'; G.yy.axFp = 120 * 256; G.yy.ayFp = G.T.uwTopFp;
  G.Input.U = 1;
  let emergeAt = -1, surfAt = -1, mono = true, prevAy = null;
  for (let i = 0; i < 60; i++) {
    G.tick();
    if (emergeAt >= 0 && G.yy.state === 'EMERGE') {
      if (prevAy !== null && G.yy.ayFp > prevAy) mono = false;   // 上浮期间 y 不得回升
      prevAy = G.yy.ayFp;
    }
    if (emergeAt < 0 && G.yy.state === 'EMERGE') { emergeAt = i; prevAy = G.yy.ayFp; }
    if (G.yy.state === 'SURF') { surfAt = i; break; }
  }
  const dur = surfAt - emergeAt;
  /* 行为断言（2026-08-27 返修）：emergeTicks 本身是估值，拿它检查实现自己等于循环论证。
     这里只验证行为性质——UW 顶部按↑必进 EMERGE、上浮过程 y 单调不回升、
     有限 tick 内回 SURF 且脚底回到水线锚点。时长数值只打印，不作判据。 */
  const ok = emergeAt >= 0 && surfAt > 0 && mono && dur > 0 &&
             G.yy.ayFp === G.T.surfFootY * 256;
  return { ok, note: `UW顶按↑→${emergeAt + 1}tick进EMERGE 单调上浮=${mono} ${dur}tick回SURF` +
                     `（时长${G.T.emergeTicks}为估值，不作判据） 脚底=${G.yy.ayFp / 256}（应${G.T.surfFootY}）` };
}

/* ============================ 观察项 ============================ */
/* 这些只打印，永不挡路。数字变化说明手感变了，但不代表做错了。 */

/* O1. 判定盒左右镜像是否对称（台账 S-06） */
function obsMirror(file) {
  const { api: A } = loadGame(file);
  const bad = [];
  let pairs = 0;
  for (const id in A.SPRITES.frames) {
    const p = id.split('.');
    if (p[2] !== 'R') continue;
    const R = A.SPRITES.frames[id];
    const L = A.SPRITES.frames[[p[0], p[1], 'L', p[3]].join('.')];
    if (!L) continue;
    for (const kind of ['hitbox', 'hurtbox']) {
      const br = R[kind], bl = L[kind];
      if (!br || !bl || !br.length || !bl.length) continue;
      pairs++;
      const offR = br[0].x - R.anchorX;
      const offL = bl[0].x - L.anchorX;
      if (offL !== -offR - br[0].w) bad.push(id + '/' + kind);
    }
  }
  return `${bad.length} / ${pairs} 组左右不对称` +
         (bad.length ? `（例：${bad[0]}）` : '');
}

/* O2. 判定盒相对帧宽的覆盖率（台账 S-04） */
function obsCoverage(file) {
  const { api: A } = loadGame(file);
  const out = [];
  for (const id of ['yy.SURF.R.0', 'yy.UW.R.0', 'dd.UW.R.0']) {
    const f = A.SPRITES.frames[id];
    if (!f || !f.hurtbox || !f.hurtbox[0]) continue;
    out.push(`${id.split('.')[0]}.${id.split('.')[1]} ${f.w}px→${Math.round(f.hurtbox[0].w / f.w * 100)}%`);
  }
  return out.join('  ');
}

/* ============================== 主流程 ============================== */

let failed = 0;
console.log('\n阳阳水泳大乱斗 —— 验收\n' + '='.repeat(60));

for (const b of BUILDS) {
  const file = path.join(REPO, b.file);
  console.log(`\n【${b.tag}】${b.file}`);

  if (!fs.existsSync(file)) {
    if (b.required) {
      console.log('  阻塞  文件不存在');
      failed++;
    } else {
      console.log('  跳过  文件不存在（美术版是本地产物，需先跑 bake.py --out）');
    }
    continue;
  }

  const checks = [['内置自检', checkSelftest], ['踢击命中', checkKick], ['原版肩组互殴', checkGrapple],
                  ['骑头', checkMount], ['拉脚', checkLegpull], ['池底奖牌', checkMedals], ['角色属性', checkProfiles],
                  ['结算姿态', checkResultPose], ['2P固定回放', check2PReplay],
                  ['水面锁位', checkSurfLock], ['跳跃方向预选', checkJumpDir],
                  ['按住下潜', checkDiveHold], ['上浮时序', checkEmerge]];
  for (const [name, fn] of checks) {
    let r;
    try { r = fn(file); } catch (e) { r = { ok: false, note: '抛异常：' + e.message }; }
    if (r.skip) { console.log(`  跳过  ${name}：${r.note}`); continue; }
    console.log(`  ${r.ok ? '通过' : '阻塞'}  ${name}：${r.note}`);
    if (!r.ok) failed++;
  }

  const obs = [['判定盒镜像', obsMirror], ['判定盒覆盖率', obsCoverage]];
  for (const [name, fn] of obs) {
    let s;
    try { s = fn(file); } catch (e) { s = '(测不了：' + e.message + ')'; }
    console.log(`  观察  ${name}：${s}`);
  }
}

console.log('\n' + '='.repeat(60));
if (failed) {
  console.log(`结论：${failed} 项阻塞，必须返修后才能进下一阶段。\n`);
  process.exit(1);
}
console.log('结论：阻塞项全部通过，可以进下一阶段。');
console.log('（"观察"项不挡路。数字有变化就记进《输出/建议台账.md》，标好归属阶段。）\n');
