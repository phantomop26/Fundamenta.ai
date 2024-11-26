const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}

async function scrapeBusinessData(jsonFolders) {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    for (const folder of jsonFolders) {
        const files = fs.readdirSync(folder).filter(file => file.endsWith('.json'));

        for (const file of files) {
            const filePath = path.join(folder, file);
            const folderName = path.basename(file, '.json');
            const outputFolder = path.join(folder, folderName);

            if (!fs.existsSync(outputFolder)) {
                fs.mkdirSync(outputFolder);
            }

            let businesses;
            try {
                const fileContent = fs.readFileSync(filePath, 'utf-8');
                businesses = JSON.parse(fileContent);
            } catch (error) {
                console.error(`Failed to parse JSON file ${file}:`, error);
                continue;
            }

            for (const business of businesses) {
                const names = [
                    business.name,
                    `${business.name}, New York`
                ];

                let searchSuccessful = false;

                for (const name of names) {
                    console.log(`Searching for: ${name}`);
                    try {
                        await page.goto('https://www.google.com/maps', { waitUntil: 'networkidle2', timeout: 60000 });
                        await page.waitForSelector('input#searchboxinput', { timeout: 10000 });
                        await page.type('input#searchboxinput', name);
                        await page.waitForSelector('button#searchbox-searchbutton', { timeout: 10000 });
                        await page.click('button#searchbox-searchbutton');
                        await page.waitForSelector('.a5H0ec', { timeout: 10000 });

                        searchSuccessful = true;
                        break;
                    } catch (error) {
                        console.error(`Error searching for ${name}:`, error);
                        continue;
                    }
                }

                if (!searchSuccessful) {
                    console.log(`Failed to find results for ${business.name}. Skipping.`);
                    continue;
                }

                const placeDetails = await page.evaluate(() => {
                    const name = document.querySelector('.DUwDvf.lfPIob')?.innerText || null;
                    const category = document.querySelector('.DkEaL')?.innerText || null;
                    const address = document.querySelector('.Io6YTe.fontBodyMedium.kR99db.fdkmkc')?.innerText || null;
                    const Details = [...document.querySelectorAll('.RcCsl.fVHpi.w4vB1d.NOE9ve.M0S7ae')]
                        .map(el => el.innerText.replace(/\n/g, '').trim());
                    const ratingElement = document.querySelector('div.F7nice span[aria-hidden="true"]');
                    const rating = ratingElement ? ratingElement.innerText : null;
                    const reviewCountElement = document.querySelector('.F7nice span[aria-label*="reviews"]');
                    const reviewCount = reviewCountElement ? reviewCountElement.getAttribute('aria-label').match(/\d{1,3}(,\d{3})*/g)[0] : null;
                    const priceElement = document.querySelector('.mgr77e');
                    const price = priceElement ? priceElement.textContent : null;

                    return {
                        name,
                        category,
                        price,
                        address,
                        Details,
                        rating,
                        totalReviews: reviewCount,
                    };
                });

                console.log("Place Details:", placeDetails);

                // Navigate to the "About" section
                try {
                    const aboutTabSelector = 'button[aria-label*="About"]';
                    const aboutTabExists = await page.$(aboutTabSelector);

                    if (aboutTabExists) {
                        await page.click(aboutTabSelector);
                        await delay(2000);
                    } else {
                        console.log(`"About" section not available for ${business.name}.`);
                    }
                } catch (error) {
                    console.error(`Error navigating to the About section for ${business.name}:`, error);
                    continue;
                }

                const aboutDetails = await page.evaluate(() => {
                    const aboutSectionText = document.querySelector('.HeZRrf')?.innerText || null;

                    const categories = Array.from(document.querySelectorAll('.iP2t7d.fontBodyMedium')).map(categorySection => {
                        const categoryTitle = categorySection.querySelector('.iL3Qke.fontTitleSmall')?.innerText || null;
                        const options = Array.from(categorySection.querySelectorAll('.hpLkke')).map(option => {
                            const label = option.querySelector('span[aria-label]')?.getAttribute('aria-label') || option.querySelector('.f5BGzb + span')?.innerText || '';
                            return label;
                        }).filter(label => label);
                        return {
                            categoryTitle,
                            options,
                        };
                    });

                    return {
                        about: aboutSectionText,
                        categories,
                    };
                });

                console.log("About Details:", JSON.stringify(aboutDetails.categories, null, 2));

                // Collect and save reviews
                const reviewsTabSelector = 'button[aria-label*="Reviews"]';
                try {
                    await page.waitForSelector(reviewsTabSelector, { timeout: 20000 });
                    await page.click(reviewsTabSelector);
                    await delay(2000);
                } catch (error) {
                    console.error(`Error navigating to reviews for ${business.name}:`, error);
                    continue;
                }

                const reviewsContainerSelector = '.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde';
                try {
                    await page.waitForSelector(reviewsContainerSelector, { timeout: 10000 });
                } catch (error) {
                    console.error(`Error loading reviews for ${business.name}:`, error);
                    continue;
                }

                let lastHeight = 0;
                let retryCounter = 0;
                const maxRetries = 3;
                const allReviews = new Set();

                while (true) {
                    const currentHeight = await page.evaluate((selector) => {
                        const scrollableSection = document.querySelector(selector);
                        scrollableSection.scrollBy(0, scrollableSection.scrollHeight);
                        return scrollableSection.scrollHeight;
                    }, reviewsContainerSelector);

                    if (currentHeight > lastHeight) {
                        lastHeight = currentHeight;
                        retryCounter = 0;
                    } else {
                        retryCounter += 1;
                        console.log(`No new content, retry attempt ${retryCounter}/${maxRetries}`);
                        if (retryCounter >= maxRetries) {
                            console.log("Max retries reached or no more content to scroll. Exiting scrolling loop.");
                            break;
                        }
                    }
                    await delay(1000);

                    const newReviews = await page.evaluate(() => {
                        const reviewElements = document.querySelectorAll('.jftiEf');
                        return Array.from(reviewElements).map(review => {
                            const ratingElement = review.querySelector('.kvMYJc[role="img"]');
                        const rating = ratingElement ? ratingElement.getAttribute('aria-label') : null;
                        const textElement = review.querySelector('.wiI7pd');
                        const text = textElement ? textElement.innerText : null;
                        const ownerResponse = review.querySelector('.cDe7pd');
                        const ownerResponseText = ownerResponse ? ownerResponse.innerText : null;

                        const userProfilePictureElement = document.querySelector('.NBa7we');
                        const userProfilePicture = userProfilePictureElement ? userProfilePictureElement.getAttribute('src') : null;

                        const userhistory = review.querySelectorAll('button.al6Kxe[data-href]');
                        const userElement = review.querySelector('.d4r55');
                        const dateElement = review.querySelector('.rsqaWe');
                        const userInfoElement = review.querySelector('.RfnDt');
                        const userInfo = userInfoElement ? userInfoElement.innerText : null;
                        const photoElements = review.querySelectorAll('.Tya61d');
                        const photoUrls = Array.from(photoElements).map(photoElement => photoElement.style.backgroundImage.slice(5, -2));

                        const moreButton = review.querySelector('button[aria-label="More"]');
                        if (moreButton) {
                            moreButton.click();
                        }
                        
                        if (rating && text) {
                            return {
                                user: userElement ? userElement.innerText : 'Anonymous',
                                rating,
                                text,
                                ownerResponseText,
                                date: dateElement ? dateElement.innerText : null,
                                userInfo,
                                photoUrls, 
                                userProfilePicture,
                                userhistory: Array.from(userhistory).map(item => item.getAttribute('data-href')),
                            };
                            }
                            return null;
                        }).filter(review => review !== null);
                    });

                    if (newReviews && newReviews.length > 0) {
                        newReviews.forEach(review => allReviews.add(JSON.stringify(review)));
                    } else {
                        console.log('No new valid reviews found.');
                        break;
                    }
                }

                const allReviewsArray = Array.from(allReviews).map(review => JSON.parse(review));
                const sanitizedPlaceName = business.name.replace(/[\s\\/:*?"<>|,]/g, '_');
                const outputFilePath = path.join(outputFolder, `${sanitizedPlaceName}.json`);
                fs.writeFileSync(outputFilePath, JSON.stringify({ placeDetails, aboutDetails, reviews: allReviewsArray }, null, 2), 'utf-8');
                console.log(`Saved details for ${business.name} to ${outputFilePath}`);
            }
            
        }
        
    }

    await browser.close();
}

// Example usage
const jsonFolders = [
    '/Users/sahil/Downloads/man/ManPlacesBatch1',
    '/Users/sahil/Downloads/man/ManPlacesBatch2',
    '/Users/sahil/Downloads/man/ManPlacesBatch3'
];

scrapeBusinessData(jsonFolders);
