**Google Maps Place and Review Scraper**

This Node.js script uses Puppeteer to scrape place details and user reviews from Google Maps based on a list of places. The script performs search retries, extracts detailed information about the place (name, category, rating, address), and captures user reviews with owner responses, profile pictures, user history, and photos.

**Extraction Time: 2-3 Minutes/ Business (Depending of the no of reviews**
Features

	•	Automated Search: Searches for each place using both primary terms and fallbacks if needed.
	•	Place Details: Captures name, category, price, rating, address, and additional about details.
	•	User Reviews: Scrapes reviews with details like rating, text, owner response, user profile pictures, user history, and uploaded photos.
	•	Auto-scrolling and Expanding: Continuously scrolls within the review section and clicks “More” to expand long reviews.
	•	Retry Logic: Includes retry attempts and alternative search suggestions for enhanced accuracy and reliability.

Prerequisites

	•	Node.js (tested with version 14+)
	•	Puppeteer for browser automation
	•	fs for file handling

Installation

	1.	Clone the repository:

git clone https://github.com/yourusername/google-maps-review-scraper.git
cd google-maps-review-scraper


	2.	Install dependencies:

npm install puppeteer


	3.	Prepare the list of places by defining an array named places in the script, where each object includes the properties Category, Zip, and Names for each place to search.

Usage

	1.	Run the script:

node script.js


	2.	Output files: For each place, the script will save a JSON file named after the place containing its details and reviews.

Script Breakdown

	•	Primary and Fallback Search: Searches Google Maps for each place by combining its category and zip code or using the specific name, with retries.
	•	Alternative Suggestions: If both searches fail, the script checks for any suggested alternatives.
	•	Place Details Extraction: Retrieves place details like category, rating, address, and contact info.
	•	About and Categories Extraction: Pulls detailed information from the “About” section.
	•	Review Scraping: Extracts user reviews with additional data like profile picture, rating, user history, and owner responses.
	•	Scrolling and Expanding Logic: Scrolls within the review container and expands full reviews.
	•	Error Handling: Retry logic and error messages ensure reliable scraping across sessions.

Output Structure

Each place’s data is saved in a JSON file with the following structure:

{
  "placeDetails": {
    "name": "Sample Place",
    "category": "Restaurant",
    "price": "$$",
    "address": "123 Main St, New York, NY",
    "Details": ["Open 24 hours", "(123) 456-7890"],
    "rating": "4.5",
    "totalReviews": "1,234"
  },
  "aboutDetails": {
    "about": "Casual dining with a variety of options.",
    "categories": [
      {
        "categoryTitle": "Amenities",
        "options": ["Free Wi-Fi", "Outdoor Seating"]
      }
    ]
  },
  "reviews": [
    {
      "user": "John Doe",
      "rating": "5",
      "text": "Great place with amazing food!",
      "ownerResponseText": "Thank you for your feedback!",
      "date": "2 months ago",
      "userInfo": "Local Guide · 100 reviews",
      "photoUrls": ["https://example.com/photo.jpg"],
      "userProfilePicture": "https://example.com/user_photo.jpg",
      "userhistory": ["/url/to/user/history"]
    }
  ]
}

Notes

	•	For Educational Use Only: This scraper is for personal and educational purposes. Comply with Google Maps’ Terms of Service when scraping data.
	•	Rate Limits: Use with delays and proper error handling to avoid getting blocked.

License

This project is licensed under the MIT License. See the LICENSE file for details.
