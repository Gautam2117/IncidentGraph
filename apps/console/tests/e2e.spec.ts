import { test, expect } from '@playwright/test';

test.describe('IncidentGraph authenticated engineering console', () => {
  test('protects routes, authenticates, and renders every primary live-API surface', async ({ page }) => {
    await page.goto('/incidents');
    await expect(page).toHaveURL(/\/login\?returnTo=%2Fincidents/);

    const adminEmail = process.env.BOOTSTRAP_ADMIN_EMAIL || 'admin@incidentgraph.local';
    const adminPassword = process.env.BOOTSTRAP_ADMIN_PASSWORD || 'replace-with-a-random-admin-password-at-least-16-characters';

    await page.getByLabel('Username or email').fill(adminEmail);
    await page.getByLabel('Password').fill(adminPassword);
    await page.getByRole('button', { name: 'Open control plane' }).click();
    await expect(page).toHaveURL(/\/incidents$/);
    await expect(page.getByRole('heading', { name: 'Active & Historical Incidents' })).toBeVisible();

    const routes: Array<[string, string]> = [
      ['/', 'Investigate with evidence. Remediate with control.'],
      ['/topology', 'Service Dependency Topology'],
      ['/knowledge', 'Knowledge index'],
      ['/knowledge/debug', 'Inspect ranked evidence'],
      ['/scenarios', 'Chaos scenarios'],
      ['/evaluations', 'AI evaluations'],
      ['/evaluations/compare', 'Compare evaluations'],
      ['/audit', 'Audit trail'],
      ['/settings/models', 'Model providers'],
      ['/settings/retrieval', 'Retrieval configuration'],
      ['/settings/webhooks', 'Webhook integration'],
    ];
    for (const [route, heading] of routes) {
      await page.goto(route);
      await expect(page.getByRole('heading', { name: heading })).toBeVisible();
    }

    const securityHeaders = await page.request.get('/login');
    expect(securityHeaders.headers()['x-content-type-options']).toBe('nosniff');
    expect(securityHeaders.headers()['x-frame-options']).toBe('DENY');
  });

  test('rejects cross-origin mutation attempts at the session boundary', async ({ request }) => {
    const adminEmail = process.env.BOOTSTRAP_ADMIN_EMAIL || 'admin@incidentgraph.local';
    const adminPassword = process.env.BOOTSTRAP_ADMIN_PASSWORD || 'replace-with-a-random-admin-password-at-least-16-characters';
    const response = await request.post('/api/session/login', {
      headers: { origin: 'https://attacker.invalid' },
      data: { username: adminEmail, password: adminPassword },
    });
    expect(response.status()).toBe(403);
  });
});
