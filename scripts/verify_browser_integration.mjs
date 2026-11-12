import { spawn } from 'child_process';
import http from 'http';

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchJson(url) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(2000, () => {
      req.destroy();
      reject(new Error('timeout'));
    });
  });
}

async function runVerification() {
  const backend = spawn('backend\\venv\\Scripts\\python.exe', ['backend\\run.py'], {
    env: { ...process.env, PORT: '5000', FLASK_ENV: 'development', FLASK_DEBUG: '0' },
    stdio: 'pipe'
  });

  for (let i = 0; i < 30; i++) {
    await sleep(300);
    try {
      const res = await fetchJson('http://localhost:5000/api/v1/health');
      if (res && res.data && res.data.status === 'healthy') break;
    } catch (e) {}
  }

  const frontend = spawn('npx.cmd', ['vite', '--port', '5173', '--strictPort'], {
    cwd: './frontend',
    shell: true,
    stdio: 'pipe'
  });

  for (let i = 0; i < 30; i++) {
    await sleep(300);
    try {
      const ok = await new Promise((resolve) => {
        const req = http.get('http://localhost:5173', (res) => resolve(res.statusCode === 200));
        req.on('error', () => resolve(false));
      });
      if (ok) break;
    } catch (e) {}
  }

  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const chrome = spawn(chromePath, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--user-data-dir=' + process.env.TEMP + '\\chrome_integration_profile'
  ]);

  let targets = null;
  for (let i = 0; i < 30; i++) {
    await sleep(300);
    try {
      targets = await fetchJson('http://127.0.0.1:9222/json');
      if (targets && targets.length > 0) break;
    } catch (e) {}
  }

  const ws = new WebSocket(targets[0].webSocketDebuggerUrl);

  const consoleLogs = [];
  const networkResponses = [];
  let reqId = 1;
  const pending = new Map();

  function send(method, params = {}) {
    const id = reqId++;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  await new Promise((resolve) => ws.onopen = resolve);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) p.reject(msg.error);
      else p.resolve(msg.result);
    }

    if (msg.method === 'Runtime.consoleAPICalled') {
      const text = msg.params.args.map(a => a.value || a.description).join(' ');
      consoleLogs.push({ type: msg.params.type, text });
    }

    if (msg.method === 'Network.responseReceived') {
      networkResponses.push(msg.params);
    }
  };

  await send('Page.enable');
  await send('Network.enable');
  await send('Runtime.enable');

  await send('Page.navigate', { url: 'http://localhost:5173' });

  let renderedStatus = null;
  let renderedText = null;

  for (let i = 0; i < 30; i++) {
    await sleep(300);
    const evalResult = await send('Runtime.evaluate', {
      expression: `
        (() => {
          const el = document.querySelector('#api-status');
          if (!el) return null;
          return {
            status: el.getAttribute('data-status'),
            html: el.outerHTML,
            text: el.innerText
          };
        })()
      `,
      returnByValue: true
    });

    const val = evalResult.result && evalResult.result.value;
    if (val && val.status === 'healthy') {
      renderedStatus = val.status;
      renderedText = val.text;
      break;
    }
  }

  const healthEvent = networkResponses.find(r => r.response.url.includes('/api/v1/health'));
  let bodyPayload = null;
  if (healthEvent) {
    try {
      const bodyRes = await send('Network.getResponseBody', { requestId: healthEvent.requestId });
      bodyPayload = JSON.parse(bodyRes.body);
    } catch (e) {
      bodyPayload = e.message;
    }
  }

  console.log('=== EXACT BROWSER INTEGRATION EVIDENCE ===');
  console.log('Request URL:', healthEvent ? healthEvent.response.url : 'NOT FOUND');
  console.log('HTTP Status Code:', healthEvent ? healthEvent.response.status : 'N/A');
  console.log('Response Headers:', JSON.stringify(healthEvent ? healthEvent.response.headers : {}, null, 2));
  console.log('Response JSON Body:', JSON.stringify(bodyPayload, null, 2));
  console.log('Browser Rendered Status:', renderedStatus);
  console.log('Browser Rendered Text:', renderedText);
  console.log('Browser Console Messages:', consoleLogs);

  ws.close();
  chrome.kill();
  frontend.kill();
  backend.kill();
}

runVerification().catch(e => {
  console.error(e);
  process.exit(1);
});
