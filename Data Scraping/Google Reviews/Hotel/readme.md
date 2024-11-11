**Google Maps Place and Review Scraper**

This Node.js project uses Puppeteer to scrape Google Maps for place details and user reviews based on a list of provided place names. It retrieves information such as place name, category, rating, address, and user reviews. All data is saved to JSON files.

**Extraction Time: 2-3 Minutes / Business (Depending on the no of reviews)**

Features

	•	Scrapes Google Maps for place details (name, category, rating, address, contact information, etc.)
	•	Navigates to the reviews tab and scrapes user reviews with details like rating, review text, user info, profile picture, and posted photos
	•	Automatically scrolls within the reviews section to load all available reviews
	•	Saves the place details and reviews to JSON files, one for each place

Prerequisites

	•	Node.js (tested with version 14+)
	•	Puppeteer library for headless browser automation

Installation

	1.	Clone the repository:

git clone https://github.com/yourusername/google-maps-review-scraper.git
cd google-maps-review-scraper


	2.	Install dependencies:

npm install puppeteer


	3.	Prepare the list of places you want to scrape by adding them to the places array in the script.

Usage

	1.	Run the script:

node script.js


	2.	The script will launch a browser instance, open Google Maps, and start searching each place from the places array.
	3.	Once the script completes, it will save a JSON file for each place, containing both place details and reviews.

Script Breakdown

	•	Place Search - Searches Google Maps for each place name provided in the places array.
	•	Review Extraction - Gathers each review’s text, rating, date, user info, and photos.
	•	Scrolling Logic - Auto-scrolls within the review section to load all reviews.
	•	Error Handling - Retry logic and delays for improved scraping reliability.

Output

Each place’s data is saved to a JSON file named after the place, with the following structure:

{
  "placeDetails": {
    "name": "Sample Place",
    "category": "Restaurant",
    "smallDescription": "Casual dining",
    "address": "123 Main St, New York, NY",
    "contactDetails": ["(123) 456-7890"],
    "rating": "4.5",
    "totalReviews": "1,234"
  },
  "reviews": [
    {
      "user": "John Doe",
      "rating": "5",
      "text": "Great place!",
      "date": "2 months ago",
      "userInfo": "Local Guide · 120 reviews",
      "photoUrls": ["https://example.com/photo.jpg"],
      "userProfilePicture": "https://example.com/user_photo.jpg"
    }
  ]
}

Notes

	•	This script is for educational and personal use. Ensure compliance with Google Maps’ Terms of Service when scraping data.
	•	Use appropriate delays and retry logic to avoid being blocked by Google.

License

This project is licensed under the MIT License. See the LICENSE file for details.