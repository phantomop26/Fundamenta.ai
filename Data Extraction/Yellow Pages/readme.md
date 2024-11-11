Yellow Pages Business Listings Scraper

This Node.js script uses Puppeteer to scrape business listings from Yellow Pages for specified categories in Manhattan, NY. It retrieves information such as business name, categories, phone number, address, links, and badges, then saves each category’s data in a separate JSON file.

**Extraction Time: 2-3 Minutes / Business**

Features

	•	Category-Specific Scraping: Retrieves business listings for specified categories (e.g., Restaurants, Plumbers, etc.)
	•	Multi-Page Navigation: Automatically calculates the total number of pages for each category and iterates through them
	•	Data Extraction: Collects business name, categories, links, phone number, address, and badges
	•	Data Saving: Stores each category’s results in a separate JSON file

Prerequisites

	•	Node.js (tested with version 14+)
	•	Puppeteer for headless browser automation
	•	fs module for file handling

Install dependencies by running:

npm install puppeteer

Setup

	1.	Clone the repository:

git clone https://github.com/yourusername/yellowpages-scraper.git
cd yellowpages-scraper


	2.	Configure Categories: Add the categories you want to scrape in the categories array within the script, e.g., const categories = ['Restaurants', 'Plumbers', 'Electricians'];
	3.	Run the Script:

node script.js



How It Works

	1.	Define Categories: Each category specified in the categories array is formatted for the Yellow Pages URL structure.
	2.	Navigate to Pages: The script calculates the total pages for each category based on the total number of results.
	3.	Scrape Business Listings: For each page, it extracts data including business name, categories, links, badges, phone, and address.
	4.	Save Results: After scraping, the script saves data to a JSON file named after the category (e.g., yellowpages_restaurants.json).

Script Breakdown

	•	Category Formatting: Converts category names to lowercase and replaces spaces with hyphens to match URL formatting.
	•	Pagination and Data Extraction: Scrapes business listings on each page until all results are gathered.
	•	Delay Logic: Introduces a delay between page requests to avoid overloading the Yellow Pages server.

Example Output

Each JSON file contains data in the following format:

[
    {
        "name": "Joe's Pizza",
        "categories": ["Pizza", "Italian Restaurant"],
        "links": [
            {"text": "Website", "href": "https://www.joespizza.com"},
            {"text": "Menu", "href": "https://www.joespizza.com/menu"}
        ],
        "badges": "Top Rated",
        "phone": "(123) 456-7890",
        "address": "123 Main St, New York, NY 10001"
    },
    {
        "name": "ABC Plumbing",
        "categories": ["Plumber"],
        "links": [],
        "badges": null,
        "phone": "(987) 654-3210",
        "address": "456 Elm St, New York, NY 10002"
    }
]

Notes

	•	Avoid Overloading the Server: The script includes a delay between page requests. Adjust the delay if needed.
	•	Ensure Proper Use: This scraper is intended for educational and personal use. Make sure to follow Yellow Pages’ Terms of Service when scraping data.

License

This project is licensed under the MIT License.

