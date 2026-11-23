// Loopback-only Prism checks. No real service, Django, database or JWT is used.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { once } from 'node:events';
import net from 'node:net';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';

const cli = process.argv[2];
if (!cli) {
  process.stderr.write('Specify the path to an already prepared Prism CLI entry point.\n');
  process.exit(2);
}
const spec = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'openapi.yaml');
const reservation = net.createServer();
reservation.listen(0, '127.0.0.1');
await once(reservation, 'listening');
const port = reservation.address().port;
await new Promise((resolve) => reservation.close(resolve));
// Minimal child environment: do not forward the user's credentials/environment.
const env = { PATH: process.env.PATH };
if (process.env.SystemRoot) env.SystemRoot = process.env.SystemRoot;
const prism = spawn(process.execPath, [cli, 'mock', spec, '-h', '127.0.0.1', '-p', String(port)], {
  cwd: path.dirname(spec), env, stdio: 'ignore', windowsHide: true,
});
let startupError = false;
prism.on('error', () => { startupError = true; });
const base = `http://127.0.0.1:${port}`;
// An opaque per-run mock bearer, private and never printed/persisted. It is not a JWT.
const mockBearer = randomBytes(32).toString('hex');
let checks = 0;
let lastStatus;
let expectedStatus;
async function check(method, route, expected, body, prefer, inspect, authenticated = true) {
  const headers = {};
  if (authenticated) headers.Authorization = `Bearer ${mockBearer}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (prefer) headers.Prefer = prefer;
  const response = await fetch(base + route, {
    method, headers, body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(5000),
  });
  lastStatus = response.status;
  expectedStatus = expected;
  assert.equal(response.status, expected, 'Unexpected mock status');
  if (inspect) inspect(await response.json());
  checks += 1;
}

try {
  let ready = false;
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (startupError || prism.exitCode !== null) throw new Error('Mock startup failed');
    try {
      const response = await fetch(base + '/health/live', { signal: AbortSignal.timeout(300) });
      if (response.status === 200) { ready = true; break; }
    } catch { /* Server not ready; do not print response or internal diagnostics. */ }
    await delay(100);
  }
  assert.ok(ready, 'Mock startup timeout');
  const articles = '/api/knowledge/v1/articulos/';
  const draft = articles + '10900000-0000-4000-8000-000000000001/';
  const article = articles + '10900000-0000-4000-8000-000000000002/';
  await check('GET', '/health/live', 200, undefined, undefined, undefined, false);
  await check('GET', '/health/ready', 503, undefined, 'code=503', (data) => {
    assert.equal(data.database, 'down');
  }, false);
  await check('GET', articles, 401, undefined, undefined, undefined, false);
  await check('GET', articles + '?q=consulta&page=1&page_size=20', 200, undefined,
    'example=empresa', (data) => assert.equal(data.results[0].visibilidad, 'empresa'));
  await check('GET', articles + '?q=sincoincidencias', 200, undefined,
    'example=vacia', (data) => assert.deepEqual(data.results, []));
  await check('POST', articles, 201, {}, undefined, (data) => assert.equal(data.estado, 'borrador'));
  await check('GET', article, 200, undefined, 'example=empresa', (data) => {
    assert.equal(data.estado, 'publicado');
  });
  await check('PATCH', draft, 200, { titulo: 'Borrador de demostración' }, undefined, (data) => {
    assert.equal(data.titulo, 'Borrador de demostración');
  });
  await check('GET', '/api/knowledge/v1/soluciones/?q=consulta', 200, undefined,
    'example=candidatos', (data) => {
      assert.ok(data.results.every((item) => item.estado === 'publicado'));
      assert.ok(!Object.hasOwn(data, 'coincidencia_confirmada'));
    });
  await check('GET', '/api/knowledge/v1/soluciones/?q=sincoincidencias', 200, undefined,
    'example=vacia', (data) => assert.deepEqual(data.results, []));
  await check('GET', '/api/knowledge/v1/soluciones/', 400);
  await check('POST', articles, 400, { autor_id: 'not-client-controlled' });
  await check('PATCH', draft, 400, {});
  await check('PATCH', draft, 400, { estado: 'publicado' });
  await check('GET', articles + '?page_size=101', 400);
  await check('GET', articles, 503, undefined, 'code=503', (data) => {
    assert.equal(data.codigo, 'servicio_no_disponible');
  });
  // Prism selects the documented 400 status; its validation report is tool behavior,
  // not evidence that the proposed KB error envelope or authorization is implemented.
  process.stdout.write(`PASS Prism loopback smoke: checks=${checks}; no API/JWT/DB integration claimed\n`);
} catch (error) {
  // Assertion messages can include payload fragments: print neither them nor stack traces.
  process.stderr.write(`FAIL Prism smoke after ${checks} checks (${error.name}); `
    + `expected=${expectedStatus}; status=${lastStatus}; details suppressed\n`);
  process.exitCode = 1;
} finally {
  if (prism.exitCode === null) {
    const stopped = once(prism, 'exit');
    prism.kill();
    await Promise.race([stopped, delay(5000)]);
    if (prism.exitCode === null) prism.kill('SIGKILL');
  }
}
