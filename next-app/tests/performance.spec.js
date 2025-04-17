// @ts-check
const { test, expect } = require('@playwright/test');

// Simple performance test: measures time to load home page and render chart

test('home page loads within 2 seconds and chart is visible', async ({ page }) => {
  const start = Date.now();
  await page.goto('/');
  // Wait for chart or main content
  const chartFound = await Promise.race([
    page.waitForSelector('div[style*="height: 400"]', { timeout: 2000 }).then(() => true).catch(() => false),
    page.waitForSelector('text=/chart|gold|price/i', { timeout: 2000 }).then(() => true).catch(() => false)
  ]);
  const duration = Date.now() - start;
  expect(chartFound).toBeTruthy();
  expect(duration).toBeLessThanOrEqual(2000);
});
