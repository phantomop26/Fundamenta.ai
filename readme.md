**Data Pipeline for Business and User Information Extraction**

This project implements a full data pipeline that performs data extraction, cleaning, scraping, and final data preparation for analysis. The pipeline is organized into several stages, each focusing on a key part of the data processing workflow.

**Project Structure**

The project includes the following stages:
	1.	Data Extraction - Extracts business and category information.<br>
	2.	Data Cleaning I - Cleans and preprocesses the extracted data for web scraping.
    <br>
	3.	Data Scraping - Scrapes user data from the web across various platforms.
    <br>
	4.	Data Cleaning II - Cleans and processes the scraped data to prepare it for analysis.
    <br>
	5.	Data Analysis - (Future phase) Prepares data insights and visualizations.

**Folders and Contents**

**1. Data Extraction**

	•	Purpose: Extracts information about business categories and individual businesses within those categories.
	•	Description: Organizes extracted data into structured files saved under the data_extraction folder.
	•	Technologies: Uses tools like Puppeteer or Overpass API to collect structured data from sources such as business directories or maps.

**Extraction Time: 5 minutes / Categories (Depends on the size of location)**

**2. Data Cleaning I**

	•	Purpose: Prepares extracted data for web scraping.
	•	Description: Standardizes data formatting, removes duplicates, and organizes data fields for consistent input during the web scraping phase.
	•	Technologies: Python (using libraries like Pandas for data manipulation).

**Extraction Time: 2 minutes / Categories (Depends on the size of Batch)**

**3. Data Scraping**

	•	Purpose: Scrapes user-related data from platforms such as Instagram, Google, Yelp, and TripAdvisor.
	•	Description: This stage collects user reviews, ratings, and other user-generated content across selected platforms.
	•	Technologies: Uses Puppeteer, Selenium, or API integrations with social and review platforms to retrieve user data.

**Extraction Time: 40-50 Seconds / Business (Depends on the Number of Reviews)**

**4. Data Cleaning II**

	•	Purpose: Cleans and processes scraped data, making it ready for analysis.
	•	Description: Handles text normalization, removes irrelevant data points, and organizes information for easier analysis.
	•	Technologies: Python with NLP libraries (e.g., NLTK or spaCy) for text processing, and Pandas for data structuring.

**Extraction Time: 2 minutes / Categories (Depends on the size of the Batch)**

**5. Data Analysis**

	•	Purpose: Analyze the cleaned data and generate insights.
	•	Description: Apply analytical methods and visualizations to understand trends, patterns, and user sentiments.
	•	Technologies: Python (e.g., Matplotlib, Seaborn), Tableau for visualizations.

