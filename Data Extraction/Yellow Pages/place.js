const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // Define the categories you want to scrape
  const categories = [];

  const baseUrl = 'https://www.yellowpages.com/manhattan-ny';

  for (const category of categories) {
    // Convert category name to lowercase and replace spaces with hyphens
    const formattedCategory = category.toLowerCase().replace(/\s+/g, '-');
    console.log(`Scraping category: ${category} (URL formatted as: ${formattedCategory})`);

    let categoryListings = [];

    // Navigate to the first page of the category to get total results
    await page.goto(`${baseUrl}/${formattedCategory}?page=1`, { waitUntil: 'networkidle2' });
    await page.waitForSelector('span.showing-count');

    // Get the total count of results for the current category
    const totalResults = await page.evaluate(() => {
      const resultText = document.querySelector('span.showing-count')?.innerText;
      const match = resultText?.match(/of (\d+)/);
      return match ? parseInt(match[1]) : null;
    });

    if (!totalResults) {
      console.log(`Could not determine the total number of results for category ${category}.`);
      continue;
    }

    // Calculate the number of pages
    const resultsPerPage = 30;
    const totalPages = Math.ceil(totalResults / resultsPerPage);
    console.log(`Total results: ${totalResults}, Total pages: ${totalPages} for category ${category}`);

    // Delay function as a replacement for page.waitForTimeout
    const delay = (time) => new Promise(resolve => setTimeout(resolve, time));

    // Loop through each page within the category
    for (let i = 1; i <= totalPages; i++) {
      console.log(`Scraping page ${i} of ${totalPages} in category ${category}`);
      await page.goto(`${baseUrl}/${formattedCategory}?page=${i}`, { waitUntil: 'networkidle2' });
      await page.waitForSelector('a.business-name');

      // Scrape data on the current page
      const listings = await page.evaluate(() => {
        const pageListings = [];
        
        const businessElements = document.querySelectorAll('.result');
        businessElements.forEach((element) => {
          const nameElement = element.querySelector('a.business-name');
          const categoriesElement = element.querySelectorAll('.categories a');
          const linkElements = element.querySelectorAll('.links a');
          const phoneElement = element.querySelector('.phone');
          const addressElement = element.querySelector('.adr');
          const badgesElement = element.querySelector('.badges');

          const name = nameElement ? nameElement.innerText.trim() : null;
          const categories = Array.from(categoriesElement).map(cat => cat.innerText.trim());
          const links = Array.from(linkElements).map(link => ({
            text: link.innerText.trim(),
            href: link.href
          }));
          const badges = badgesElement ? badgesElement.innerText.trim() : null;
          const phone = phoneElement ? phoneElement.innerText.trim() : null;
          const address = addressElement ? addressElement.innerText.trim() : null;

          pageListings.push({
            name,
            categories,
            links,
            badges,
            phone,
            address
          });
        });

        return pageListings;
      });

      categoryListings = categoryListings.concat(listings);

      // Delay between pages to avoid overloading the server
      await delay(1000);
    }

    // Save the results for each category to a separate JSON file
    const fileName = `yellowpages_${formattedCategory}.json`;
    fs.writeFileSync(fileName, JSON.stringify(categoryListings, null, 2));

    console.log(`Data for category ${category} saved to ${fileName}`);
  }

  console.log('Scraping complete.');
  await browser.close();
})();