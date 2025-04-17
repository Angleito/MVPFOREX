// @ts-check
const { test, expect } = require('@playwright/test');

test('debug layout issues', async ({ page }) => {
  // Navigate to the app
  await page.goto('http://localhost:3001');
  
  // Take a screenshot for visual inspection
  await page.screenshot({ path: 'layout-debug.png', fullPage: true });
  
  // Get all element dimensions and positions
  const layoutData = await page.evaluate(() => {
    // Function to get element info
    function getElementInfo(selector, name) {
      const elements = document.querySelectorAll(selector);
      return Array.from(elements).map((el, index) => {
        const rect = el.getBoundingClientRect();
        return {
          name: `${name || selector} #${index}`,
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          visible: rect.width > 0 && rect.height > 0 && 
                 window.getComputedStyle(el).display !== 'none' &&
                 window.getComputedStyle(el).visibility !== 'hidden'
        };
      });
    }
    
    // Collect info about key elements
    return {
      header: getElementInfo('h1', 'Header'),
      chart: getElementInfo('div[style*="height: 400"]', 'Chart'),
      buttons: getElementInfo('button', 'Button'),
      outputAreas: getElementInfo('div[style*="background: #fffbe6"]', 'OutputArea'),
      mainContainer: getElementInfo('main', 'MainContainer'),
      // Check for any overlapping elements
      overlaps: (() => {
        const allElements = document.querySelectorAll('div, button, h1, h2, h3, p');
        const overlaps = [];
        
        for (let i = 0; i < allElements.length; i++) {
          const el1 = allElements[i];
          const rect1 = el1.getBoundingClientRect();
          if (rect1.width === 0 || rect1.height === 0) continue;
          
          for (let j = i+1; j < allElements.length; j++) {
            const el2 = allElements[j];
            // Skip checking parent/child relationships
            if (el1.contains(el2) || el2.contains(el1)) continue;
            
            const rect2 = el2.getBoundingClientRect();
            if (rect2.width === 0 || rect2.height === 0) continue;
            
            // Check for overlap
            if (!(rect1.right < rect2.left || 
                rect1.left > rect2.right || 
                rect1.bottom < rect2.top || 
                rect1.top > rect2.bottom)) {
              overlaps.push({
                element1: {
                  tagName: el1.tagName,
                  className: el1.className,
                  id: el1.id,
                  text: el1.textContent.substring(0, 20) + '...',
                  rect: {
                    x: Math.round(rect1.x),
                    y: Math.round(rect1.y),
                    width: Math.round(rect1.width),
                    height: Math.round(rect1.height)
                  }
                },
                element2: {
                  tagName: el2.tagName,
                  className: el2.className,
                  id: el2.id,
                  text: el2.textContent.substring(0, 20) + '...',
                  rect: {
                    x: Math.round(rect2.x),
                    y: Math.round(rect2.y),
                    width: Math.round(rect2.width),
                    height: Math.round(rect2.height)
                  }
                }
              });
            }
          }
        }
        return overlaps;
      })(),
      // Check for any model analysis errors
      errors: Array.from(document.querySelectorAll('div'))
        .filter(div => div.textContent && div.textContent.includes('Analysis failed'))
        .map(div => div.textContent)
    };
  });
  
  // Log the layout data for analysis
  console.log('LAYOUT DIAGNOSTICS:');
  console.log(JSON.stringify(layoutData, null, 2));
});
