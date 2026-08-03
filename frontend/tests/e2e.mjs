import { chromium } from 'playwright';

(async () => {
  console.log('Starting frontend E2E test...');
  
  // Launch browser
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  const FRONTEND_URL = 'http://localhost:5173'; // default vite port

  try {
    console.log(`Navigating to ${FRONTEND_URL}/dashboard (Unauthenticated)...`);
    await page.goto(`${FRONTEND_URL}/dashboard`);
    
    // Wait for redirect to /login
    await page.waitForURL('**/login', { timeout: 5000 });
    console.log('✅ Successfully redirected to /login');

    // Verify Login page renders the correct button
    console.log('Verifying Login page content...');
    
    // Check for Continue with Google text
    const loginTextVisible = await page.isVisible('text="Continue with Google"');
    if (loginTextVisible) {
      console.log('✅ "Continue with Google" button is visible');
    } else {
      throw new Error('"Continue with Google" button not found on login page');
    }
    
    console.log('All frontend E2E tests passed successfully!');

  } catch (err) {
    console.error('❌ Frontend E2E test failed:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
