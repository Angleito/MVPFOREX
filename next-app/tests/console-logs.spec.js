// @ts-check
const { test, expect } = require('@playwright/test');

test('Check console logs', async ({ page }) => {
  // Create array to store console logs
  const logs = [];
  
  // Listen for console messages
  page.on('console', (msg) => {
    logs.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });

  // Listen for page errors
  page.on('pageerror', (error) => {
    logs.push({
      type: 'error',
      text: error.message,
      stack: error.stack
    });
  });

  // Navigate to the application
  await page.goto('http://localhost:3002');
  
  // Wait for the page to be fully loaded
  await page.waitForLoadState('networkidle');
  
  // Wait a bit more to capture any delayed logs
  await page.waitForTimeout(3000);
  
  // Click on an analysis button to trigger API calls and data processing
  await page.getByText('Analyze with GPT-4.1').click();
  
  // Wait for the analysis to complete
  await page.waitForTimeout(5000);
  
  // Display all collected logs
  console.log('CONSOLE LOGS COLLECTED:');
  logs.forEach((log, index) => {
    console.log(`--- Log ${index + 1} ---`);
    console.log(`Type: ${log.type}`);
    console.log(`Message: ${log.text}`);
    if (log.location) {
      console.log(`Location: ${log.location.url}:${log.location.lineNumber}`);
    }
    if (log.stack) {
      console.log(`Stack: ${log.stack}`);
    }
    console.log('-------------------');
  });
  
  // Verify that some logs exist
  expect(logs.length).toBeGreaterThan(0);
});
