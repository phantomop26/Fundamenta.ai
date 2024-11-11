const puppeteer = require('puppeteer');
const fs = require('fs');
const csv = require('csv-parser');
const results = [];

function readCSV(filePath) {
  return new Promise((resolve, reject) => {
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (data) => results.push(data.user_links))
      .on('end', () => resolve(results))
      .on('error', (error) => reject(error));
  });
}

async function scrapeUserProfile(page) {
  const profilePicElement = await page.$('div.Gmmhvf img');
  const userTagElement = await page.$('span.FNyx3.F8kQwb');
  const reviewPointsElement = await page.$('span.VEEl9c');
  const userNameElement = await page.$('h1.geAzIe');
  const contrielement = await page.$('span.FNyx3');
  const contributions = contrielement ? await page.evaluate(span => span.textContent, contrielement) : null;
  const profilePicUrl = profilePicElement ? await page.evaluate(img => img.src, profilePicElement) : null;
  const userTag = userTagElement ? await page.evaluate(span => span.textContent, userTagElement) : null;
  const reviewPoints = reviewPointsElement ? await page.evaluate(span => span.textContent, reviewPointsElement) : null;
  const userName = userNameElement ? await page.evaluate(h1 => h1.textContent, userNameElement) : null;
  const userTagOrContributions = contributions ? contributions : userTag;
  return {
    name: userName || 'Unknown',
    profilePicUrl,
    reviewPoints,
    userTagOrContributions,
  };
}

async function infiniteScroll(page, selector) {
  const delay = (time) => new Promise(resolve => setTimeout(resolve, time));
  let lastHeight = 0;
  let retryCounter = 0;
  const maxRetries = 3;
  const maxScrollAttempts = 30;
  let scrollCount = 0;

  while (scrollCount < maxScrollAttempts) {
    const currentHeight = await page.evaluate((scrollSelector) => {
      const scrollableSection = document.querySelector(scrollSelector);
      if (scrollableSection) {
        scrollableSection.scrollBy(0, scrollableSection.scrollHeight);
        return scrollableSection.scrollHeight;
      }
      return 0;
    }, selector);

    if (currentHeight > lastHeight) {
      lastHeight = currentHeight;
      retryCounter = 0;
    } else {
      retryCounter += 1;
      if (retryCounter >= maxRetries) break;
    }

    await delay(5000); // Wait for reviews to load after scroll
    scrollCount++;
  }
}

async function clickAllMoreButtons(page) {
  const delay = (time) => new Promise(resolve => setTimeout(resolve, time));
  let moreButtons = await page.$$('button.w8nwRe.kyuRq[aria-label="See more"]');
  while (moreButtons.length > 0) {
    for (const button of moreButtons) {
      try {
        await button.click();
        await delay(500);  // Adjust delay for expanding reviews
      } catch (error) {
        console.error('Error clicking More button:', error);
      }
    }
    moreButtons = await page.$$('button.w8nwRe.kyuRq[aria-label="See more"]');
  }
}

async function scrapeReviews(page, reviewContainerSelector, reviewItemSelector) {
  // Ensure scroll happens within the review container
  await infiniteScroll(page, reviewContainerSelector);  // Scroll to the bottom of the review section
  await clickAllMoreButtons(page);  // Expand individual reviews

  const reviews = await page.$$eval(reviewItemSelector, reviewElements => {
    return reviewElements.map(reviewElement => {
      const name = reviewElement.querySelector('div.d4r55.YJxk2d')?.textContent || null;
      const address = reviewElement.querySelector('div.RfnDt.xJVozb')?.textContent || null;
      const ratingElement = reviewElement.querySelector('span.kvMYJc[aria-label]');
      const rating = ratingElement ? ratingElement.getAttribute('aria-label') : null;
      const time = reviewElement.querySelector('span.rsqaWe')?.textContent || null;

      const reviewTextBox = reviewElement.querySelector('div[jslog="127691"]');
      const textReview = reviewElement.querySelector('span.wiI7pd')?.textContent || null;

      const additionalDetails = reviewTextBox
        ? Array.from(reviewTextBox.querySelectorAll('span.RfDO5c span'))
          .map(detail => detail.textContent.trim())
          .join(', ')
        : '';

      const texttag = (additionalDetails ? ' | ' + additionalDetails : null);

      const photoElements = reviewElement.querySelectorAll('button.Tya61d');
      const photos = Array.from(photoElements).map(photo => {
        const backgroundImage = photo.style.backgroundImage;
        return backgroundImage.replace('url("', '').replace('")', '');
      });

      const ownerResponseElement = reviewElement.querySelector('div.CDe7pd');
      let ownerResponse = null;
      if (ownerResponseElement) {
        const responseDate = reviewElement.querySelector('span.DZSIDd')?.textContent || null;
        const responseText = reviewElement.querySelector('div.wiI7pd')?.textContent || null;
        ownerResponse = {
          date: responseDate,
          text: responseText
        };
      }

      return { name, address, rating, time, textReview, texttag, photos, ownerResponse };
    });
  });

  return reviews;
}

async function scrapeMultipleUrls(urls) {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  for (const url of urls) {
    let retries = 3;
    while (retries > 0) {
      try {
        await page.goto(url, { waitUntil: 'networkidle2' });
        await page.waitForNavigation({ waitUntil: 'load', timeout: 30000 });

        const profile = await scrapeUserProfile(page);
        profile.link = url;

        // Update the selector for the reviews container and review items
        const reviewsContainerSelector = '.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde';
        const reviewItemSelector = '.jftiEf.fontBodyMedium';

        const reviews = await scrapeReviews(page, reviewsContainerSelector, reviewItemSelector);

        const data = {
          profile,
          reviews
        };

        const fileName = `reviews_${profile.name.replace(/\s/g, '_')}.json`;
        fs.writeFileSync(fileName, JSON.stringify(data, null, 2));
        console.log(`Saved reviews to ${fileName}`);
        break; // Success, break retry loop
      } catch (error) {
        console.error(`Error scraping URL ${url}:`, error);
        if (error.message.includes('detached Frame')) {
          retries -= 1;
          console.log(`Retrying... (${3 - retries} attempts left)`);
          await page.waitFor(5000); // Corrected delay before retrying
        } else {
          break; // Other errors, break retry loop
        }
      }
    }
  }

  await browser.close();
}

(async () => {
  try {
    const urls = await readCSV('users.csv'); 
    await scrapeMultipleUrls(urls); 
  } catch (error) {
    console.error('Error:', error);
  }
})();