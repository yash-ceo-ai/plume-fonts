// Task 1 demo: the app's real UI text in each OFL candidate, side by side, dark and light.
// Writes study/compare.html (OFL fonts only, committed) and, if Klim's trial files exist on this machine,
// .local/compare-with-sohne.html (not committed: the trial licence allows trying them in design work only).
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';

const root = new URL('..', import.meta.url).pathname;
const FS = 'node_modules/@fontsource-variable';
const fonts = [
  { id: 'geist', name: 'Geist', family: 'Geist Variable', greek: false },
  { id: 'inter', name: 'Inter', family: 'Inter Variable', greek: true },
  { id: 'hanken-grotesk', name: 'Hanken Grotesk', family: 'Hanken Grotesk Variable', greek: false },
  { id: 'instrument-sans', name: 'Instrument Sans', family: 'Instrument Sans Variable', greek: false },
  { id: 'figtree', name: 'Figtree', family: 'Figtree Variable', greek: false },
  { id: 'schibsted-grotesk', name: 'Schibsted Grotesk', family: 'Schibsted Grotesk Variable', greek: false },
];
const TRIAL = '/Users/yash/Projects/_trial-fonts/sohne-font-family';
const hasTrial = existsSync(`${TRIAL}/TestSohne-Buch-BF663d89cd32e6a.otf`);

const panel = (f) => `
<section class="p" style="font-family:'${f.family}'${f.sohne ? ',sans-serif' : ", 'Geist Variable', sans-serif"}">
  <h2>${f.name}${f.greek === false ? ' <i>no Greek</i>' : ''}${f.sohne ? ' <i>trial, local only</i>' : ''}</h2>
  <div class="big">Aa Gg Rr 1 4 7 &amp;</div>
  <div class="abc">Hamburgefonstiv 0123456789<br>abcdefghijklmnopqrstuvwxyz</div>
  <div class="ui">
    <div class="side"><b>Overview</b><span>Prompts</span><span>Brand</span><span>Search</span><span>Site checks</span><span>Settings</span></div>
    <div class="main">
      <h3>AI visibility</h3>
      <div class="kpi"><small>Mentions this week</small><strong>12,480</strong><em>+8.2%</em></div>
      <table>
        <tr><td>best crm for startups</td><td>1,204</td><td>38.5%</td></tr>
        <tr><td>crm pricing comparison</td><td>987</td><td>12.1%</td></tr>
        <tr><td>how to pick a crm</td><td>76</td><td>101.0%</td></tr>
      </table>
      <p>Renown watches how AI answers talk about your brand and tells you what to fix first. 14px body, 20px line.</p>
      <p class="el">Επισκόπηση προτροπών και αναφορών της μάρκας σας.</p>
      <p class="ro">Țări, județe și județul Cluj: ș ț ă î â.</p>
      <button>Run scan</button>
    </div>
  </div>
</section>`;

function page(list, title) {
  const links = fonts.map((f) => `<link rel="stylesheet" href="../${FS}/${f.id}/index.css">`).join('\n');
  const sohne = list.some((f) => f.sohne)
    ? `<style>@font-face{font-family:'Sohne Trial';src:url('${TRIAL}/TestSohne-Buch-BF663d89cd32e6a.otf');font-weight:400}@font-face{font-family:'Sohne Trial';src:url('${TRIAL}/TestSohne-Kraftig-BF663d89cd37e26.otf');font-weight:500}@font-face{font-family:'Sohne Trial';src:url('${TRIAL}/TestSohne-Halbfett-BF663d89cd2d67b.otf');font-weight:600}</style>`
    : '';
  return `<!doctype html><html data-t="dark"><meta charset="utf-8"><title>${title}</title>
${links}${sohne}
<style>
:root{--bg:#121110;--panel:#171615;--raised:#232221;--line:#232221;--text:#ecebe9;--text2:#aaa8a5;--muted:#898784}
[data-t=light]{--bg:#f3f2f0;--panel:#fff;--raised:#efeeec;--line:#e4e3e0;--text:#121110;--text2:#31302e;--muted:#676563}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/20px system-ui}
.bar{position:sticky;top:0;padding:10px 20px;background:var(--panel);border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center;font-family:system-ui}
.bar button{height:28px;padding:0 12px;border-radius:8px;border:1px solid var(--line);background:var(--raised);color:var(--text);cursor:pointer}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(520px,1fr));gap:16px;padding:20px}
.p{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px}
h2{font-size:14px;font-weight:500;margin:0 0 12px;color:var(--text2)}h2 i{font-style:normal;color:#e5484d;font-size:12px;margin-left:8px}
.big{font-size:56px;line-height:60px;font-weight:500;letter-spacing:-.02em}.abc{font-size:18px;line-height:26px;color:var(--text2);margin:8px 0 16px;word-break:break-all}
.ui{display:grid;grid-template-columns:140px 1fr;gap:16px;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px}
.side{display:flex;flex-direction:column;gap:2px}.side span,.side b{padding:6px 8px;border-radius:8px;color:var(--muted)}.side b{background:var(--raised);color:var(--text);font-weight:500}
h3{margin:0 0 8px;font-size:24px;line-height:28px;font-weight:500;letter-spacing:-.01em}
.kpi{display:flex;flex-direction:column;margin-bottom:10px}.kpi small{color:var(--muted);font-size:13px}.kpi strong{font-size:28px;line-height:34px;font-weight:500}.kpi em{font-style:normal;color:#35a06c;font-size:13px}
table{width:100%;border-collapse:collapse;margin-bottom:10px}td{padding:6px 0;border-bottom:1px solid var(--line)}td+td{text-align:right}
p{margin:6px 0;color:var(--text2)}button.x,.main button{margin-top:6px;height:32px;padding:0 14px;border-radius:8px;border:0;background:var(--text);color:var(--bg);font:inherit;font-weight:500}
</style>
<div class="bar"><b>${title}</b><button onclick="document.documentElement.dataset.t=document.documentElement.dataset.t==='dark'?'light':'dark'">Theme</button></div>
<div class="g">${list.map(panel).join('')}</div></html>`;
}

mkdirSync(`${root}study`, { recursive: true });
writeFileSync(`${root}study/compare.html`, page(fonts, 'Plume Sans: OFL candidates in the Renown UI'));
console.log('study/compare.html');
if (hasTrial) {
  mkdirSync(`${root}.local`, { recursive: true });
  const withSohne = [{ id: 'sohne', name: 'Söhne (Klim trial)', family: 'Sohne Trial', sohne: true, greek: true }, ...fonts];
  writeFileSync(`${root}.local/compare-with-sohne.html`, page(withSohne, 'Candidates next to Söhne (local only)').replaceAll('../node_modules', '../node_modules'));
  console.log('.local/compare-with-sohne.html');
}
