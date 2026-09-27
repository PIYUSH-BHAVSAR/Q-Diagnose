#!/usr/bin/env node
/* Responsive audit — optional, needs a real browser. Setup (dev-only, not in `npm run check`):
     npm i -D playwright && npx playwright install chromium
     npm run dev                # or: npm run build && npm run preview
     npm run test:responsive    # audits 14 sizes × 8 routes against http://localhost:5173
   It fails (exit 1) on: horizontal page overflow, any element painting outside the viewport,
   clipped text without an ellipsis, tap targets under 28px on touch contexts, text under 11px,
   and flex children that paint on top of each other (the failure mode plain overflow checks miss).
   Measures every screen size × every route, in the real browser.
   Reports horizontal overflow (with the offending element), clipped text (no ellipsis),
   tiny tap targets, sub-11px text, and horizontal scroll containers that hide content. */
import { createRequire } from 'module';
// require(), not import(), so NODE_PATH and a hoisted install in the workspace root both resolve
let chromium = null;
for (const spec of ['playwright', 'playwright-core']) {
  try { chromium = createRequire(import.meta.url)(spec).chromium; break; } catch { /* not installed */ }
}
if (!chromium) {
  console.log('SKIP  responsive audit — install it once with: npm i -D playwright && npx playwright install chromium');
  process.exit(0);
}
import fs from 'fs';

const BASE = process.env.AUDIT_BASE || 'http://localhost:5173';
const OUT = process.env.AUDIT_OUT || '.audit-responsive';
fs.mkdirSync(OUT, { recursive: true });

const SIZES = [
  ['320-galaxy-fold', 320, 700],
  ['360-android', 360, 800],
  ['390-iphone14', 390, 844],
  ['430-iphone15pm', 430, 932],
  ['768-ipad-portrait', 768, 1024],
  ['834-ipad-landscape', 834, 1112],
  ['1024-ipad-pro', 1024, 1366],
  ['1280-laptop', 1280, 800],
  ['1440-common', 1440, 900],
  ['1920-fullhd', 1920, 1080],
  ['2560-quadhd', 2560, 1440]
];

// touch devices get the coarse-pointer rules — same widths, different input
const TOUCH_SIZES = [
  ['768-ipad-touch', 768, 1024],
  ['1024-ipad-pro-touch', 1024, 1366],
  ['1180-surface-touch', 1180, 800]
];

const ROUTES = [
  ['dashboard', '/'],
  ['datasets', '/datasets'],
  ['dataset-detail', '/datasets/DS-392805F2'],
  ['experiment-new', '/experiments/new'],
  ['experiment-running', '/experiments/EXP-DEMO-0003'],
  ['experiment-results', '/experiments/EXP-DEMO-0001'],
  ['experiments', '/experiments'],
  ['reports', '/reports']
];

const PROBE = () => {
  const vw = window.innerWidth;
  const esc = (el) => {
    const cls = (el.className && typeof el.className === 'string') ? '.' + el.className.trim().split(/\s+/).slice(0, 3).join('.') : '';
    const parent = el.parentElement ? el.parentElement.tagName.toLowerCase() : '';
    return `${el.tagName.toLowerCase()}${cls}`.slice(0, 70) + (parent ? `  (in ${parent})` : '');
  };
  const inScroller = (el) => {
    for (let n = el; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (/auto|scroll/.test(cs.overflowX)) return true;
    }
    return false;
  };
  const clipped = [];
  const overflowing = [];
  const tiny = [];
  const smallText = [];
  const els = [...document.querySelectorAll('body *')];

  for (const el of els) {
    const r = el.getBoundingClientRect();
    if (!r.width && !r.height) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || cs.opacity === '0') continue;

    // 1. paints outside the viewport (and is not inside an intentional scroller)
    // a visually-hidden element (skip links park at left:-9999px until focused) is not overflow
    const parkedOffscreen = cs.position === 'absolute' && r.left <= -100;
    if (r.right > vw + 1.5 && !inScroller(el) && !parkedOffscreen) {
      overflowing.push({ what: esc(el), right: Math.round(r.right), w: Math.round(r.width) });
    }
    // 2. text cut off with no ellipsis
    if (r.width > 8 && el.scrollWidth > el.clientWidth + 2 && !inScroller(el)) {
      const noEllipsis = !/ellipsis|clip/.test(cs.textOverflow) && cs.whiteSpace !== 'nowrap';
      if (noEllipsis && el.children.length === 0 && el.textContent.trim().length > 2) {
        clipped.push({ what: esc(el), cut: el.scrollWidth - el.clientWidth, text: el.textContent.trim().slice(0, 40) });
      }
    }
    // 3. tap targets
    if (/^(A|BUTTON|SELECT|INPUT)$/.test(el.tagName) && !el.disabled && cs.position !== 'fixed') {
      // a wrapping flex row can be 152px tall and 20px wide — that is not a tiny target.
      // flag controls only when the tappable box itself is small.
      if (r.height < 28 || (r.width < 28 && r.height < 40)) {
        tiny.push({ what: esc(el), h: Math.round(r.height), w: Math.round(r.width), label: (el.getAttribute('aria-label') || el.textContent || el.placeholder || '').trim().slice(0, 26) });
      }
    }
    // 4. text too small to read
    const fsz = parseFloat(cs.fontSize);
    if (fsz && fsz < 11 && el.textContent.trim().length > 3 && el.children.length === 0) {
      smallText.push({ what: esc(el), px: fsz, text: el.textContent.trim().slice(0, 30) });
    }
  }

  // horizontal page scroll is the headline failure
  const doc = document.documentElement;
  const pageOverflowPx = doc.scrollWidth - vw;

  // 5. scrollers that swallow a whole section (table wider than its box, no fade hint)
  const scrollers = [...document.querySelectorAll('*')].filter((n) => {
    const cs = getComputedStyle(n);
    return /auto|scroll/.test(cs.overflowX) && n.scrollWidth > n.clientWidth + 4 && n.clientWidth > 0;
  }).map((n) => ({ what: esc(n), hiddenPx: n.scrollWidth - n.clientWidth, label: (n.querySelector('h3,caption,th')?.textContent || '').trim().slice(0, 28) }));

    // 5b. horizontal overlap: two flex children painting on top of each other
    const overlaps = [];
    for (const box of document.querySelectorAll('.topbar, .card-hd, .page-head, .list > li, .row, .tabs')) {
      const kids = [...box.children].map((el) => ({ el, r: el.getBoundingClientRect() })).filter((k) => k.r.width > 4 && k.r.height > 4);
      for (let i = 0; i < kids.length; i++) {
        for (let j = i + 1; j < kids.length; j++) {
          const a = kids[i].r, b = kids[j].r;
          const ix = Math.min(a.right, b.right) - Math.max(a.left, b.left);
          const iy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
          if (ix > 6 && iy > 6) {
            overlaps.push({ box: esc(box), a: esc(kids[i].el), b: esc(kids[j].el), px: Math.round(ix) });
          }
        }
      }
    }

  // 6. elements wider than the viewport at all (root cause list)
  const widest = [...document.querySelectorAll('table,.card,.grid,.hero,.qgrid')]
    .map((el) => ({ what: esc(el), w: Math.round(el.getBoundingClientRect().width) }))
    .filter((x) => x.w > vw + 1.5)
    .sort((a, b) => b.w - a.w)
    .slice(0, 3);

  return {
    vw,
    pageOverflowPx,
    overflowing: overflowing.slice(0, 6),
    clipped: clipped.slice(0, 6),
    tiny: tiny.slice(0, 8),
    tinyCount: tiny.length,
    smallText: smallText.slice(0, 4),
    scrollers: scrollers.slice(0, 4),
    overlaps: overlaps.slice(0, 6),
    widest
  };
};

(async () => {
  let browser;
  try { browser = await chromium.launch({ args: ['--no-sandbox', '--disable-dev-shm-usage'] }); }
  catch (e) { console.log('SKIP  no browser available here —', String(e).split('\n')[0]); process.exit(0); }
  const report = [];

  const ALL = [...SIZES.map((x) => [...x, false]), ...TOUCH_SIZES.map((x) => [...x, true])];
  for (const [sizeName, w, h, touch] of ALL) {
    const ctx = await browser.newContext({
      viewport: { width: w, height: h }, deviceScaleFactor: w < 500 ? 2 : 1,
      hasTouch: touch, isMobile: touch
    });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e).slice(0, 120)));
    for (const [routeName, path] of ROUTES) {
      await page.goto(BASE + path, { waitUntil: 'load', timeout: 45000 });
      await page.waitForTimeout(w < 500 ? 1100 : 900);
      const res = await page.evaluate(PROBE);
      report.push({ size: sizeName, route: routeName, touch, ...res, pageErrors: errs });
      if (w === SIZES[2][1] || w === SIZES[4][1]) {   // phone + tablet: keep evidence shots
        await page.screenshot({ path: `${OUT}/${sizeName}-${routeName}.jpg`, type: 'jpeg', quality: 85, fullPage: w < 500 });
      }
    }
    await ctx.close();
  }
  await browser.close();

  fs.mkdirSync(OUT, { recursive: true });
  fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 1));

  // A 22px chip under a mouse is normal (Linear does it); under a thumb it is a bug.
  // So tap-target size only counts against touch contexts.
  const tinyFor = (r) => (r.touch ? r.tinyCount : 0);
  const bad = (r) => r.pageOverflowPx > 1.5 || r.overflowing.length || r.clipped.length || tinyFor(r) || r.smallText.length || r.overlaps.length || r.pageErrors.length;
  console.log('\n================ RESPONSIVE AUDIT ================');
  let fails = 0;
  for (const r of report) {
    const flag = bad(r);
    if (flag) fails++;
    console.log(`${flag ? '✗' : '✓'} ${r.size.padEnd(20)} ${r.route.padEnd(20)} overflow=${r.pageOverflowPx}px  out=${r.overflowing.length} clip=${r.clipped.length} tiny=${tinyFor(r)} small=${r.smallText.length} overlap=${r.overlaps.length}${r.pageErrors.length ? ' ERRORS:' + r.pageErrors[0] : ''}`);
  }
  console.log(`\n${fails} of ${report.length} size×route combinations have at least one issue\n`);

  // top offenders, grouped
  const group = (key) => {
    const m = new Map();
    for (const r of report) for (const o of r[key]) {
      const k = o.what.replace(/^\w+/, (t) => t);
      m.set(k, (m.get(k) ?? 0) + 1);
    }
    return [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12);
  };
  console.log('── overlapping flex children ──');
  {
    const m = new Map();
    for (const r of report) for (const o of r.overlaps) {
      const k = `${o.box} → ${o.a} ✕ ${o.b}`;
      const e = m.get(k) ?? { n: 0, px: 0, sizes: new Set() };
      e.n++; e.px = Math.max(e.px, o.px); e.sizes.add(r.size); m.set(k, e);
    }
    for (const [k, v] of [...m.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, 12)) {
      console.log(`   ${String(v.n).padStart(3)}×  ${k}  (worst ${v.px}px; e.g. ${[...v.sizes].slice(0, 3).join(', ')})`);
    }
  }
  for (const key of ['overflowing', 'clipped', 'tiny', 'smallText']) {
    console.log(`── ${key} ──`);
    for (const [what, n] of group(key)) console.log(`   ${String(n).padStart(3)}×  ${what}`);
  }
  console.log('── horizontal scrollers (tables that need a swipe) ──');
  const sc = new Map();
  for (const r of report) for (const s of r.scrollers) sc.set(`${s.what}|${s.label}`, (sc.get(`${s.what}|${s.label}`) ?? 0) + 1);
  for (const [k, n] of [...sc.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10)) console.log(`   ${String(n).padStart(3)}×  ${k}`);
  process.exit(report.some(bad) ? 1 : 0);
})();
