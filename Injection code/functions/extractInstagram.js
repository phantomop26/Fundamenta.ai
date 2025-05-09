const puppeteer = require('puppeteer');
const fs = require('fs');
const csv = require('csv-parser');
const { parse } = require('url');

/**
 * Initialize a Puppeteer browser instance with stealth settings
 * @param {boolean} headless - Whether to run in headless mode
 * @returns {Promise<Browser>} - Puppeteer browser instance
 */
async function initializeBrowser(headless = false) {
  console.log('Initializing browser...');
  
  // Use more realistic window dimensions
  const width = 1366;
  const height = 768;
  
  const browser = await puppeteer.launch({
    headless: headless ? 'new' : false,
    args: [
      '--no-sandbox',
      '--disable-dev-shm-usage',
      `--window-size=${width},${height}`,
      '--disable-blink-features=AutomationControlled', // Prevent detection via automation flags
      '--disable-features=IsolateOrigins,site-per-process', // Disable site isolation
      '--disable-web-security', // Allow cross-domain cookies
      '--disable-features=site-per-process',
      '--lang=en-US,en', // Set language
      '--user-data-dir=./user-data', // Use persistent session data
    ],
    ignoreDefaultArgs: ['--enable-automation'], // Hide automation flag
    defaultViewport: { width, height }
  });
  
  const page = await browser.newPage();
  
  // Pass WebDriver test
  await page.evaluateOnNewDocument(() => {
    // Overwrite the 'navigator.webdriver' property to prevent detection
    Object.defineProperty(navigator, 'webdriver', {
      get: () => false,
    });
    
    // Overwrite chrome properties
    window.chrome = {
      runtime: {},
    };
    
    // Overwrite permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
      parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
    );
    
    // Prevent detection via plugins length
    Object.defineProperty(navigator, 'plugins', {
      get: () => [
        {
          0: {
            type: "application/x-google-chrome-pdf",
            suffixes: "pdf",
            description: "Portable Document Format",
            enabledPlugin: Plugin,
          },
          description: "Portable Document Format",
          filename: "internal-pdf-viewer",
          length: 1,
          name: "Chrome PDF Plugin",
        },
        {
          0: {
            type: "application/pdf",
            suffixes: "pdf",
            description: "",
            enabledPlugin: Plugin,
          },
          description: "",
          filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
          length: 1,
          name: "Chrome PDF Viewer",
        },
        {
          0: {
            type: "application/x-nacl",
            suffixes: "",
            description: "Native Client Executable",
            enabledPlugin: Plugin,
          },
          1: {
            type: "application/x-pnacl",
            suffixes: "",
            description: "Portable Native Client Executable",
            enabledPlugin: Plugin,
          },
          description: "",
          filename: "internal-nacl-plugin",
          length: 2,
          name: "Native Client",
        },
      ],
    });
    
    // Pass Captcha browser tests
    window.navigator.connection = {
      rtt: 100,
      downlink: 10,
      effectiveType: "4g",
    };
    
    // Prevent fingerprinting via canvas
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
      if (type === 'image/png' && this.width === 220 && this.height === 30) {
        return originalToDataURL.apply(this, [type]);
      }
      return originalToDataURL.apply(this, arguments);
    };
  });
  
  // Random realistic user agent
  const userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
  ];
  
  const randomUserAgent = userAgents[Math.floor(Math.random() * userAgents.length)];
  await page.setUserAgent(randomUserAgent);
  console.log('Using User-Agent:', randomUserAgent);
  
  // Set extra HTTP headers to appear more like a real browser
  await page.setExtraHTTPHeaders({
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br'
  });
  
  return { browser, page };
}

/**
 * Simulate human-like interactions on the page
 * @param {Page} page - Puppeteer page instance
 */
async function simulateHumanBehavior(page) {
  const viewportHeight = page.viewport().height;
  
  // Random scroll behavior
  await page.mouse.move(Math.random() * 100, Math.random() * 100);
  
  // Scroll down the page at variable speeds with pauses
  const scrollPoints = Math.floor(Math.random() * 3) + 2; // 2-4 scroll points
  const maxScroll = viewportHeight * 3; 
  
  for (let i = 0; i < scrollPoints; i++) {
    const scrollAmount = (maxScroll / scrollPoints) * (i + 1);
    
    // Variable scroll speed
    await page.evaluate((scrollPos) => {
      return new Promise((resolve) => {
        let start = null;
        const duration = Math.random() * 1000 + 500; // 500-1500ms
        const initialPosition = window.pageYOffset;
        
        function step(timestamp) {
          if (!start) start = timestamp;
          const progress = (timestamp - start) / duration;
          
          if (progress < 1) {
            const easing = progress < 0.5 
              ? 2 * progress * progress 
              : -1 + (4 - 2 * progress) * progress; // Ease in-out quadratic
            
            window.scrollTo(0, initialPosition + (scrollPos - initialPosition) * easing);
            window.requestAnimationFrame(step);
          } else {
            window.scrollTo(0, scrollPos);
            resolve();
          }
        }
        
        window.requestAnimationFrame(step);
      });
    }, scrollAmount);
    
    // Pause between scrolls
    await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));
  }
  
  // Small mouse movements
  for (let i = 0; i < 5; i++) {
    await page.mouse.move(
      100 + Math.floor(Math.random() * 200),
      100 + Math.floor(Math.random() * 200),
      { steps: 10 }
    );
    await new Promise(resolve => setTimeout(resolve, Math.random() * 300 + 50));
  }
}

/**
 * Handle Google's CAPTCHA if it appears
 * @param {Page} page - Puppeteer page instance
 * @returns {boolean} - Whether a CAPTCHA was detected and handled
 */
async function handleCaptcha(page) {
  // Check for typical CAPTCHA indicators
  const captchaSelectors = [
    'iframe[src*="recaptcha"]',
    'textarea#g-recaptcha-response',
    'div.g-recaptcha',
    '#captcha',
    'img[src*="captcha"]',
    '.recaptcha-checkbox-border',
    'h1:contains("Unusual traffic")',
    'body:contains("unusual traffic")'
  ];
  
  for (const selector of captchaSelectors) {
    const captchaElement = await page.$(selector);
    if (captchaElement) {
      console.log('CAPTCHA detected! Taking screenshot and pausing...');
      await page.screenshot({ path: 'captcha-detected.png' });
      
      // Wait for manual intervention - will need to solve the CAPTCHA manually
      console.log('Please solve the CAPTCHA in the browser window');
      console.log('Waiting 30 seconds for manual CAPTCHA solution...');
      await new Promise(resolve => setTimeout(resolve, 30000));
      
      return true;
    }
  }
  
  // Also check for text indicating bot detection
  const pageContent = await page.content();
  const botDetectionTerms = [
    'unusual traffic',
    'automated queries',
    'detect that you are a bot',
    'robot',
    'captcha',
    'security check',
    'verify you are a human'
  ];
  
  for (const term of botDetectionTerms) {
    if (pageContent.toLowerCase().includes(term.toLowerCase())) {
      console.log(`Bot detection term found: "${term}"`);
      await page.screenshot({ path: 'bot-detection.png' });
      
      console.log('Please complete any verification in the browser window');
      console.log('Waiting 30 seconds for manual intervention...');
      await new Promise(resolve => setTimeout(resolve, 30000));
      
      return true;
    }
  }
  
  return false;
}

/**
 * Search for a name and address by directly going to Google search URL
 * @param {Page} page - Puppeteer page instance
 * @param {string} name - Business name
 * @param {string} address - Business address
 * @param {number} waitTime - Time to wait for elements in seconds
 * @returns {Promise<string[]>} - Array of extracted links
 */
async function searchNameAddress(page, name, address, waitTime = 20, maxRetries = 3) {
  // Format the search query with quotes around name and address
  const searchQuery = `"${name}" "${address}"`;
  
  // Properly encode the search query for URL
  const encodedQuery = encodeURIComponent(searchQuery);
  
  // Add randomized parameters to appear more natural
  const searchParams = [
    `q=${encodedQuery}`,
    `hl=en`,
    `gl=us`,
    `source=hp`,
    `ei=${Math.random().toString(36).substring(2, 15)}`,
    `iflsig=${Math.random().toString(36).substring(2, 15)}`
  ];
  
  // Randomize the order and presence of some parameters
  if (Math.random() > 0.5) searchParams.push(`ved=${Math.random().toString(36).substring(2, 15)}`);
  if (Math.random() > 0.5) searchParams.push(`uact=5`);
  if (Math.random() > 0.3) searchParams.push(`oq=${encodedQuery}`);
  
  const searchUrl = `https://www.google.com/search?${searchParams.join('&')}`;
  
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      console.log(`Attempt ${retries + 1} for ${name}, ${address}`);
      console.log(`Navigating to search URL (abbreviated): https://www.google.com/search?q=${encodedQuery.substring(0, 30)}...`);
      
      // Navigate directly to the search URL
      await page.goto(searchUrl, { 
        timeout: 30000,
        waitUntil: 'networkidle2'
      });
      
      // Add a random delay before any interactions
      const randomDelay = Math.floor(Math.random() * 3000) + 2000;
      await new Promise(resolve => setTimeout(resolve, randomDelay));
      
      // Check for and handle CAPTCHA
      const captchaDetected = await handleCaptcha(page);
      if (captchaDetected) {
        console.log('Continuing after CAPTCHA handling...');
      }
      
      // Handle cookie consent if it appears
      try {
        const cookieSelectors = [
          'button:has-text("Accept all")', 
          'button:has-text("I agree")',
          'button[id*="consent"]',
          'button[aria-label*="consent"]',
          'div[role="dialog"] button'
        ];
        
        for (const selector of cookieSelectors) {
          const cookieButton = await page.$(selector);
          if (cookieButton) {
            console.log(`Found cookie consent button: ${selector}`);
            
            // Wait a natural amount of time before clicking
            await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));
            
            await cookieButton.click();
            console.log('Clicked cookie consent button');
            await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 1000));
            break;
          }
        }
      } catch (err) {
        console.log('No cookie banner detected or error handling it:', err.message);
      }
      
      // Simulate human-like behavior on the page
      await simulateHumanBehavior(page);
      
      // Take a screenshot after searching
      await page.screenshot({ path: `search-result-${name.replace(/[^a-z0-9]/gi, '_').substring(0, 20)}.png` });
    
      // Wait for results to load with randomized delay
      await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 3000));
      
      // Find all links using multiple methods for redundancy
      const results = await page.evaluate(() => {
        const links = new Set();
        
        // Method 1: g-link elements (common in Google)
        document.querySelectorAll('g-link a').forEach(a => {
          if (a.href) links.add(a.href);
        });
        
        // Method 2: Standard result links
        document.querySelectorAll('.g .yuRUbf a, .g .rc a, .tF2Cxc a').forEach(a => {
          if (a.href) links.add(a.href);
        });
        
        // Method 3: All links that aren't navigation/Google internal
        document.querySelectorAll('a').forEach(a => {
          if (a.href && 
              !a.href.startsWith('https://www.google.com/') && 
              !a.href.includes('webcache.googleusercontent') &&
              !a.href.includes('/search?') &&
              a.href !== '#') {
            links.add(a.href);
          }
        });
        
        return Array.from(links);
      });
      
      console.log(`Found ${results.length} raw links`);
      
      // Clean the URLs (remove Google redirects if present)
      const cleanedResults = results.map(href => {
        if (href.includes('google.com/url?')) {
          try {
            const parsedUrl = parse(href);
            const params = new URLSearchParams(parsedUrl.query);
            if (params.has('url') || params.has('q')) {
              return params.get('url') || params.get('q');
            }
          } catch (e) {
            console.error('Error parsing URL:', e);
          }
        }
        return href;
      }).filter(url => url && !url.includes('google.com')); // Filter out any remaining Google URLs
      
      console.log(`Extracted ${cleanedResults.length} cleaned links`);
      
      // Final random delay before returning results
      await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));
      
      return cleanedResults;
    } catch (err) {
      console.error(`Error searching for ${name}, ${address} (attempt ${retries + 1}): ${err.message}`);
      
      // Take a screenshot of the error state
      await page.screenshot({ path: `error-search-${retries}.png` });
      
      retries++;
      
      if (retries >= maxRetries) {
        console.error(`Maximum retries reached for ${name}, ${address}`);
        return [];
      }
      
      // Wait before retrying with variable delay
      const retryDelay = Math.floor(Math.random() * 5000) + 10000; // 10-15 seconds
      console.log(`Waiting ${retryDelay/1000} seconds before retry...`);
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }
  }
  
  // If we reach here, all retries failed
  return [];
}

/**
 * Close the Puppeteer browser instance
 * @param {Browser} browser - Puppeteer browser instance to close
 */
async function closeBrowser(browser) {
  try {
    await browser.close();
  } catch (err) {
    console.error(`Error closing browser: ${err.message}`);
  }
}

/**
 * Read CSV file and return array of objects
 * @param {string} filePath - Path to the CSV file
 * @returns {Promise<Array>} - Array of objects representing the CSV rows
 */
function readCSV(filePath) {
  return new Promise((resolve, reject) => {
    const results = [];
    
    fs.createReadStream(filePath)
      .pipe(csv({ headers: [
        'businessID', 'gmapsURL', 'address', 'category', 
        'categoryGeneral', 'name', 'phone', 'website', 
        'instagram', 'blank1', 'blank2', 'blank3'
      ], skipLines: 0 }))
      .on('data', (data) => results.push(data))
      .on('end', () => resolve(results))
      .on('error', (err) => reject(err));
  });
}

/**
 * Main function to process the CSV and search for businesses
 */
async function main() {
  // Initialize the browser
  const { browser, page } = await initializeBrowser(false);
  
  try {
    // Read the CSV file
    const data = await readCSV('instas.csv');
    
    // Process each row with variable delays between searches
    const results = {};
    for (const row of data) {
      try {
        console.log(`Searching for: ${row.name}, ${row.address}`);
        
        // Skip empty names or addresses
        if (!row.name || !row.address) {
          console.log(`Skipping business ID ${row.businessID} - missing name or address`);
          results[row.businessID] = [];
          continue;
        }
        
        const foundLinks = await searchNameAddress(page, row.name, row.address);
        results[row.businessID] = foundLinks;
        console.log(`Found ${foundLinks.length} links for ${row.name}`);
        
        // Save intermediate results after each successful search
        fs.writeFileSync(
          `search_results_partial_${Object.keys(results).length}.json`, 
          JSON.stringify(results, null, 2)
        );
        
        // Variable delay between searches to avoid detection
        const delay = Math.floor(Math.random() * 10000) + 10000; // 10-20 seconds
        console.log(`Waiting ${delay/1000} seconds before next search...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } catch (rowError) {
        console.error(`Error processing row ${row.businessID}:`, rowError);
        results[row.businessID] = [];
        
        // Extended wait after error
        const errorDelay = Math.floor(Math.random() * 10000) + 15000; // 15-25 seconds
        console.log(`Error occurred. Waiting ${errorDelay/1000} seconds before continuing...`);
        await new Promise(resolve => setTimeout(resolve, errorDelay));
      }
    }
    
    // Write results to a JSON file
    fs.writeFileSync('search_results.json', JSON.stringify(results, null, 2));
    console.log(`Completed searches for ${Object.keys(results).length} businesses`);
  } catch (err) {
    console.error('Error in main process:', err.message);
  } finally {
    // Make sure to close the browser when done
    await closeBrowser(browser);
  }
}

// Run the main function
main().catch(err => {
  console.error('Unhandled error:', err);
  process.exit(1);
});