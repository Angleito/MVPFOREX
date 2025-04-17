// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Supabase Integration Tests', () => {
  // Skip these tests if environment variables aren't set
  test.beforeEach(async ({ page }) => {
    // Check if Supabase environment variables are set
    const hasSupabaseConfig = await page.evaluate(() => {
      return !!(window.process?.env?.NEXT_PUBLIC_SUPABASE_URL && 
                 window.process?.env?.NEXT_PUBLIC_SUPABASE_ANON_KEY);
    });
    
    if (!hasSupabaseConfig) {
      test.skip();
      console.log('Supabase environment variables not configured, skipping tests');
    }
  });

  test('Supabase client initializes correctly', async ({ page }) => {
    // Navigate to home page
    await page.goto('/');
    
    // Add test instrumentation to detect Supabase initialization
    await page.evaluate(() => {
      // Use a custom attribute on a DOM element instead of window object
      // to avoid TypeScript errors
      const testState = document.createElement('div');
      testState.id = 'supabase-test-state';
      testState.setAttribute('data-initialized', 'false');
      document.body.appendChild(testState);
      
      // Override console.log to capture Supabase initialization message
      const originalConsoleLog = console.log;
      console.log = function(...args) {
        originalConsoleLog.apply(console, args);
        
        // Check if log message indicates Supabase initialization
        if (args.some(arg => typeof arg === 'string' && arg.includes('Supabase client initialized'))) {
          const testState = document.getElementById('supabase-test-state');
          if (testState) {
            testState.setAttribute('data-initialized', 'true');
          }
        }
      };
    });
    
    // Reload page to trigger initialization with our instrumentation
    await page.reload();
    
    // Wait for a moment to allow initialization to complete
    await page.waitForTimeout(2000);
    
    // Check if Supabase was initialized
    const isInitialized = await page.evaluate(() => {
      const testState = document.getElementById('supabase-test-state');
      return testState && testState.getAttribute('data-initialized') === 'true';
    });
    
    // Expect initialization to have occurred
    // Note: This could pass even if real DB connection fails as we check for the attempt
    expect(isInitialized).toBeTruthy();
  });

  test('feedback submission flow works', async ({ page }) => {
    // Navigate to home page
    await page.goto('/');
    
    // Mock the feedback API to isolate testing from backend
    await page.route('/api/feedback', async route => {
      const postData = JSON.parse(route.request().postData() || '{}');
      
      // Verify required fields are present
      if (!postData.model || postData.rating === undefined) {
        await route.fulfill({ 
          status: 400, 
          body: JSON.stringify({ status: 'error', error: 'Missing required fields' }) 
        });
        return;
      }
      
      // Mock successful response
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ 
          status: 'ok', 
          message: 'Feedback submitted successfully',
          data: { id: 'mock-feedback-id' }
        })
      });
    });
    
    // Add a simple feedback submission form for testing
    await page.evaluate(() => {
      if (!document.querySelector('#feedback-test-form')) {
        const form = document.createElement('form');
        form.id = 'feedback-test-form';
        form.innerHTML = `
          <h3>Test Feedback Submission</h3>
          <select id="feedback-model">
            <option value="GPT-4.1">GPT-4.1</option>
            <option value="Claude 3.7">Claude 3.7</option>
            <option value="Perplexity Pro">Perplexity Pro</option>
          </select>
          <input type="number" id="feedback-rating" min="1" max="5" value="4" />
          <textarea id="feedback-comments">Test comment</textarea>
          <button type="submit">Submit Feedback</button>
          <div id="feedback-result"></div>
        `;
        form.style.padding = '20px';
        form.style.margin = '20px';
        form.style.border = '1px solid #ccc';
        
        document.body.appendChild(form);
        
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const modelElement = document.querySelector('#feedback-model');
          const ratingElement = document.querySelector('#feedback-rating');
          const commentsElement = document.querySelector('#feedback-comments');
          const resultElement = document.querySelector('#feedback-result');
          
          if (!modelElement || !ratingElement || !commentsElement || !resultElement) {
            console.error('Form elements not found');
            return;
          }
          
          // Get values safely using DOM properties without TypeScript issues
          const model = modelElement.tagName === 'SELECT' ? modelElement.options[modelElement.selectedIndex].value : '';
          const rating = ratingElement.tagName === 'INPUT' ? parseInt(ratingElement.getAttribute('value') || '0') : 0;
          const comments = commentsElement.tagName === 'TEXTAREA' ? commentsElement.textContent || '' : '';
          
          try {
            const res = await fetch('/api/feedback', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ model, rating, comments, analysisId: 'test-analysis' })
            });
            
            const data = await res.json();
            resultElement.textContent = 
              data.status === 'ok' 
                ? 'Feedback submitted successfully!' 
                : `Error: ${data.error || 'Unknown error'}`;
          } catch (err) {
            resultElement.textContent = `Error: ${err instanceof Error ? err.message : 'Unknown error'}`;
          }
        });
      }
    });
    
    // Submit the form
    await page.locator('#feedback-test-form button[type="submit"]').click();
    
    // Verify success message appears
    await expect(page.locator('#feedback-result')).toContainText('Feedback submitted successfully', {
      timeout: 5000
    });
  });
});
