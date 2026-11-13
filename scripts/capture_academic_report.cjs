const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require('C:/Users/YuRui/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '..');
(async () => {
  const browser = await chromium.launch({headless: true, executablePath: 'C:/Users/YuRui/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe'});
  const evidence = {};
  const archive = path.join(root, 'results/academic-20261113/screenshots');
  fs.mkdirSync(archive, {recursive: true});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1200}, deviceScaleFactor: 1.5});
    await page.goto(pathToFileURL(path.join(root, 'results/academic-20261113/report.html')).href);
    await page.evaluate(() => document.fonts.ready);
    for (const id of ['glitch', 'glitch-projects', 'infer', 'infer-projects', 'academic-graph']) {
      const section = page.locator('#' + id);
      const clipped = await section.locator('pre,td,h1,.pair').evaluateAll(nodes => nodes.filter(n => n.scrollWidth > n.clientWidth + 1).length);
      assert.equal(clipped, 0, 'Clipped text in ' + id);
      const box = await section.boundingBox();
      assert.equal(box.width, 1440);
      await section.screenshot({path: path.join(archive, id + '.png')});
      evidence[id] = {box, text: await section.innerText(), clipped};
    }
  } finally { await browser.close(); }
  fs.writeFileSync(path.join(root, 'results/academic-20261113/screenshots.json'), JSON.stringify(evidence, null, 2) + '\n');
  console.log('5 report panels captured without horizontal clipping');
})().catch(error => {console.error(error); process.exitCode = 1;});
