// @ts-check
const { test, expect } = require('@playwright/test');

test('Diagnose blank screen issues', async ({ page }) => {
  // Array to collect logs, errors, and network requests
  const logs = [];
  const errors = [];
  const networkRequests = [];
  const networkResponses = [];
  
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
    errors.push({
      text: error.message,
      stack: error.stack
    });
  });
  
  // Listen for network requests
  page.on('request', request => {
    networkRequests.push({
      url: request.url(),
      method: request.method(),
      headers: request.headers(),
      resourceType: request.resourceType()
    });
  });
  
  // Listen for network responses
  page.on('response', response => {
    networkResponses.push({
      url: response.url(),
      status: response.status(),
      statusText: response.statusText(),
      headers: response.headers()
    });
  });

  // Navigate to the application
  console.log('Navigating to the application...');
  await page.goto('http://localhost:3001');
  
  // Wait to ensure page had a chance to load or error out
  await page.waitForTimeout(5000);
  
  // Take a screenshot to visualize the current state
  await page.screenshot({ path: 'blank-screen-debug.png', fullPage: true });
  
  // Check if the page is truly blank by looking for any visible elements
  const visibleContent = await page.evaluate(() => {
    // Check if body has any visible children
    const body = document.body;
    const bodyHasVisibleChildren = Array.from(body.children).some(child => {
      const style = window.getComputedStyle(child);
      return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
    });
    
    // Check if there's any text content visible
    const hasTextContent = body.innerText && body.innerText.trim().length > 0;
    
    // Check if any elements have been rendered
    const elementCount = document.querySelectorAll('*').length;
    
    // Check if main element exists
    const mainExists = !!document.querySelector('main');
    
    // Get HTML content for analysis
    const htmlContent = document.documentElement.outerHTML.substring(0, 10000); // First 10k chars
    
    return {
      bodyHasVisibleChildren,
      hasTextContent,
      elementCount,
      mainExists,
      htmlContent
    };
  });
  
  // Attempt to access React DevTools if possible
  const reactInfo = await page.evaluate(() => {
    // @ts-ignore: React DevTools global hook is not in TypeScript definitions
    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
      return {
        // @ts-ignore: React DevTools global hook is not in TypeScript definitions
        hasReactDevTools: true,
        // @ts-ignore: React DevTools global hook is not in TypeScript definitions
        renderers: Object.keys(window.__REACT_DEVTOOLS_GLOBAL_HOOK__._renderers).length
      };
    }
    return { hasReactDevTools: false };
  });
  
  // Check if TradingView widget is loading
  const hasTradingViewWidget = await page.evaluate(() => {
    return !!document.querySelector('div[id^="tradingview"]') || 
           !!document.querySelector('iframe[src*="tradingview.com"]');
  });
  
  // Analyze styles to check for CSS issues
  const styleInfo = await page.evaluate(() => {
    const sheets = document.styleSheets;
    let styleInfo = { 
      styleSheetCount: sheets.length,
      cssRules: 0
    };
    
    try {
      for (let i = 0; i < sheets.length; i++) {
        styleInfo.cssRules += sheets[i].cssRules.length;
      }
    } catch (e) {
      styleInfo.cssError = e.message;
    }
    
    return styleInfo;
  });
  
  // Check for NextJS specific elements
  const nextJsInfo = await page.evaluate(() => {
    return {
      hasNextData: !!document.getElementById('__NEXT_DATA__'),
      hasNextHydration: !!document.querySelector('[data-nextjs-hydration]')
    };
  });
  
  // Print comprehensive diagnostic information
  console.log('\n----- DIAGNOSTIC RESULTS -----');
  console.log('\nPage Rendering Status:');
  console.log(`Visible Children: ${visibleContent.bodyHasVisibleChildren}`);
  console.log(`Has Text Content: ${visibleContent.hasTextContent}`);
  console.log(`Element Count: ${visibleContent.elementCount}`);
  console.log(`Main Element Exists: ${visibleContent.mainExists}`);
  console.log(`TradingView Widget Exists: ${hasTradingViewWidget}`);
  
  console.log('\nReact Status:');
  console.log(`React DevTools Available: ${reactInfo.hasReactDevTools}`);
  if (reactInfo.hasReactDevTools) {
    console.log(`React Renderers: ${reactInfo.renderers}`);
  }
  
  console.log('\nNext.js Status:');
  console.log(`Next Data Element: ${nextJsInfo.hasNextData}`);
  console.log(`Next Hydration Data: ${nextJsInfo.hasNextHydration}`);
  
  console.log('\nStyle Information:');
  console.log(`Style Sheets: ${styleInfo.styleSheetCount}`);
  console.log(`CSS Rules: ${styleInfo.cssRules}`);
  if (styleInfo.cssError) {
    console.log(`CSS Error: ${styleInfo.cssError}`);
  }
  
  console.log('\nConsole Logs:');
  logs.forEach((log, index) => {
    console.log(`${index + 1}. [${log.type}] ${log.text}`);
  });
  
  console.log('\nPage Errors:');
  if (errors.length === 0) {
    console.log('No JavaScript errors detected');
  } else {
    errors.forEach((error, index) => {
      console.log(`${index + 1}. ${error.text}`);
      console.log(`   ${error.stack}`);
    });
  }
  
  console.log('\nNetwork Activity:');
  console.log(`Requests Made: ${networkRequests.length}`);
  console.log(`Responses Received: ${networkResponses.length}`);
  
  // Check for failed network requests (4xx/5xx)
  const failedRequests = networkResponses.filter(r => r.status >= 400);
  console.log(`Failed Requests: ${failedRequests.length}`);
  if (failedRequests.length > 0) {
    console.log('\nFailed Network Requests:');
    failedRequests.forEach((req, index) => {
      console.log(`${index + 1}. ${req.status} ${req.statusText}: ${req.url}`);
    });
  }
  
  // Output partial HTML for diagnosis if the page is blank
  if (!visibleContent.bodyHasVisibleChildren || !visibleContent.hasTextContent) {
    console.log('\nPartial HTML Content:');
    console.log(visibleContent.htmlContent.substring(0, 500) + '...');
  }
  
  // Summary of findings
  console.log('\n----- DIAGNOSIS SUMMARY -----');
  if (errors.length > 0) {
    console.log('❌ JavaScript errors were detected - likely preventing rendering');
  }
  
  if (failedRequests.length > 0) {
    console.log('❌ Failed network requests may be causing rendering issues');
  }
  
  if (!nextJsInfo.hasNextData) {
    console.log('❌ Next.js data is missing - application may not be properly bootstrapped');
  }
  
  if (!visibleContent.bodyHasVisibleChildren) {
    console.log('❌ No visible content detected - severe rendering issue');
  }
  
  if (visibleContent.elementCount < 10) {
    console.log('❌ Very few DOM elements - application markup is not rendering properly');
  }
  
  if (logs.some(log => log.text.includes('hydration') && log.type === 'error')) {
    console.log('❌ Next.js hydration errors detected - client/server markup mismatch');
  }
  
  if (errors.length === 0 && visibleContent.bodyHasVisibleChildren && visibleContent.elementCount > 10) {
    console.log('✅ Basic rendering appears to be working, but content may be invisible');
    console.log('   Check for CSS issues like z-index problems or improper positioning');
  }
});
