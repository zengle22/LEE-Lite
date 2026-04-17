import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  reporter: 'json',
  use: {
    headless: true,
    browserName: 'chromium',
  },
});
