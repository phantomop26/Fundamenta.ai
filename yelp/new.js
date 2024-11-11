const puppeteer = require('puppeteer');
const fs = require('fs');

const places = [
    // {
    //     "name": "Dos Caminos",
    //     "url": "https://www.yelp.com/biz/dos-caminos-new-york"
    // },
    // {
    //     "name": "La Esquina",
    //     "url": "https://www.yelp.com/biz/la-esquina-new-york"
    // },
    // {
    //     "name": "Champers Social Club",

    //     "url": "https://www.yelp.com/biz/champers-social-club-new-york"
    // },
    // {
    //     "name": "Jacks Wife Freda",
    //     "url": "https://www.yelp.com/biz/jacks-wife-freda-new-york"
    // },
    // {
    //     "name": "Bar Moga",
    //     "url": "https://www.yelp.com/biz/bar-moga-new-york"
    // },
    // {
    //     "name": "Bibliotheque Cafe & Winebar",
    //     "url": "https://www.yelp.com/biz/bibliotheque-new-york"
    // },
    // {
    //     "name": "Lucia Pizza",
    //     "url": "https://www.yelp.com/biz/lucia-of-soho-new-york"
    // },
    // {//didnt scrape
    //     "name": "Charley Bird",
    //     "url": "https://www.yelp.com/biz/charlie-bird-new-york"
    // },
    // // {
    // //     "name": "Caff Bene",
    // //     "url": "https://www.yelp.com/biz/caffe-bene-new-york"
    // // },
    // {"name": "balthazar",
    //     "url": "https://www.yelp.com/biz/balthazar-new-york"},
    // {
    //     "name": "Song E Napule",
    //     "url": "https://www.yelp.com/biz/song-e-napule-new-york"
    // },
    // {
    //     "name": "Comodo",
    //     "url": "https://www.yelp.com/biz/comodo-new-york"
    // },
    // {
    //     "name": "12 Chairs",
    //     "url": "https://www.yelp.com/biz/12-chairs-new-york"
    // },
    // {
    //     "name": "Emmett's",
    //     "url": "https://www.yelp.com/biz/Emmetts-new-york"
    // },
    // {
    //     "name": "Raku Soho",
    //     "url": "https://www.yelp.com/biz/raku-soho-ßnew-york"
    // },
    // {
    //     "name": "Lupa",
    //     "url": "https://www.yelp.com/biz/lupa-new-york"
    // },
    // // {
    // //     "name": "Mikaku",
    // //     "url": "https://www.yelp.com/biz/mikaku-sushi-new-york"
    // // },

    // // {
    // //     "name": "Osteria Morini",
    // //     "url": "https://www.yelp.com/biz/osteria-morini-new-york"
    // // },
    // // {
    // //     "name": "Fanelli Cafe",
    // //     "url": "https://www.yelp.com/biz/fanelli-cafe-new-york"
    // // },
    // // {
    // //     "name": "Balthazar",
    // //     "url": "https://www.yelp.com/biz/balthazar-new-york"
    // // },
    // // {
    // //     "name": "Blue Ribbon",
    // //     "url": "https://www.yelp.com/biz/blue-ribbon-new-york"
    // // },
    // // {
    // //     "name": "The Dutch",
    // //     "url": "https://www.yelp.com/biz/the-dutch-new-york"
    // // },
    // {
    //     "name": "Dominique Ansel Bakery",
    //     "url": "https://www.yelp.com/biz/dominique-ansel-bakery-new-york"
    // },
    // {
    //     "name": "Miss Lily's (Soho)",
    //     "url": "https://www.yelp.com/biz/Miss-Lilys-7a-cafe-new-york"
    // },
    // {
    //     "name": "Sartianos",
    //     "url": "https://www.yelp.com/biz/sartianos-new-york"
    // },
    // {
    //     "name": "Jane",
    //     "url": "https://www.yelp.com/biz/jane-new-york"
    // },
    // {
    //     "name": "Da Marcella",
    //     "url": "https://www.yelp.com/biz/da-marcella-new-york"
    // },
    // {
    //     "name": "Black Tap",
    //     "url": "https://www.yelp.com/biz/black-tap-new-york"
    // },
    // {
    //     "name": "Blue Ribbon Brassiere",
    //     "url": "https://www.yelp.com/biz/blue-ribbon-brassiere-new-york"
    // },
    // {
    //     "name": "Arturo's Coal Oven Pizza",
    //     "url": "https://www.yelp.com/biz/arturos-new-york"
    // },
    // {
    //     "name": "Boqueria Soho",
    //     "url": "https://www.yelp.com/biz/boqueria-soho-new-york"
    // },
    // {
    //     "name": "lupe's East L.A. Kitchen",
    //     "url": "https://www.yelp.com/biz/lupes-east-l-a-kitchen-new-york"
    // },
    // {
    //     "name": "Think Coffee",
    //     "url": "https://www.yelp.com/biz/think-coffee-new-york"
    // },
    // {
    //     "name": "Pepe Rosso",
    //     "url": "https://www.yelp.com/biz/pepe-rosso-new-york"
    // },
    // {
    //     "name": "Antique Garage",
    //     "url": "https://www.yelp.com/biz/antique-garage-new-york"
    // },
    // {
    //     "name": "Lure Fishbar",
    //     "url": "https://www.yelp.com/biz/lure-fishbar-new-york"
    // },
    // {
    //     "name": "Morgenstern's Finest Ice Cream",
    //     "url": "https://www.yelp.com/biz/morgensterns-finest-ice-cream-new-york"
    // },
    // {
    //     "name": "Lucky's",
    //     "url": "https://www.yelp.com/biz/luckys-new-york"
    // },
    // {
    //     "name": "GMT Tavern",
    //     "url": "https://www.yelp.com/biz/gmt-tavern-new-york"
    // },
    // {
    //     "name": "Bosie",
    //     "url": "https://www.yelp.com/biz/bosie-new-york"
    // },
    // {
    //     "name": "Mocha Burger",
    //     "url": "https://www.yelp.com/biz/mocha-burger-new-york"
    // },
    // {
    //     "name": "Molcajete Taqueria",
    //     "url": "https://www.yelp.com/biz/molcajete-taqueria-new-york"
    // },
    // {
    //     "name": "Pera SoHo",
    //     "url": "https://www.yelp.com/biz/pera-soho-new-york"
    // },
    // {
    //     "name": "Sessanta",
    //     "url": "https://www.yelp.com/biz/sessanta-new-york"
    // },
    // {
    //     "name": "Aurora SoHo",
    //     "url": "https://www.yelp.com/biz/aurora-soho-new-york"
    // },
    // {
    //     "name": "Birch Coffee",
    //     "url": "https://www.yelp.com/biz/birch-coffee-new-york"
    // },
    // {
    //     "name": "Her Name Was Carmen",
    //     "url": "https://www.yelp.com/biz/her-name-was-carmen-new-york"
    // },
    // {
    //     "name": "Sadelles",
    //     "url": "https://www.yelp.com/biz/sadelles-new-york"
    // },
    // {
    //     "name": "Chobani SoHo",
    //     "url": "https://www.yelp.com/biz/chobani-soho-new-york"
    // },
    // {
    //     "name": "La Colombe Coffee Roasters",
    //     "url": "https://www.yelp.com/biz/la-colombe-coffee-roasters-new-york"
    // },
    // {
    //     "name": "Papatzu Mexican Restaurant",
    //     "url": "https://www.yelp.com/biz/papatzu-mexican-restaurant-new-york"
    // },
    // {
    //     "name": "Pinch Chinese",
    //     "url": "https://www.yelp.com/biz/pinch-chinese-new-york"
    // },

    // {
    //     "name": "Sanctuary T",
    //     "url": "https://www.yelp.com/biz/sanctuary-t-new-york"
    // },
    // {
    //     "name": "Banter",
    //     "url": "https://www.yelp.com/biz/banter-new-york"
    // },
    // {
    //     "name": "Carbone",
    //     "url": "https://www.yelp.com/biz/carbone-new-york"
    // },
    // {
    //     "name": "The Woo",
    //     "url": "https://www.yelp.com/biz/the-woo-new-york"
    // },
    // {
    //     "name": "San Carlo Osteria Piemonte",
    //     "url": "https://www.yelp.com/biz/san-carlo-osteria-piemonte-new-york"
    // },
    // {
    //     "name": "Despaa",
    //     "url": "https://www.yelp.com/biz/despaa-new-york"
    // },
    // {
    //     "name": "Piccola Cucina",
    //     "url": "https://www.yelp.com/biz/piccola-cucina-new-york"
    // },
    // {
    //     "name": "T2 tea",
    //     "url": "https://www.yelp.com/biz/t2-tea-new-york"
    // },
    // {
    //     "name": "Barolo",
    //     "url": "https://www.yelp.com/biz/barolo-new-york"
    // },
    // {
    //     "name": "Piccola Cucina Estiatorio",
    //     "url": "https://www.yelp.com/biz/piccola-cucina-estiatorio-new-york"
    // },
    // {
    //     "name": "King",
    //     "url": "https://www.yelp.com/biz/king-new-york"
    // },

    // {
    //     "name": "Famous Ben's Pizza",
    //     "url": "https://www.yelp.com/biz/famous-bens-pizza-new-york"
    // },
    {
        "name": "MAMO",
        "url": "https://www.yelp.com/biz/mamo-new-york"
    },
    {
        "name": "Mishka Soho",
        "url": "https://www.yelp.com/biz/mishka-soho-new-york"
    },
    {
        "name": "Bistro les Amis",
        "url": "https://www.yelp.com/biz/bistro-les-amis-new-york"
    },
    {
        "name": "Tomo21 Sushi",
        "url": "https://www.yelp.com/biz/tomo21-sushi-new-york"
    },

    {
        "name": "Cipriani Downtown NYC",
        "url": "https://www.yelp.com/biz/cipriani-downtown-nyc-new-york"
    },
    {
        "name": "Joe & The Juice",
        "url": "https://www.yelp.com/biz/joe-and-the-juice-new-york"
    },
    {
        "name": "Caput Mundi",
        "url": "https://www.yelp.com/biz/caput-mundi-new-york"
    },
    {
        "name": "Matchaful",
        "url": "https://www.yelp.com/biz/matchaful-new-york"
    },
    {
        "name": "Omen Azen",
        "url": "https://www.yelp.com/biz/omen-azen-new-york"
    },
    {
        "name": "DOMODOMO",
        "url": "https://www.yelp.com/biz/domodomo-new-york"
    },
    {
        "name": "Il Corallo Trattoria",
        "url": "https://www.yelp.com/biz/il-corallo-trattoria-new-york"
    },
    {
        "name": "Shuka",
        "url": "https://www.yelp.com/biz/shuka-new-york"
    },
    {
        "name": "Eataly - So-Ho",
        "url": "https://www.yelp.com/biz/eataly-soho-new-york"
    },
    {
        "name": "Blank Slate",
        "url": "https://www.yelp.com/biz/blank-slate-new-york"
    },
    {
        "name": "Blank Street Coffeee",
        "url": "https://www.yelp.com/biz/blank-street-coffeee-new-york"
    },
    {
        "name": "Mangia",
        "url": "https://www.yelp.com/biz/mangia-new-york"
    },
    {
        "name": "Beatnic",
        "url": "https://www.yelp.com/biz/beatnic-new-york"
    },
    {
        "name": "Panther Coffee",
        "url": "https://www.yelp.com/biz/panther-coffee-new-york"
    },
    {
        "name": "Sui Yoga Studio.Cafe",
        "url": "https://www.yelp.com/biz/sui-yoga-studio.cafe-new-york"
    },
    {
        "name": "Mori",
        "url": "https://www.yelp.com/biz/mori-new-york"
    },
    {
        "name": "Restaurante Flix",
        "url": "https://www.yelp.com/biz/restaurante-flix-new-york"
    },
    {
        "name": "Kintsugi",
        "url": "https://www.yelp.com/biz/kintsugi-new-york"
    },
    {
        "name": "Now or Never",
        "url": "https://www.yelp.com/biz/now-or-never-new-york"
    },
    {
        "name": "Lucia Alimentari",
        "url": "https://www.yelp.com/biz/lucia-alimentari-new-york"
    }];


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