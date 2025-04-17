"""Browser compatibility tests using Playwright."""
import pytest
from playwright.sync_api import sync_playwright, expect
import json

@pytest.fixture(scope="session")
def browser_types():
    """List of browsers to test."""
    return ['chromium', 'firefox', 'webkit']

@pytest.fixture(scope="session")
def page_url():
    """Test server URL."""
    return 'http://localhost:5000'

def test_page_loads_in_all_browsers(browser_types, page_url):
    """Test that the page loads correctly in all supported browsers."""
    with sync_playwright() as p:
        for browser_type in browser_types:
            browser = getattr(p, browser_type).launch()
            page = browser.new_page()
            
            # Load the page
            page.goto(page_url)
            
            # Check that critical elements are present
            expect(page.locator('#priceChart')).to_be_visible()
            expect(page.locator('#analyzeBtn')).to_be_visible()
            expect(page.locator('#marketOverview')).to_be_visible()
            
            # Test responsive design
            page.set_viewport_size({'width': 1920, 'height': 1080})
            expect(page.locator('.chart-container')).to_be_visible()
            
            page.set_viewport_size({'width': 768, 'height': 1024})
            expect(page.locator('.chart-container')).to_be_visible()
            
            page.set_viewport_size({'width': 375, 'height': 812})
            expect(page.locator('.chart-container')).to_be_visible()
            
            browser.close()

def test_analysis_workflow_in_all_browsers(browser_types, page_url):
    """Test the analysis workflow in all supported browsers."""
    with sync_playwright() as p:
        for browser_type in browser_types:
            browser = getattr(p, browser_type).launch()
            page = browser.new_page()
            
            # Load the page
            page.goto(page_url)
            
            # Trigger analysis
            page.click('#analyzeBtn')
            
            # Wait for analysis results
            expect(page.locator('#results')).to_be_visible()
            expect(page.locator('.loading-overlay')).to_be_hidden()
            
            # Check chart interactions
            page.click('[data-chart-type="line"]')
            expect(page.locator('#priceChart')).to_be_visible()
            
            page.click('[data-chart-type="candlestick"]')
            expect(page.locator('#priceChart')).to_be_visible()
            
            browser.close()

def test_metrics_dashboard_in_all_browsers(browser_types, page_url):
    """Test the metrics dashboard in all supported browsers."""
    with sync_playwright() as p:
        for browser_type in browser_types:
            browser = getattr(p, browser_type).launch()
            page = browser.new_page()
            
            # Load the page
            page.goto(page_url)
            
            # Check all chart components
            charts = [
                '#patternRecognitionChart',
                '#nlpMetricsChart',
                '#latencyChart',
                '#backtestChart',
                '#feedbackChart'
            ]
            
            for chart_id in charts:
                expect(page.locator(chart_id)).to_be_visible()
            
            # Test chart interactions
            for chart_id in charts:
                page.hover(chart_id)
                # Ensure tooltips or hover effects work
                expect(page.locator(f"{chart_id} .plotly")).to_be_visible()
            
            browser.close()

def test_error_handling_in_all_browsers(browser_types, page_url):
    """Test error handling in all supported browsers."""
    with sync_playwright() as p:
        for browser_type in browser_types:
            browser = getattr(p, browser_type).launch()
            page = browser.new_page()
            
            # Load the page
            page.goto(page_url)
            
            # Test with invalid timeframe
            page.evaluate("""() => {
                fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ timeframe: 'invalid' })
                })
            }""")
            
            # Check error message display
            expect(page.locator('.alert-danger')).to_be_visible()
            
            browser.close()

def test_loading_states_in_all_browsers(browser_types, page_url):
    """Test loading states and animations in all supported browsers."""
    with sync_playwright() as p:
        for browser_type in browser_types:
            browser = getattr(p, browser_type).launch()
            page = browser.new_page()
            
            # Load the page
            page.goto(page_url)
            
            # Click analyze button
            page.click('#analyzeBtn')
            
            # Check loading overlay
            expect(page.locator('.loading-overlay')).to_be_visible()
            expect(page.locator('.spinner-border')).to_be_visible()
            
            # Wait for analysis to complete
            expect(page.locator('.loading-overlay')).to_be_hidden()
            
            browser.close()