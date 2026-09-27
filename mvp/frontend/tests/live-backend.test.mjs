// npm run test:live — adapter check against a RUNNING backend on :8000.
// Skips itself when the server is not up, so CI without a backend stays green.
import { readFileSync } from 'fs';
import { execSync } from 'child_process';
import {
  adaptDatasetList, adaptProfile, adaptValidation, adaptStatus, adaptResources, adaptError, adaptResults
} from '../src/lib/adapters.js';

const BASE = process.env.API_URL ?? 'http://localhost:8000';
const get = (p) => fetch(BASE + p).then(async (r) => ({ status: r.status, body: await r.json().catch(() => ({})) }));

let up = true;
try { await get('/api/health'); } catch { up = false; }
if (!up) {
  console.log('SKIP  live backend check — no server on ' + BASE + ' (start: cd mvp && python -m backend.main)');
  process.exit(0);
}

const results = await get('/api/datasets');
const list = adaptDatasetList(results.body);
const id = list.datasets[0].id;
const out = [];
const ok = (n, c, g) => { out.push([c, n, g]); };

ok('datasets listed', list.total >= 1, list.total);
ok('display name resolved', !!list.datasets[0].display, list.datasets[0]);
ok('featureCount = length of the columns array the API returned',
   list.datasets[0].featureCount === results.body.datasets[0].columns.length, list.datasets[0].featureCount);

const prof = await get(`/api/datasets/${id}/profile`);
const p = adaptProfile(prof.body);
ok('profile rows numeric', Number.isFinite(p.rows) && p.rows > 0, p.rows);
ok('profile columns[] → rows', p.columns.length > 0 && !!p.columns[0].name, p.columns.length);
ok('profile target resolved', typeof p.target === 'string' || p.target === null, p.target);

const val = await get(`/api/datasets/${id}/validate`);
if (val.status === 200) {
  const v = adaptValidation(val.body);
  ok('validation boolean-ish', typeof v.passed === 'boolean', v.passed);
  ok('qualityScore absent → null, not 0', v.qualityScore === null, v.qualityScore);
}

const created = await fetch(`${BASE}/api/experiments`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ dataset_id: id, name: 'adapter live check' })
}).then((r) => r.json());

if (created.experiment_id) {
  const expId = created.experiment_id;
  await fetch(`${BASE}/api/experiments/${expId}/run`, { method: 'POST' });
  await new Promise((r) => setTimeout(r, 2500));
  const st = adaptStatus((await get(`/api/experiments/${expId}/status`)).body);
  ok('status stage mapped into the 6 UI buckets',
     ['preprocessing', 'classical_training', 'quantum_training', 'benchmarking', 'explaining', 'completed'].includes(st.stage), st.stage);
  ok('status progress is a number in [0,1]', Number.isFinite(st.progress) && st.progress >= 0 && st.progress <= 1, st.progress);
  ok('status never throws on missing error_message', 'error' in st, st.error);
  const res = adaptResources((await get(`/api/experiments/${expId}/resources`)).body);
  ok('resources tolerate an empty object', typeof res === 'object', res);
  const bad = await get(`/api/experiments/${expId}/results`);
  if (bad.status !== 200) {
    const e = adaptError({ response: { status: bad.status, data: bad.body } });
    ok('a 400 becomes a human sentence, not [object Object]', typeof e.message === 'string' && e.message.length > 4, e.message);
  }
  const r2 = adaptResults(bad.body);           // fed the error payload on purpose: must be total
  ok('adaptResults never throws on unexpected payload', !!r2 && Object.keys(r2.models).length === 0, r2);
  execSync(`curl -s -X DELETE ${BASE}/api/experiments/${expId} > /dev/null || true`);
}

let fails = 0;
for (const [c, n, g] of out) { if (!c) fails++; console.log(`${c ? 'PASS' : 'FAIL'}  ${n}${c ? '' : '  → ' + JSON.stringify(g)}`); }
console.log(fails === 0 ? `\n✅ LIVE BACKEND: ${out.length}/${out.length} pass` : `\n❌ ${fails} failed`);
process.exit(fails ? 1 : 0);
