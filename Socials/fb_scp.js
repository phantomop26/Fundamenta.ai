// const fs = require('fs');
// const csv = require('csv-parser');
// const puppeteer = require('puppeteer-extra');
// const StealthPlugin = require('puppeteer-extra-plugin-stealth');

// puppeteer.use(StealthPlugin());

// const urls = [];

// fs.createReadStream('fb.csv')
//   .pipe(csv())
//   .on('data', (row) => {
//     urls.push(row.website);
//   })
//   .on('end', async () => {
//     const browser = await puppeteer.launch({ headless: 'new' });
//     const page = await browser.newPage();
//     const results = [];

//     for (let url of urls) {
//       try {
//         await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

//         // Repeatedly remove login popup if it shows up
//         await page.evaluate(() => {
//           const interval = setInterval(() => {
//             const blockers = document.querySelectorAll('div.__fb-light-mode.x1n2onr6.xzkaem6');
//             blockers.forEach(el => el.remove());
//             if (blockers.length === 0) clearInterval(interval);
//           }, 500);
//         });

//         await new Promise(resolve => setTimeout(resolve, 3000));


//         const data = await page.evaluate(() => {
//           const result = {};

//           // Get name from <svg aria-label="">
//           const svg = document.querySelector('svg[aria-label]');
//           if (svg) result.name = svg.getAttribute('aria-label');

//           // Get profile image from <image xlink:href="">
//         // const imageTag = document.querySelector('svg image');
//         // const imageURL = imageTag ? imageTag.getAttributeNS('http://www.w3.org/1999/xlink', 'href') : null;

//         //   if (image) result.profileImage = image.getAttribute('xlink:href');

//           // Get all span text contents that match the given class pattern
//           const spans = Array.from(document.querySelectorAll('span.x193iq5w')).map(el => el.innerText.trim());
//           result.details = spans.filter(Boolean);

//           return result;
//         });

//         results.push({ url, ...data });
//         console.log(`✅ Scraped: ${url}`);
//       } catch (err) {
//         console.error(`❌ Failed: ${url}`, err.message);
//         results.push({ url, error: err.message });
//       }
//     }

//     await browser.close();
//     fs.writeFileSync('facebook_results.json', JSON.stringify(results, null, 2));
//     console.log('✅ Done. Data saved to facebook_results.json');
//   });













const fs = require('fs');
const csv = require('csv-parser');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

const urls = [];

fs.createReadStream('fb.csv')
  .pipe(csv())
  .on('data', (row) => {
    urls.push(row.website);
  })
  .on('end', async () => {
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();
    const results = [];

    for (let url of urls) {
      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

        // Repeatedly remove login popup if it shows up
        await page.evaluate(() => {
          const interval = setInterval(() => {
            const blockers = document.querySelectorAll('div.__fb-light-mode.x1n2onr6.xzkaem6');
            blockers.forEach(el => el.remove());
            if (blockers.length === 0) clearInterval(interval);
          }, 500);
        });

        await new Promise(resolve => setTimeout(resolve, 3000));

        const data = await page.evaluate(() => {
          const result = {};

          // Get name from <svg aria-label="">
          const svg = document.querySelector('svg[aria-label]');
          if (svg) result.name = svg.getAttribute('aria-label');

          // Get profile image URL from xlink:href
          const imageTag = document.querySelector('svg image');
          if (imageTag) {
            result.profileImage = imageTag.getAttributeNS('http://www.w3.org/1999/xlink', 'href');
          }

          // Likes & Followers
          const likesEl = document.querySelector('a[href$="friends_likes/"]');
          const followersEl = document.querySelector('a[href$="followers/"]');
          if (likesEl) result.likes = likesEl.innerText.trim();
          if (followersEl) result.followers = followersEl.innerText.trim();

          // Extract span text content
          const spans = Array.from(document.querySelectorAll('span.x193iq5w')).map(el => el.innerText.trim());

          for (let i = 0; i < spans.length; i++) {
            const text = spans[i];

            if (text.includes('Somos')) {
              result.about = text;
            } else if (text.startsWith('+52')) {
              result.phone = text;
            } else if (text.includes('@')) {
              result.email = text;
            } else if (text.includes('Price Range')) {
              result.priceRange = text.replace('Price Range · ', '');
            } else if (text.includes('recommend') && text.includes('%')) {
              result.recommendation = text;
            } else if (text.startsWith('Page ·')) {
              result.category = text.replace('Page · ', '');
            } else if (/Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i.test(text)) {
              result.recentPost = {
                date: text,
                content: spans[i + 1] || '',
                likes: spans[i + 2] || ''
              };
              break;
            }
          }

          return result;
        });

        results.push({ url, ...data });
        console.log(`✅ Scraped: ${url}`);
      } catch (err) {
        console.error(`❌ Failed: ${url}`, err.message);
        results.push({ url, error: err.message });
      }
    }

    await browser.close();
    fs.writeFileSync('facebook_results.json', JSON.stringify(results, null, 2));
    console.log('✅ Done. Data saved to facebook_results.json');
  });
