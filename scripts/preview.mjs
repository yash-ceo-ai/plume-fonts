// Writes study/plume-sans.html: Plume Sans (alpha) next to Inter (its base) and next to Plume Icons, in the Renown UI.
// Plume Icons are read from the sibling repo (../plume-icons/dist/svg) when it is built; otherwise the icons are skipped.
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

const ui = (cls) => `
<div class="ui ${cls}">
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
    <h3>AI visibility</h3>
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
    <p>Renown watches how AI answers talk about your brand and tells you what to fix first. “Round quotes” and commas, 14px body, 20px line.</p>
    <p class="x">Επισκόπηση προτροπών και αναφορών της μάρκας σας. · Țări, județe și județul Cluj: ș ț ă î â. · Тест кириллицы.</p>
    <div class="btns"><button class="pri">${icon('play', 'fill', 16)}Run scan</button><button>${icon('download', 'line', 16)}Export</button><button>${icon('filter', 'line', 16)}Filter</button></div>
  </main>
</div>`;

const glyphs = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789 &@#%$€£ ?!.,;:“”‘’ ()[]{}<>/\\| +−=×÷ ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ αβγδεζηθικλμνξοπρστυφχψω ĂÂÎȘȚ ăâîșț АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ';

const html = `<!doctype html><html data-t="dark" lang="en"><meta charset="utf-8"><title>Plume Sans (alpha)</title>
<style>
@font-face{font-family:'Plume Sans';src:url('../fonts/PlumeSans-Regular.woff2') format('woff2');font-weight:400}
@font-face{font-family:'Plume Sans';src:url('../fonts/PlumeSans-Medium.woff2') format('woff2');font-weight:500}
@font-face{font-family:'Plume Sans';src:url('../fonts/PlumeSans-SemiBold.woff2') format('woff2');font-weight:600}
@font-face{font-family:'Inter Base';src:url('../node_modules/inter-ui/variable/InterVariable.woff2') format('woff2');font-weight:100 900}
:root{--bg:#121110;--panel:#171615;--raised:#232221;--line:#2a2927;--text:#ecebe9;--t2:#aaa8a5;--muted:#898784;--on:#121110}
[data-t=light]{--bg:#f3f2f0;--panel:#fff;--raised:#efeeec;--line:#e4e3e0;--text:#121110;--t2:#31302e;--muted:#676563;--on:#f3f2f0}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/20px system-ui}
.bar{position:sticky;top:0;z-index:2;display:flex;gap:12px;align-items:center;padding:10px 24px;background:var(--panel);border-bottom:1px solid var(--line)}
.bar b{margin-right:auto;font-weight:600}.bar button{height:28px;padding:0 12px;border-radius:8px;border:1px solid var(--line);background:var(--raised);color:var(--text);cursor:pointer}
.wrap{max-width:1280px;margin:0 auto;padding:24px;display:grid;gap:24px}
.sec h2{font:600 13px system-ui;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin:0 0 12px}
.cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}@media(max-width:900px){.cols{grid-template-columns:minmax(0,1fr)}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px}.card h4{margin:0 0 10px;font:500 12px system-ui;color:var(--muted)}
.plume{font-family:'Plume Sans',sans-serif}.inter{font-family:'Inter Base',sans-serif}
.hero{font-size:120px;line-height:120px;font-weight:600;letter-spacing:-.03em;margin:0;color:var(--text)}.h2{font-size:44px;line-height:52px;font-weight:500;letter-spacing:-.02em;margin:8px 0;color:var(--text)}
.ramp div{display:flex;gap:16px;align-items:baseline;white-space:nowrap;overflow:hidden;line-height:1.3;padding:6px 0;border-bottom:1px solid var(--line);color:var(--t2)}.ramp span{flex:none;width:64px;font:12px system-ui;color:var(--muted)}
.ramp .w4{font-weight:400}.ramp .w5{font-weight:500}.ramp .w6{font-weight:600}
.g{font-size:26px;line-height:38px;word-break:break-all;color:var(--text)}.g.s{font-size:15px;line-height:24px;color:var(--t2)}
.ui{display:grid;grid-template-columns:150px 1fr;gap:16px;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px}
.nav{display:flex;align-items:center;gap:10px;height:32px;padding:0 8px;border-radius:8px;color:var(--muted)}.nav.on{background:var(--raised);color:var(--text);font-weight:500}
.nav svg,button svg{flex:none}h3{margin:0 0 10px;font-size:24px;line-height:28px;font-weight:500;letter-spacing:-.01em}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}.kpis div{border:1px solid var(--line);border-radius:10px;padding:10px 12px;display:flex;flex-direction:column;background:var(--panel)}
.kpis small{color:var(--muted);font-size:13px}.kpis b{font-size:28px;line-height:34px;font-weight:500;font-variant-numeric:tabular-nums}.kpis em{font-style:normal;color:#35a06c;font-size:13px}.kpis em.r{color:#e5484d}
table{width:100%;border-collapse:collapse;margin-bottom:10px;font-variant-numeric:tabular-nums}th{text-align:left;font-weight:500;color:var(--muted);font-size:13px}th+th,td+td{text-align:right}td,th{padding:6px 0;border-bottom:1px solid var(--line)}
p{margin:6px 0;color:var(--t2)}p.x{font-size:13px}
.btns{display:flex;gap:8px;margin-top:10px}button{display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 12px;border-radius:8px;border:1px solid var(--line);background:var(--raised);color:var(--text);font:inherit;font-weight:500;font-size:13px}
button.pri{background:var(--text);color:var(--on);border-color:transparent;height:40px;padding:0 16px;font-size:14px}
</style>
<div class="bar"><b>Plume Sans · alpha ${'0.1.0'} · Inter base, corners softened to match Plume Icons</b><button onclick="document.documentElement.dataset.t=document.documentElement.dataset.t==='dark'?'light':'dark'">Theme</button></div>
<div class="wrap">
  <div class="sec"><h2>Plume Sans next to its base, Inter</h2><div class="cols">
    <div class="card plume"><h4>Plume Sans</h4><p class="hero">Rag 147</p><p class="h2">Renown AI visibility, “quotes”, 12,480</p></div>
    <div class="card inter"><h4>Inter (original)</h4><p class="hero">Rag 147</p><p class="h2">Renown AI visibility, “quotes”, 12,480</p></div>
  </div></div>
  <div class="sec"><h2>In the Renown UI, with Plume Icons</h2><div class="cols">
    <div class="card"><h4>Plume Sans + Plume Icons</h4>${ui('plume')}</div>
    <div class="card"><h4>Inter + Plume Icons</h4>${ui('inter')}</div>
  </div></div>
  <div class="sec"><h2>Weights and sizes</h2><div class="card plume ramp">
    ${[12, 13, 14, 16, 20, 24, 32].map((s) => `<div style="font-size:${s}px"><span>${s}px</span><i class="w4" style="font-style:normal">Regular 400 · Renown watches how AI talks about you</i><i class="w5" style="font-style:normal">Medium 500</i><i class="w6" style="font-style:normal">SemiBold 600</i></div>`).join('')}
  </div></div>
  <div class="sec"><h2>Characters (Latin, Romanian, Greek, Cyrillic)</h2><div class="cols">
    <div class="card plume"><h4>Plume Sans</h4><div class="g">${glyphs}</div></div>
    <div class="card inter"><h4>Inter</h4><div class="g">${glyphs}</div></div>
  </div></div>
</div></html>`;
mkdirSync(`${root}study`, { recursive: true });
writeFileSync(`${root}study/plume-sans.html`, html);
console.log('study/plume-sans.html');
