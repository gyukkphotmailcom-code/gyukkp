#!/usr/bin/env node
/* ============================================================================
   复现脚本 —— 肩组双方同时被判为 attacker
   ----------------------------------------------------------------------------
   用法：node 过程文件/Claude重启规划/repro_肩组双attacker.js

   现象：两人同时朝对方游动而接触时，肩组建立为 aRole=attacker / bRole=attacker，
        没有 defender。后果：
          1. 双方都能出拳（decide() 的 startPunch 门是 role==='attacker'）
          2. 没有 defender → resolvePair 里 defD=null → escapeFp 永不累积
             → 附录 A-1 那套"被抓方连打挣脱"完全不会触发
          3. 结果是互相刷血的连打竞速；双方速度相同时 3 秒双双阵亡、判 draw

   根因：主 HTML 第 1430 行
        aRole: towA ? 'attacker' : 'defender', bRole: towB ? 'attacker' : 'defender'
        towA 与 towB 同时为真时，两边都拿到 attacker。

   为什么 verify.js 没抓到：它的肩组用例只驱动单侧按 B（等价本脚本场景 B），
        那条路径行为完全正确。对称进入这条路径从未被覆盖。
   ========================================================================== */

const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..', '..');

function load(file) {
  const html = fs.readFileSync(path.join(REPO, file), 'utf8');
  const m = html.match(/<script>([\s\S]*)<\/script>/);
  const ctx = { fillStyle: '', imageSmoothingEnabled: false,
                fillRect() {}, drawImage() {}, clearRect() {} };
  const canvas = { width: 256, height: 224, style: {}, getContext: () => ctx };
  global.document = { getElementById: () => canvas, createElement: () => canvas,
                      title: '', body: { appendChild() {}, innerHTML: '' }, addEventListener() {} };
  global.window = { innerWidth: 1024, innerHeight: 900, addEventListener() {} };
  global.addEventListener = () => {};
  global.requestAnimationFrame = () => {};
  global.location = { search: '' };
  global.URLSearchParams = URLSearchParams;
  new Function(m[1] + `;globalThis.__api={yy,dad,MATCH,tick,ST,Input,InputSources,
    T:ORIGINAL_TUNING, interaction:()=>(typeof interaction!=='undefined'?interaction:null)};`)();
  return globalThis.__api;
}

function run(label, mashYY, mashDD) {
  const a = load('阳阳水泳大乱斗-原版复刻.html');
  const { yy, dad, MATCH, tick, ST, Input, InputSources } = a;

  const blank = () => ({ L:0, R:0, U:0, D:0, A:0, B:0, pA:0, pB:0 });
  const dInp = blank();
  InputSources.BOT = () => dInp;
  dad.input = 'BOT';

  const clear = o => { for (const k in o) o[k] = 0; };

  // 水下互相靠近（这就是"两人同时朝对方游"的自然情形）
  function approach(self, foe, inp) {
    clear(inp);
    if (self.state === ST.SURF || self.state === ST.BREATH || self.state === ST.DIVE) { inp.D = 1; return; }
    if (self.state !== ST.UW) return;
    const dx = foe.axFp - self.axFp, dy = foe.ayFp - self.ayFp;
    if (Math.abs(dx) > 256) { dx > 0 ? inp.R = 1 : inp.L = 1; }
    if (Math.abs(dy) > 256 && foe.state === ST.UW) { dy > 0 ? inp.D = 1 : inp.U = 1; }
  }
  const mash = (self, inp, rate) => { clear(inp); if (rate > 0 && self.t % rate === 0) { inp.B = 1; inp.pB = 1; } };

  let firstGrapple = null, hits = { yy: 0, dd: 0 };
  let lastA = yy.hpFp, lastB = dad.hpFp;

  for (let t = 0; t < 10800 && MATCH.phase === 'FIGHT'; t++) {
    const I = a.interaction();
    if (I && I.kind === 'GRAPPLE') { mash(yy, Input, mashYY); mash(dad, dInp, mashDD); }
    else { approach(yy, dad, Input); approach(dad, yy, dInp); }
    if (I && !firstGrapple) firstGrapple = { t, aId: I.aId, aRole: I.aRole, bId: I.bId, bRole: I.bRole };
    tick();
    if (yy.hpFp !== lastA) { hits.yy++; lastA = yy.hpFp; }
    if (dad.hpFp !== lastB) { hits.dd++; lastB = dad.hpFp; }
  }

  console.log(`\n【${label}】`);
  if (firstGrapple) {
    const bad = firstGrapple.aRole === firstGrapple.bRole;
    console.log(`  肩组建立 t=${firstGrapple.t}  ` +
                `${firstGrapple.aId}=${firstGrapple.aRole} / ${firstGrapple.bId}=${firstGrapple.bRole}` +
                (bad ? '   ← 两边同角色，没有 defender' : ''));
  } else {
    console.log('  未进入肩组');
  }
  console.log(`  受击次数：阳阳 ${hits.yy}  爸爸 ${hits.dd}`);
  console.log(`  终局：phase=${MATCH.phase} winner=${MATCH.winner} ` +
              `剩余 ${Math.ceil(MATCH.ticksLeft / 60)}s  ` +
              `yy.hp=${yy.hpFp} dad.hp=${dad.hpFp}`);
}

console.log('肩组角色分配复现');
console.log('='.repeat(60));
run('场景 A：肩组中双方都不按键（应：超时解开，零伤害）', 0, 0);
run('场景 B：只有阳阳连打（verify.js 覆盖的路径，行为正确）', 10, 0);
run('场景 C：双方同速连打（应：一方挣脱或一方赢；实际：双双阵亡）', 10, 10);
console.log('\n' + '='.repeat(60));
console.log('期望：场景 C 中恰好一人是 attacker、另一人是 defender，');
console.log('      defender 的连打累积 escapeFp 并能脱身，不应出现双双阵亡。');
