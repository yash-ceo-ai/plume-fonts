// Writes study/compare-slider.html: the same Renown screen twice, today's font (Geist) on the left and Plume on the right,
// with a draggable divider. Plume Icons are read from the sibling repo (../plume-icons/dist/svg) when it is built.
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';

const root = new URL('..', import.meta.url).pathname;
const iconDir = `${root}../plume-icons/dist/svg`;
const icon = (name, v = 'line', size = 18) => {
  const f = `${iconDir}/${v}/${name}.svg`;
  if (!existsSync(f)) return '';
  const id = `i${Math.random().toString(36).slice(2, 7)}`;
  return readFileSync(f, 'utf8').trim()
    .replace(/id="(plume-[^"]+)"/g, `id="${id}$1"`).replace(/url\(#(plume-[^)]+)\)/g, `url(#${id}$1)`)
    .replace('<svg ', `<svg width="${size}" height="${size}" `);
};

const screen = () => `
<div class="ui">
  <aside>
    <div class="nav on">${icon('dashboard', 'fill')}Overview</div>
    <div class="nav">${icon('chats')}Prompts</div>
    <div class="nav">${icon('brand')}Brand</div>
    <div class="nav">${icon('search')}Search</div>
    <div class="nav">${icon('radar')}Site checks</div>
    <div class="nav">${icon('list-checks')}To-do</div>
    <div class="nav">${icon('bot')}Otto</div>
    <div class="nav">${icon('gear')}Settings</div>
  </aside>
  <main>
    <div class="top"><h3>AI visibility</h3><span class="chip">Last 7 days</span></div>
    <div class="kpis">
      <div><small>Mentions this week</small><b>12,480</b><em>+8.2%</em></div>
      <div><small>Share of voice</small><b>38.5%</b><em class="r">−1.4%</em></div>
      <div><small>Prompts tracked</small><b>1,204</b><em>+24</em></div>
    </div>
    <table>
      <tr><th>Prompt</th><th>Mentions</th><th>Share</th></tr>
      <tr><td>best crm for startups</td><td>1,204</td><td>38.5%</td></tr>
      <tr><td>crm pricing comparison</td><td>987</td><td>12.1%</td></tr>
      <tr><td>how to pick a crm</td><td>76</td><td>101.0%</td></tr>
      <tr><td>renown.ai/pricing</td><td>8</td><td>0.4%</td></tr>
    </table>
    <p>Renown watches how AI answers talk about your brand and tells you what to fix first. 14px body, 20px line. Țări și județe: ă â î ș ț. Επισκόπηση προτροπών και αναφορών της μάρκας σας.</p>
    <div class="btns"><button class="pri">${icon('play', 'fill', 16)}Run scan</button><button>${icon('download', 'line', 16)}Export</button><button>${icon('filter', 'line', 16)}Filter</button></div>
    <div class="big">Rag 147 <span>Renown AI</span></div>
  </main>
</div>`;

const html = `<!doctype html><html data-t="dark" lang="en"><meta charset="utf-8"><title>Today's font vs Plume</title>
<style>
@font-face{font-family:'Plume';src:url('../fonts/Plume-Regular.woff2') format('woff2');font-weight:400}
@font-face{font-family:'Plume';src:url('../fonts/Plume-Medium.woff2') format('woff2');font-weight:500}
@font-face{font-family:'Plume';src:url('../fonts/Plume-SemiBold.woff2') format('woff2');font-weight:600}
@font-face{font-family:'Geist Today';src:url('../node_modules/@fontsource-variable/geist/files/geist-latin-wght-normal.woff2') format('woff2');font-weight:100 900;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:'Geist Today';src:url('../node_modules/@fontsource-variable/geist/files/geist-latin-ext-wght-normal.woff2') format('woff2');font-weight:100 900;unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
:root{--bg:#121110;--panel:#171615;--raised:#232221;--line:#2a2927;--text:#ecebe9;--t2:#aaa8a5;--muted:#898784;--on:#121110;--zoom:1}
[data-t=light]{--bg:#f3f2f0;--panel:#fff;--raised:#efeeec;--line:#e4e3e0;--text:#121110;--t2:#31302e;--muted:#676563;--on:#f3f2f0}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/20px system-ui,sans-serif}
.bar{display:flex;gap:12px;align-items:center;padding:10px 24px;background:var(--panel);border-bottom:1px solid var(--line)}
.bar b{margin-right:auto;font-weight:600}.bar button,.bar select{height:28px;padding:0 12px;border-radius:8px;border:1px solid var(--line);background:var(--raised);color:var(--text);cursor:pointer;font:inherit}
.wrap{max-width:1180px;margin:20px auto;padding:0 24px}
.cmp{position:relative;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--panel);user-select:none;touch-action:none;cursor:ew-resize}
.layer{padding:52px 20px 20px;zoom:var(--zoom)}
.layer.today{font-family:'Geist Today',system-ui,sans-serif}
.layer.plume{font-family:'Plume',system-ui,sans-serif;position:absolute;inset:0;background:var(--panel);clip-path:inset(0 0 0 var(--x,50%))}
.tag{position:absolute;top:12px;z-index:3;padding:4px 10px;border-radius:8px;background:var(--text);color:var(--on);font:600 12px system-ui}
.tag.l{left:12px}.tag.r{right:12px}
.handle{position:absolute;top:0;bottom:0;left:var(--x,50%);width:0;z-index:4;pointer-events:none}
.handle::before{content:'';position:absolute;top:0;bottom:0;left:-1px;width:2px;background:var(--text)}
.handle i{position:absolute;top:50%;left:-20px;width:40px;height:40px;margin-top:-20px;border-radius:50%;background:var(--text);color:var(--on);display:grid;place-items:center;font:600 16px system-ui;font-style:normal;box-shadow:0 2px 10px #0006}
.cmp input{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:ew-resize;z-index:5;margin:0}
.ui{display:grid;grid-template-columns:150px 1fr;gap:16px;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px}
.nav{display:flex;align-items:center;gap:10px;height:32px;padding:0 8px;border-radius:8px;color:var(--muted)}.nav.on{background:var(--raised);color:var(--text);font-weight:500}
.nav svg,button svg{flex:none}.top{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}h3{margin:0;font-size:24px;line-height:28px;font-weight:500}
.chip{border:1px solid var(--line);border-radius:8px;padding:2px 10px;color:var(--t2);font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}.kpis div{border:1px solid var(--line);border-radius:10px;padding:10px 12px;display:flex;flex-direction:column;background:var(--panel)}
.kpis small{color:var(--muted);font-size:13px}.kpis b{font-size:28px;line-height:34px;font-weight:500;font-variant-numeric:tabular-nums}.kpis em{font-style:normal;color:#35a06c;font-size:13px}.kpis em.r{color:#e5484d}
table{width:100%;border-collapse:collapse;margin-bottom:10px;font-variant-numeric:tabular-nums}th{text-align:left;font-weight:500;color:var(--muted);font-size:13px}th+th,td+td{text-align:right}td,th{padding:6px 0;border-bottom:1px solid var(--line)}
p{margin:6px 0;color:var(--t2)}.btns{display:flex;gap:8px;margin-top:10px}
button.b,.btns button{display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 12px;border-radius:8px;border:1px solid var(--line);background:var(--raised);color:var(--text);font:inherit;font-weight:500;font-size:13px}
.btns button.pri{background:var(--text);color:var(--on);border-color:transparent;height:40px;padding:0 16px;font-size:14px}
.big{margin-top:16px;font-size:64px;line-height:68px;font-weight:600;letter-spacing:-.02em}.big span{font-weight:400;color:var(--t2);font-size:36px}
.hint{color:var(--muted);text-align:center;margin:12px 0 0;font-size:13px}
</style>
<div class="bar"><b>Today's font (Geist) vs Plume</b>
  <select id="zoom" aria-label="Zoom"><option value="1">100%</option><option value="1.5">150%</option><option value="2">200%</option></select>
  <button onclick="document.documentElement.dataset.t=document.documentElement.dataset.t==='dark'?'light':'dark'">Theme</button></div>
<div class="wrap">
  <div class="cmp" id="cmp">
    <div class="layer today" id="today">${screen()}</div>
    <div class="layer plume" id="plume">${screen()}</div>
    <span class="tag l">Today: Geist</span><span class="tag r">New: Plume</span>
    <div class="handle"><i>↔</i></div>
    <input type="range" min="0" max="100" value="50" step="0.1" aria-label="Compare today's font and Plume" id="rng">
  </div>
  <p class="hint">Drag anywhere, or use the arrow keys. The left side is the font the app shows today; the right side is Plume. Same text, same icons, same sizes.</p>
</div>
<script>
const cmp = document.getElementById('cmp'), rng = document.getElementById('rng');
const set = (v) => cmp.style.setProperty('--x', v + '%');
rng.addEventListener('input', () => set(rng.value)); set(rng.value);
document.getElementById('zoom').onchange = (e) => document.documentElement.style.setProperty('--zoom', e.target.value);
new ResizeObserver(() => { document.getElementById('plume').style.height = document.getElementById('today').offsetHeight + 'px'; }).observe(document.getElementById('today'));
</script></html>`;
mkdirSync(`${root}study`, { recursive: true });
writeFileSync(`${root}study/compare-slider.html`, html);
console.log('study/compare-slider.html');
