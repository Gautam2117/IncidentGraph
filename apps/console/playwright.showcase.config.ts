import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/showcase',
  fullyParallel: true,
  reporter: 'line',
  use: {
    baseURL: 'http://127.0.0.1:3100',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'INCIDENTGRAPH_DEMO_MODE=true NEXT_PUBLIC_INCIDENTGRAPH_DEMO_MODE=true npm run dev -- --hostname 127.0.0.1 --port 3100',
    url: 'http://127.0.0.1:3100',
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
