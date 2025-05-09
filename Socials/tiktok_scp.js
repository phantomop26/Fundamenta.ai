// tiktok_scraper.js
const fs = require('fs');
const csv = require('csv-parser');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

async function readCsv(filePath) {
  return new Promise((resolve, reject) => {
    const urls = [];
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', row => {
        if (row.tiktok_links) urls.push(row.tiktok_links.trim());
      })
      .on('end', () => resolve(urls))
      .on('error', reject);
  });
}

(async () => {
  const urls = await readCsv('tiktok.csv');
  if (!urls.length) {
    console.error('No URLs found in tiktok.csv under header "tiktok_links".');
    process.exit(1);
  }

  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  const results = [];

  for (const url of urls) {
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForSelector('h1[data-e2e="user-title"]', { timeout: 10000 });
      await page.waitForSelector('strong[data-e2e="followers-count"]', { timeout: 10000 });
      // tiny delay to ensure counts are updated
      await page.waitForTimeout(500);

      const data = await page.evaluate(() => {
        const result = {};

        // Username & account name
        const userEl = document.querySelector('h1[data-e2e="user-title"]');
        if (userEl) result.username = userEl.innerText.trim();

        const acctEl = document.querySelector('h2[data-e2e="user-subtitle"]');
        if (acctEl) result.accountName = acctEl.innerText.trim();

        // Bio
        const bioEl = document.querySelector('h2[data-e2e="user-bio"]');
        if (bioEl) result.bio = bioEl.innerText.trim();

        // Profile image (SVG or <img> fallback)
        let imgUrl = null;
        const svgImage = document.querySelector('svg image');
        if (svgImage) {
          imgUrl = svgImage.getAttributeNS('http://www.w3.org/1999/xlink', 'href');
        } else {
          const avatarImg = document.querySelector('div[data-e2e="user-avatar"] img');
          if (avatarImg) imgUrl = avatarImg.src;
        }
        if (imgUrl) result.profileImage = imgUrl;

        // Stats
        const followingCount = document.querySelector('strong[data-e2e="following-count"]');
        const followersCount = document.querySelector('strong[data-e2e="followers-count"]');
        const likesCount     = document.querySelector('strong[data-e2e="likes-count"]');
        if (followingCount) result.following = followingCount.innerText.trim();
        if (followersCount) result.followers = followersCount.innerText.trim();
        if (likesCount)     result.likes     = likesCount.innerText.trim();

        return result;
      });

      data.url = url;
      console.log(`✅ Scraped ${url}:`, {
        username: data.username,
        followers: data.followers,
      });
      results.push(data);

    } catch (err) {
      console.error(`❌ Error scraping ${url}: ${err.message}`);
    }
  }

  await browser.close();
  fs.writeFileSync('tiktok_results.json', JSON.stringify(results, null, 2), 'utf-8');
  console.log('\nAll done! Results written to tiktok_results.json');
})();
