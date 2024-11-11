const puppeteer = require('puppeteer');
const fs = require('fs');

const places = [];


    async function scrapeReviews() {
        const browser = await puppeteer.launch({ headless: false });
    
        for (const place of places) {
            const page = await browser.newPage();
            let allReviews = [];
    
            // Function to auto-scroll to the bottom of the page
            async function autoScroll(page) {
                await page.evaluate(async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 150; 
                        const timer = setInterval(() => {
                            window.scrollBy(0, distance);
                            totalHeight += distance;
    
                            // Stop scrolling when reaching the bottom
                            if (totalHeight >= document.body.scrollHeight) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                });
            }
    

            await page.goto(place.url, { waitUntil: 'networkidle2', timeout: 0 });
            const hotelName = await page.evaluate(() => {
                const element = document.querySelector('h1.y-css-olzveb');
                return element ? element.innerText : null;
            });
    
            const hotelRating = await page.evaluate(() => {
                const ratingElement = document.querySelector('div.y-css-1om4a3q[aria-label]');
                if (ratingElement) {
                    const match = ratingElement.getAttribute('aria-label').match(/([\d.]+)/);
                    return match ? match[1] : null;
                }
                return null;
            });
    
            const totalReviews = await page.evaluate(() => {
                const reviewsElement = document.querySelector('a.y-css-12ly5yx[href="#reviews"]');
                if (reviewsElement) {
                    const match = reviewsElement.innerText.match(/(\d[\d,]*)/); 
                    return match ? parseInt(match[1].replace(/,/g, '')) : null; 
                }
                return null;
            });
            
    
            const hotelPrice = await page.evaluate(() => {
                const priceElement = document.querySelector('span.y-css-33yfe');
                return priceElement ? priceElement.innerText : null;
            });
    
            const hotelCategory = await page.evaluate(() => {
                const categoryElements = document.querySelectorAll('span.y-css-kw85nd > a.y-css-12ly5yx');
                return Array.from(categoryElements)
                    .map(el => el.innerText)
                    .filter(text => text.length > 0)
                    .join(', ');
            });
    
            const address = await page.evaluate(() => {
                const streetElement = document.querySelector('p.y-css-r4s27p > a > span.raw__09f24__T4Ezm');
                const cityElement = document.querySelector('p.y-css-sauewc > span.raw__09f24__T4Ezm');
                const street = streetElement ? streetElement.innerText : '';
                const city = cityElement ? cityElement.innerText : '';
                return street && city ? `${street}, ${city}` : null;
            });
    
            console.log(`Scraping reviews for ${place.name}: Total reviews = ${totalReviews}`);
    
            async function extractReviews() {
                try {
                    await page.waitForSelector('li.y-css-mu4kr5', { timeout: 10000 });
                    
                    const reviewsData = await page.evaluate(() => {
                        const reviewElements = document.querySelectorAll('li.y-css-mu4kr5');
                        return Array.from(reviewElements).map(el => {
                            const reviewText = el.querySelector('p.comment__09f24__D0cxf span.raw__09f24__T4Ezm')?.innerText.trim() || null;
                            const userName = el.querySelector('a.y-css-12ly5yx')?.innerText.trim() || null;
                            const userPhotoLink = el.querySelector('img.y-css-1k4vfmo')?.src || null;
                            const userLocation = el.querySelector('span.y-css-h9c2fl')?.innerText.trim() || null;
                            const userFriends = el.querySelector('div.y-css-j83o9w[aria-label="Friends"]')?.innerText.trim() || null;
                            const userReviews = el.querySelector('div.y-css-j83o9w[aria-label="Reviews"]')?.innerText.trim() || null;
                            const userPhotos = el.querySelector('div.y-css-j83o9w[aria-label="Photos"]')?.innerText.trim() || null;
                            const postedPhotos = Array.from(el.querySelectorAll('img.y-css-dy9j94')).map(img => img.src);
                            const userRatingElement = el.querySelector('span.y-css-ezc413 > div.y-css-1jwbncq[role="img"]');
                            const userRating = userRatingElement ? userRatingElement.getAttribute('aria-label').match(/([\d.]+)/)[1] : null;
                            const userTagElement = el.querySelector('span.y-css-13vld4t');
                            const userTag = userTagElement ? userTagElement.innerText.trim() : null;
    
                            if (reviewText && userName && userPhotoLink && userLocation && userFriends && userReviews && userPhotos) {
                                return {
                                    reviewText,
                                    rating: userRating,
                                    user: {
                                        name: userName,
                                        tag: userTag,
                                        photoLink: userPhotoLink,
                                        location: userLocation,
                                        friends: userFriends,
                                        reviews: userReviews,
                                        photos: userPhotos,
                                        postedPhotos,
                                    }
                                };
                            } else {
                                return null;  
                            }
                        }).filter(data => data !== null);  
                    });
    
                    allReviews.push(...reviewsData);
    
                } catch (error) {
                    console.log(`Error extracting reviews for ${place.name}:`, error);
                }
            }
    
            await autoScroll(page);  
            await extractReviews();
    
            const totalPages = Math.ceil(totalReviews / 10);  
            for (let pageIndex = 1; pageIndex < totalPages; pageIndex++) {
                const nextPageURL = `${place.url}?start=${pageIndex * 10}`;
                await page.goto(nextPageURL, { waitUntil: 'networkidle2', timeout: 0 });
    
                await autoScroll(page);  
                await extractReviews();  
                if (allReviews.length < (pageIndex + 1) * 10) {
                    console.log(`Re-trying page ${pageIndex} for ${place.name}`);
                    await page.reload({ waitUntil: 'networkidle2', timeout: 0 });
                    await autoScroll(page);  
                    await extractReviews();  
                }
            }
    
            const data = {
                hotelName,
                address,
                hotelRating,
                totalReviews,
                hotelPrice,
                hotelCategory,
                reviews: allReviews,
            };
    
            const fileName = `${place.name}_reviews.json`;
            fs.writeFileSync(fileName, JSON.stringify(data, null, 2), 'utf-8');
    
            console.log(`Scraped ${allReviews.length} reviews for ${place.name}`);
        }
    
        await browser.close();
    }
    
    scrapeReviews().catch(console.error);
