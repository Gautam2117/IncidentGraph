import { expect, test } from '@playwright/test';

test.describe('public portfolio showcase', () => {
  test('opens the recruiter story and walks the primary incident', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Incidents explain themselves/ })).toBeVisible();
    await expect(page.getByText('Public interactive showcase')).toBeVisible();

    await page.getByRole('link', { name: 'Trace a SEV-1' }).click();
    await expect(page.getByRole('heading', { name: 'Checkout latency spike after payments deploy' })).toBeVisible();
    await expect(page.getByText('Payments isolated as primary service')).toBeVisible();
    await expect(page.getByText('Showcase mode')).toBeVisible();
  });

  test('serves deterministic console data and mutation previews', async ({ page, request }) => {
    const healthResponse = await request.get('/api/proxy/health/ready');
    expect(healthResponse.ok()).toBeTruthy();
    const health = await healthResponse.json();
    expect(health.status).toBe('ready');
    expect(Date.now() - Date.parse(health.timestamp)).toBeLessThan(60_000);

    await page.goto('/scenarios');
    await expect(page.getByRole('heading', { name: 'Chaos scenarios' })).toBeVisible();
    await page.getByRole('button', { name: 'Inject & probe' }).first().click();
    await expect(page.getByText('fault_verified')).toBeVisible();

    await page.goto('/evaluations');
    await expect(page.getByText('100.0%', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('offline', { exact: true })).toBeVisible();
  });

  test('keeps security headers on public pages', async ({ request }) => {
    const response = await request.get('/');
    expect(response.headers()['x-content-type-options']).toBe('nosniff');
    expect(response.headers()['x-frame-options']).toBe('DENY');
    expect(response.headers()['content-security-policy']).toContain("default-src 'self'");
  });
});
