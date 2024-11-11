**Business Data Retrieval Using Overpass API**

This Python script retrieves and categorizes data from the OpenStreetMap Overpass API for specified business types within predefined bounding boxes in Manhattan (below 14th Street). Each bounding box is queried for specific categories like health, education, and shopping, with the results saved to separate JSON files.

**Extraction Time: 5 Minutes**

Features

	•	Targeted Category Retrieval: Retrieves detailed business information for categories including health, education, and shopping.
	•	Bounding Box Limiting: Uses bounding boxes below 14th Street in Manhattan to refine data retrieval.
	•	Data Categorization: Results are categorized by business type, allowing each category’s data to be saved in a separate JSON file.
	•	Rate Limiting: Pauses between API requests to avoid overwhelming the Overpass API.

Requirements

	•	Python 3.x
	•	requests library

Install dependencies using:

pip install requests

How It Works

	1.	Define Categories and Bounding Boxes: The script uses predefined categories and bounding boxes within Manhattan.
	2.	Fetch Data: For each bounding box and category, the script:
	•	Constructs a query to retrieve nodes, ways, and relations for the category’s tags.
	•	Sends a POST request to the Overpass API.
	3.	Process and Save Results: Each retrieved element is processed to extract details like name, latitude, longitude, and category. Results are saved in JSON files, one per category.

Usage

	1.	Edit Categories or Bounding Boxes (Optional):
	•	Customize target_categories to add or remove categories.
	•	Adjust bounding_boxes for different geographic regions.
	2.	Run the Script:

python script.py


	3.	Output: JSON files named after each category (e.g., health_businesses.json, education_businesses.json, etc.) containing details for businesses within that category.

Script Breakdown

	•	Categories and Bounding Boxes: Defines specific tags for business types and bounding boxes for geographic limits.
	•	fetch_data Function: Constructs and sends a query to Overpass, returning business elements.
	•	Categorization and Saving: Elements are organized by category, and results are saved as JSON files.

Example Output

Each JSON file contains data in the following format:

[
    {
        "name": "Sample Clinic",
        "category": "clinic",
        "latitude": 40.712776,
        "longitude": -74.005974
    },
    {
        "name": "Unnamed",
        "category": "pharmacy",
        "latitude": 40.706,
        "longitude": -74.010
    }
]

Notes

	•	API Rate Limiting: The script includes a time.sleep(1) pause to reduce the likelihood of rate-limiting errors.
	•	Missing Information: Some elements may lack a name tag and are saved as "Unnamed".

License

This project is licensed under the MIT License.

