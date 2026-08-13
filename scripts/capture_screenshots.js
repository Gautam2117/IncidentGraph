const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();

  console.log('Navigating to login page...');
  await page.goto('http://localhost:3000/incidents');

  const adminEmail = process.env.BOOTSTRAP_ADMIN_EMAIL || 'admin@incidentgraph.local';
  const adminPassword = process.env.BOOTSTRAP_ADMIN_PASSWORD || 'replace-with-a-random-admin-password-at-least-16-characters';

  await page.getByLabel('Username or email').fill(adminEmail);
  await page.getByLabel('Password').fill(adminPassword);
  await page.getByRole('button', { name: 'Open control plane' }).click();
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });

  const assetsDir = path.join(__dirname, '..', 'docs', 'assets');

  console.log('Capturing Incidents Dashboard screenshot...');
  await page.goto('http://localhost:3000/incidents');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(assetsDir, 'incidents_dashboard.png') });

  console.log('Capturing Scenarios Lab screenshot...');
  await page.goto('http://localhost:3000/scenarios');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(assetsDir, 'scenarios_lab.png') });

  console.log('Capturing Evaluation Harness screenshot...');
  await page.goto('http://localhost:3000/evaluations');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(assetsDir, 'evaluations_harness.png') });

  console.log('Screenshots captured successfully!');
  await browser.close();
})().catch((err) => {
  console.error('Screenshot capture error:', err);
  process.exit(1);
});
