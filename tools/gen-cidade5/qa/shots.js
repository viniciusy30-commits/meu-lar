// node shots.js jobs.json  -> renderiza cada job {file, eye, at, out, w, h, fov}
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const dir = __dirname;
const srv = http.createServer((q, s) => { const p = path.join(dir, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'Content-Type': p.endsWith('.html') ? 'text/html' : p.endsWith('.js') ? 'text/javascript' : p.endsWith('.png') ? 'image/png' : 'application/octet-stream' }); s.end(d); }); });
srv.listen(0, async () => {
  const port = srv.address().port;
  const jobs = JSON.parse(fs.readFileSync(process.argv[2]));
  const br = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const pg = await br.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('console', m => { if (m.type() === 'error') console.log('console:', m.text()); });
  await pg.goto(`http://127.0.0.1:${port}/view.html`); await pg.waitForFunction('window.ready === true');
  for (const j of jobs) {
    const url = await pg.evaluate(o => window.render(o), j);
    fs.writeFileSync(j.out, Buffer.from(url.split(',')[1], 'base64'));
  }
  await br.close(); srv.close();
});
