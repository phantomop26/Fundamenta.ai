**Google Maps User Profile and Review Scraper**

This Node.js project uses Puppeteer to scrape user profile information and reviews from Google Maps based on a list of URLs provided in a CSV file. The script extracts data such as profile picture, user tag, review points, and detailed reviews, and saves them into individual JSON files.

**Extraction Time: 50-60 Seconds/ User**
Features

	•	Scrapes Google Maps user profile information, including name, profile picture, user tag, and review points
	•	Extracts user reviews, including text, rating, photos, and any owner responses
	•	Auto-scrolls within the review section and expands all available reviews
	•	Handles retry logic for enhanced scraping reliability
	•	Saves each user’s profile and reviews to a JSON file

Prerequisites

	•	Node.js (tested with version 14+)
	•	Puppeteer library for headless browser automation
	•	CSV Parser module to read the list of URLs from a CSV file

Installation

	1.	Clone the repository:

git clone https://github.com/yourusername/google-maps-review-scraper.git
cd google-maps-review-scraper


	2.	Install dependencies:

npm install puppeteer csv-parser


	3.	Prepare a CSV file:
Create a file named users.csv with a column containing the URLs to each user profile on Google Maps. Each URL should be in a row under the header user_links.

Usage

	1.	Run the script:

node script.js


	2.	The script will read URLs from users.csv, scrape each profile, and save the data to a JSON file named after the user.

Script Breakdown

	•	CSV Parsing - Reads URLs from users.csv to get user profile links.
	•	Infinite Scroll - Auto-scrolls within the review section to load additional reviews.
	•	Review Extraction - Gathers each review’s text, rating, photos, and other details.
	•	Pagination & Retry Logic - Handles navigation and retries for reliability.

Output

Each user’s profile and reviews are saved to a JSON file, with the following structure:

{
  "profile": {
    "name": "Sample User",
    "profilePicUrl": "https://example.com/photo.jpg",
    "reviewPoints": "1000",
    "userTagOrContributions": "Local Guide"
  },
  "reviews": [
    {
      "name": "Sample Review",
      "rating": "5.0",
      "time": "1 month ago",
      "textReview": "Great experience!",
      "photos": ["https://example.com/review-photo.jpg"],
      "ownerResponse": {
        "date": "2 weeks ago",
        "text": "Thank you for your feedback!"
      }
    }
  ]
}

License

This project is licensed under the MIT License. See the LICENSE file for details.

This version emphasizes key elements by making them bold. Let me know if you’d like further adjustments!