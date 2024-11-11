**Yelp Review Scraper**

This project is a Node.js script using Puppeteer to scrape reviews and hotel details from Yelp for a list of specified places. The script gathers detailed information about each place, including name, rating, price, address, category, and user reviews. Reviews are saved as JSON files, with one file per place.

**Extraction Time: 11 Seconds / Page**

Features

	•	Scrapes hotel name, rating, price, address, and category
	•	Extracts detailed reviews including review text, user information, ratings, and photos
	•	Saves scraped data to JSON files for easy access and analysis
	•	Auto-scrolls to load additional reviews and navigates through multiple review pages

Requirements

	•	Node.js (tested with version 14+)
	•	Puppeteer library for headless browser automation
	•	File System (fs) module for saving JSON output

Installation

	1.	Clone the repository:

git clone https://github.com/yourusername/yelp-review-scraper.git
cd yelp-review-scraper


	2.	Install dependencies:

npm install puppeteer


	3.	Add the URLs of places to the places array in the script, with each place having a name and url field.

Usage

Run the script with:

node script.js

Script Breakdown

	1.	Auto-Scroll - The script automatically scrolls down the page to load additional reviews.
	2.	Review Extraction - It gathers each review’s text, user rating, photos, user name, and location.
	3.	Pagination - If the total number of reviews exceeds one page, it navigates to the next pages.

Output

The script generates a JSON file for each place, containing:
	•	Hotel Details: Name, address, rating, price, category
	•	Reviews: An array of review objects with detailed user information

Example file structure:

{
  "hotelName": "Sample Hotel",
  "address": "123 Main St, New York, NY",
  "hotelRating": "4.5",
  "totalReviews": 250,
  "hotelPrice": "$$",
  "hotelCategory": "Hotels, Resorts",
  "reviews": [
    {
      "reviewText": "Great experience!",
      "rating": "5.0",
      "user": {
        "name": "John Doe",
        "tag": "Local Guide",
        "photoLink": "https://example.com/photo.jpg",
        "location": "New York, NY",
        "friends": "20",
        "reviews": "50",
        "photos": "10",
        "postedPhotos": ["https://example.com/review-photo.jpg"]
      }
    }
  ]
}

Note

This script is for educational and personal use. Make sure to follow Yelp’s Terms of Service when scraping data.

License

MIT License. See LICENSE for details.
