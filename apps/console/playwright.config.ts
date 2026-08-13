import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: "cd ../.. && PYTHON_BIN=${INCIDENTGRAPH_PYTHON:-.venv/bin/python}; PYTHONPATH=services/control-plane:. BOOTSTRAP_ADMIN_EMAIL=playwright-admin@incidentgraph.dev BOOTSTRAP_ADMIN_PASSWORD='PlaywrightAdminPassword123!' $PYTHON_BIN scripts/bootstrap_admin.py && PYTHONPATH=services/control-plane:. $PYTHON_BIN -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: 'http://localhost:8000/api/v1/health/live',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:3000/login',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
