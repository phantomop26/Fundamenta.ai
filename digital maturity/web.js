const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const NAV_TIMEOUT = 30_000; // 30 seconds

// pause helper
const delay = ms => new Promise(res => setTimeout(res, ms));

// scroll helper
async function autoScroll(page) {
  await page.evaluate(async () => {
    await new Promise(res => {
      let total = 0, dist = 200;
      const timer = setInterval(() => {
        window.scrollBy(0, dist);
        total += dist;
        if (total >= document.body.scrollHeight) {
          clearInterval(timer);
          res();
        }
      }, 100);
    });
  });
}

// extract addresses from raw text
function extractAddresses(rawText) {
  const lines = rawText.split('\n').map(l => l.trim()).filter(l => l);
  const addrSet = new Set();
  const strictRe = /^\d{1,5}\s+[A-Za-z0-9\s\.]+,\s*[A-Za-z\s]+,\s*[A-Za-z\s\.]+,\s*C\.P\.?\s*\d{5}$/i;
  const noNumRe  = /No\.?\s*\d+/;
  const streetRe = /(Calle|Calzada|Avenida|Av\.?|Boulevard|Bulevar|Blvd\.?|Paseo|Camino|Street|St\.|Road|Rd\.|Lane|Ln\.|Drive|Dr\.)/i;
  const cpMatches = rawText.match(/([A-Za-z0-9\s\.]+,\s*C\.P\.?\s*\d{5})/gi) || [];

  for (let line of lines) {
    if (strictRe.test(line)) {
      addrSet.add(line);
    } else if (noNumRe.test(line) && /[A-Za-z]/.test(line)) {
      addrSet.add(line);
    } else if (/\d/.test(line) && streetRe.test(line)) {
      addrSet.add(line);
    }
  }
  for (let m of cpMatches) {
    addrSet.add(m.trim());
  }

  return Array.from(addrSet);
}

// social regex patterns
const fbRe = /^https?:\/\/(?:www\.|m\.)?(?:facebook\.com|fb\.com)\/(?:(?:pages\/[A-Za-z0-9\.-]+\/\d+)|(?:profile\.php\?id=\d+)|[A-Za-z0-9\.]+)\/?(?:\?.*)?$/i;
const igRe = /^https?:\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/(?:(?:p\/[A-Za-z0-9_-]+)|[A-Za-z0-9._]+)\/?$/i;
const ttRe = /^https?:\/\/(?:www\.)?tiktok\.com\/@?[A-Za-z0-9._-]+\/?$/i;
const liRe = /^https?:\/\/(?:www\.)?linkedin\.com\/(?:in|company)\/[A-Za-z0-9_-]+\/?$/i;

async function scrapePage(url) {
  const browser = await puppeteer.launch({ headless: false, ignoreHTTPSErrors: true });
  const page = await browser.newPage();

  // navigate
  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: NAV_TIMEOUT });
  } catch (err) {
    throw new Error(`Navigation failed (${err.message})`);
  }

  // dismiss fixed/sticky widgets
  await page.evaluate(() => {
    for (let el of document.querySelectorAll('body *')) {
      const s = getComputedStyle(el);
      if ((s.position === 'fixed' || s.position === 'sticky') &&
          (s.bottom !== 'auto' || s.right !== 'auto')) {
        try { el.click(); } catch {}
      }
    }
  });

  // click any “Ver más”
  await page.evaluate(() => {
    for (let el of document.querySelectorAll('a,button')) {
      if (/^ver más$/i.test(el.innerText.trim())) {
        try { el.click(); } catch {}
      }
    }
  });

  await delay(800);
  await autoScroll(page);

  // text extraction
  const rawText = await page.evaluate(() => document.body.innerText.trim());
  const text = rawText.replace(/\s+/g, ' ');

  // emails
  const emails = Array.from(new Set(
    (text.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g) || [])
  ));

  // phones
  const phoneRaw = text.match(/\+?\d[\d\-\s\(\)]{7,}\d/g) || [];
  const phones = Array.from(new Set(
    phoneRaw.map(p => p.trim()).filter(p => p.replace(/\D/g, '').length >= 7)
  ));

  // addresses
  const addresses = extractAddresses(rawText);

  // href links
  const hrefs = await page.evaluate(() =>
    Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
  );
  // text-embedded URLs
  const textUrls = text.match(
    /(?:https?:\/\/)?(?:www\.)?(?:wa\.me|whatsapp\.com|instagram\.com|facebook\.com|tiktok\.com|linkedin\.com|google\.com\/maps|youtube\.com|youtu\.be|x\.com)\/[^\s)]+/gi
  ) || [];

  const allLinks = Array.from(new Set(
    hrefs.concat(textUrls).map(u => u.startsWith('http') ? u : 'https://' + u)
  ));

  // filter social links
  const facebook  = allLinks.filter(u => fbRe.test(u));
  const instagram = allLinks.filter(u => igRe.test(u));
  const tiktok    = allLinks.filter(u => ttRe.test(u));
  const linkedin  = allLinks.filter(u => liRe.test(u));

  await browser.close();
  return { emails, phones, addresses, links: allLinks, social: { facebook, instagram, tiktok, linkedin }, text };
}

(async () => {
  const outputPath = path.resolve(__dirname, 'results.json');
  let results = [];

  // if there's an existing partial results.json, load it
  if (fs.existsSync(outputPath)) {
    try {
      results = JSON.parse(fs.readFileSync(outputPath, 'utf-8'));
    } catch { /* ignore parse errors */ }
  }

  try {
    const filePath = path.resolve(__dirname, 'urls.txt');
    const rawUrls = fs.readFileSync(filePath, 'utf-8')
                      .split(/\r?\n/)
                      .map(l => l.trim())
                      .filter(Boolean);

    for (let raw of rawUrls) {
      // skip if already scraped
      if (results.some(r => r.url === raw || r.url === `https://${raw}` || r.url === `http://${raw}`)) {
        console.log(`🔹 Skipping already-scraped: ${raw}`);
        continue;
      }

      const tries = raw.match(/^https?:\/\//i)
        ? [raw]
        : [`https://${raw}`, `http://${raw}`];

      let success = false, data = null, finalUrl = null, error = null;
      for (let u of tries) {
        console.log(`⏳ Scraping: ${u}`);
        try {
          data = await scrapePage(u);
          success = true;
          finalUrl = u;
          console.log(`✅ Scraped: ${u}`);
          break;
        } catch (err) {
          console.warn(`⚠️  Failed ${u}: ${err.message}`);
          error = err.message;
        }
      }

      const record = {
        url: finalUrl || raw,
        success,
        ...(success ? data : { error })
      };

      results.push(record);

      // save after each scrape
      fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), 'utf-8');
      console.log(`💾 Saved ${results.length} records to ${outputPath}`);
    }

    console.log(`\n🎉 Done! Total scraped: ${results.length}`);
  } catch (err) {
    console.error('Fatal error:', err.message);
    process.exit(1);
  }
})();
