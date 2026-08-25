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
    yy, dad, MATCH, tick, ST, SPRITES, Input, resetMatch,
    interaction: () => (typeof interaction !== 'undefined' ? interaction : null),
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

  const hp0 = A.dad.hpFp;
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
  const ok = entered && dmg > 0 && iids.size === 1;
  return { ok, note: `进KICK=${entered} 扣血=${dmg} 交互对象数=${iids.size}（应为1）` };
}

/* B3a. 肩组：必须双方同时进入、出拳能扣血、只有一个交互对象、且**不会永久锁死**
   （规格书 3.4 明确点名"禁止让两名角色各自猜测对方状态，否则会产生先手偏差、
     穿插和永久锁死"，所以"能解开"和"能进入"同等重要，必须机器验证。）
   未实现时跳过而不是失败：B3 之前的提交跑这个脚本也应该是绿的。 */
function checkGrapple(file) {
  const { api: A } = loadGame(file);
  if (!A.ST.GRAPPLE) return { skip: true, note: '未实现（B3 阶段实现后本项自动转为阻塞项）' };

  A.resetMatch();
  const isGrap = s => typeof s === 'string' && s.indexOf('GRAPPLE') >= 0;
  A.yy.state = A.ST.UW; A.yy.uwPose = 'H'; A.yy.dir = 1;
  A.yy.axFp = 110 * 256; A.yy.ayFp = 140 * 256;
  A.dad.state = A.ST.UW; A.dad.uwPose = 'H'; A.dad.dir = -1;
  A.dad.axFp = 130 * 256; A.dad.ayFp = 140 * 256;

  const iids = new Set();
  const kinds = new Set();
  let bothIn = false, hp0 = A.dad.hpFp, dmg = 0;

  // 阶段一：朝对手游过去，应自动进入肩组
  A.Input.R = 1;
  for (let i = 0; i < 180 && !bothIn; i++) {
    A.tick();
    const it = A.interaction();
    if (it) { iids.add(it.id); kinds.add(it.kind); }
    if (isGrap(A.yy.state) && isGrap(A.dad.state)) bothIn = true;
  }
  A.Input.R = 0;

  // 阶段二：肩组中按 B 出拳，应扣血
  for (let i = 0; i < 90; i++) {
    if (i % 30 === 0) { A.Input.B = 1; A.Input.pB = 1; } else { A.Input.B = 0; A.Input.pB = 0; }
    A.tick();
    const it = A.interaction();
    if (it) { iids.add(it.id); kinds.add(it.kind); }
  }
  dmg = (hp0 - A.dad.hpFp) / 256;

  // 阶段三：松开全部输入，必须能解开。解不开就是永久锁死。
  A.Input.B = 0; A.Input.pB = 0; A.Input.R = 0;
  let freed = false;
  for (let i = 0; i < 900 && !freed; i++) {
    A.tick();
    if (!isGrap(A.yy.state) && !isGrap(A.dad.state)) freed = true;
  }

  const ok = bothIn && dmg > 0 && freed && iids.size >= 1 && kinds.has('GRAPPLE');
  return {
    ok,
    note: `双方同时进入=${bothIn} 出拳扣血=${dmg} 能解开=${freed}` +
          `${freed ? '' : ' ← 永久锁死'} 交互对象数=${iids.size} kind=${[...kinds].join(',') || '无'}`,
  };
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

  const checks = [['内置自检', checkSelftest], ['踢击命中', checkKick], ['肩组', checkGrapple]];
  for (const [name, fn] of checks) {
    let r;
    try { r = fn(file); } catch (e) { r = { ok: false, note: '抛异常：' + e.message }; }
    if (r.skip) { console.log(`  跳过  ${name}：${r.note}`); continue; }
    console.log(`  ${r.ok ? '通过' : '阻塞'}  ${name}：${r.note}`);
    if (!r.ok) failed++;
  }

  for (const [name, fn] of [['判定盒镜像', obsMirror], ['判定盒覆盖率', obsCoverage]]) {
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
