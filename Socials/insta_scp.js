const puppeteer = require('puppeteer');
const fs = require('fs');
const csv = require('csv-parser');

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// Load CSV
async function loadInstagramLinks(filename) {
  return new Promise((resolve, reject) => {
    const results = [];
    fs.createReadStream(filename)
      .pipe(csv())
      .on('data', data => results.push(data))
      .on('end', () => resolve(results))
      .on('error', reject);
  });
}

// Instagram login
async function loginInstagram(page, username, password) {
  await page.goto('https://www.instagram.com/accounts/login/', { waitUntil: 'networkidle2' });

  await page.waitForSelector('input[name="username"]');
  await page.type('input[name="username"]', username, { delay: 100 });
  await page.type('input[name="password"]', password, { delay: 100 });
  await page.click('button[type="submit"]');
  await page.waitForNavigation({ waitUntil: 'networkidle2' });

  // If One-Tap appears, skip it
  if (page.url().includes('/onetap/')) {
    await page.goto('https://www.instagram.com/', { waitUntil: 'networkidle2' });
  }

  // Dismiss "Save Your Login Info?" if shown
  try {
    await page.waitForSelector('button.aOOlW.HoLwm', { timeout: 5000 });
    await page.click('button.aOOlW.HoLwm');
  } catch (e) {
    // no popup
  }
}

// Scrape one profile
async function scrapeInstagramProfile(page, url) {
  try {
    await page.goto(url, { waitUntil: 'networkidle2' });
    await page.waitForSelector('span.x1lliihq.x1plvlek.xryxfnj', { timeout: 5000 });

    const data = await page.evaluate(() => {
      const grabText = sel => {
        const el = document.querySelector(sel);
        return el ? el.innerText.trim() : null;
      };
      const grabAttr = (sel, attr) => {
        const el = document.querySelector(sel);
        return el ? el.getAttribute(attr) : null;
      };
      const statsEls = Array.from(document.querySelectorAll('section.xc3tme8 span.html-span.xdj266r')).slice(0,3);
      const [posts, followers, following] = statsEls.map(el => el.innerText.trim());

      return {
        name: grabText('span.x1lliihq.x193iq5w.x6ikm8r'),
        account_category: grabText('.x9f619 ._ap3a._aaco._aacu._aacy._aad6._aade'),
        profile_picture_url: grabAttr('span[role="link"] img', 'src'),
        number_of_posts: posts || null,
        number_of_followers: followers || null,
        number_of_following: following || null,
        bio: grabText('span._ap3a._aaco._aacu._aacx._aad7._aade'),
        threads_username: grabText('span.x1lliihq.x193iq5w'),
        links: grabText('div._ap3a._aaco._aacw._aacz._aada._aade')
      };
    });

    return data;
  } catch (err) {
    console.error(`Error scraping ${url}:`, err.message);
    return {
      error: err.message
    };
  }
}

(async () => {
  const instagramEntries = await loadInstagramLinks('insta.csv');
  console.log(`Loaded ${instagramEntries.length} entries`);

  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // Log in once
  const USERNAME = 'buddynyu';
  const PASSWORD = 'Sahil@1082';
  await loginInstagram(page, USERNAME, PASSWORD);

  const results = [];
  for (const entry of instagramEntries) {
    const url = entry.instagram_link || entry.url;
    console.log(`Scraping ${url}`);
    const profilePage = await browser.newPage();
    const data = await scrapeInstagramProfile(profilePage, url);
    results.push({ source: entry.url, profile: url, ...data });
    await profilePage.close();
    await sleep(2000 + Math.random() * 2000);
  }

  await browser.close();

  fs.writeFileSync(
    'scraped_instagram_data.json',
    JSON.stringify(results, null, 2)
  );
  console.log('Scraping complete, data saved to scraped_instagram_data.json');
})();
