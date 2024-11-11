
const puppeteer = require('puppeteer');
const fs = require('fs');

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}

async function scrapeGoogleReviews(places) {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    for (const place of places) {
        try {
            const searchTerm1 = `${place.Category} ${place.Zip}`;
            const searchTerm2 = place.Names;
            let searchSuccessful = false;

            for (const searchTerm of [searchTerm1, searchTerm2]) {
                console.log(`Searching for: ${searchTerm}`);
                try {
                    await page.goto('https://www.google.com/maps', { waitUntil: 'networkidle2', timeout: 60000 });
                    await page.waitForSelector('input#searchboxinput', { timeout: 10000 });
                    await page.type('input#searchboxinput', searchTerm);
                    await page.waitForSelector('button#searchbox-searchbutton', { timeout: 10000 });
                    await page.click('button#searchbox-searchbutton');
                    await page.waitForSelector('.a5H0ec', { timeout: 10000 });
                    
                    searchSuccessful = true;
                    break;
                } catch (error) {
                    console.error(`Error searching for ${searchTerm}:`, error);
                    continue;
                }
            }

            if (!searchSuccessful) {
                console.log(`Primary searches failed for ${place.Names}. Checking for alternative suggestions...`);
                const suggestion = await page.$('.Nv2PK.Q2HXcd.THOPZb a');
                if (suggestion) {
                    const altLink = await page.evaluate(element => ({
                        name: element.getAttribute('aria-label'),
                        href: element.href
                    }), suggestion);

                    console.log(`Navigating to alternative suggestion: ${altLink.name}`);
                    await page.goto(altLink.href, { waitUntil: 'networkidle2', timeout: 60000 });
                    searchSuccessful = true;
                } else {
                    console.log(`No alternative suggestions found for ${place.Names}. Skipping.`);
                    continue;
                }
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

            try {
                const aboutTabSelector = 'button[aria-label*="About"]'; 
                await page.waitForSelector(aboutTabSelector, { timeout: 10000 });
                await page.click(aboutTabSelector);  
                await delay(2000); 
            } catch (error) {
                console.error(`Error navigating to the About section for ${place.Names}:`, error);
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


            // Check for alternative search suggestion button
            const alternativeSearchSelector = '.UsUSKc.fontBodySmall.RfCwec button.C9cOMe';
            const hasAlternativeSearch = await page.$(alternativeSearchSelector);
            if (hasAlternativeSearch) {
                try {
                    console.log("Alternative search suggestion found. Clicking it to refine search results.");
                    await page.click(alternativeSearchSelector);
                    await delay(2000);
                } catch (error) {
                    console.error("Error clicking alternative search suggestion:", error);
                }
            }

            // Check for another refinement button with class 'kyuRq'
            const refinementButtonSelector = 'button.kyuRq';
            const hasRefinementButton = await page.$(refinementButtonSelector);
            if (hasRefinementButton) {
                try {
                    console.log("Refinement button found. Clicking it for more accurate search results.");
                    await page.click(refinementButtonSelector);
                    await delay(2000);
                } catch (error) {
                    console.error("Error clicking refinement button:", error);
                }
            }


            try {
                const reviewsTabSelector = 'button[aria-label*="Reviews"]'; 
                await page.waitForSelector(reviewsTabSelector, { timeout: 20000 });
                await page.click(reviewsTabSelector);
                await delay(2000);  
            } catch (error) {
                console.error(`Error navigating to reviews for ${place.Names}:`, error);
                continue; 
            }

            const reviewsContainerSelector = '.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde';
            try {
                await page.waitForSelector(reviewsContainerSelector, { timeout: 10000 });
            } catch (error) {
                console.error(`Error loading reviews for ${place.Names}:`, error);
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
                }
            }

            const allReviewsArray = Array.from(allReviews).map(review => JSON.parse(review));
            const sanitizedPlaceName = place.Names.replace(/[\s\\/:*?"<>|,]/g, '_');
            const filePath = `${sanitizedPlaceName}.json`;
            fs.writeFileSync(filePath, JSON.stringify({ placeDetails, aboutDetails, reviews: allReviewsArray }, null, 2), 'utf-8');
            console.log(`Reviews for ${place.Names} successfully saved to ${filePath}`);
        } catch (mainError) {
            console.error(`Encountered an error processing ${place.Names}:`, mainError);
        }
    }

    await browser.close();
}

const places =[];
scrapeGoogleReviews(places);
