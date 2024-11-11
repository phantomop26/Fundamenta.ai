# # # import requests
# # # import json

# # # # Define the Overpass API endpoint
# # # overpass_url = "http://overpass-api.de/api/interpreter"

# # # # Define the Overpass QL query to get restaurants and cafes in Soho, using bounding box
# # # overpass_query = """
# # # [out:json];
# # # (
# # #   node["amenity"="restaurant"](40.7208,-74.0047,40.7282,-73.9966);
# # #   node["amenity"="cafe"](40.7208,-74.0047,40.7282,-73.9966);
# # # );
# # # out body;
# # # """

# # # # Send the request to the Overpass API
# # # response = requests.post(overpass_url, data={'data': overpass_query})

# # # # Check if the request was successful
# # # if response.status_code == 200:
# # #     # Parse the response JSON
# # #     data = response.json()

# # #     # Extract the list of places with their categories
# # #     places = []
# # #     for element in data['elements']:
# # #         place_name = element['tags'].get('name', 'Unnamed Place')
# # #         category = element['tags'].get('amenity', 'Unknown Category')
# # #         places.append({
# # #             'name': place_name,
# # #             'category': category
# # #         })

# # #     # Print the list of places
# # #     for place in places:
# # #         print(f"{place['name']}, New York")

# # #     # Optionally, save the places to a JSON file
# # #     with open('soho_places.json', 'w') as json_file:
# # #         json.dump(places, json_file, indent=4)

# # #     print("Places data saved to 'soho_places.json'")
# # # else:
# # #     print(f"Error: Unable to fetch data (HTTP {response.status_code})")

# # import requests
# # import json

# # # Define the Overpass API endpoint
# # overpass_url = "http://overpass-api.de/api/interpreter"

# # # Define the Overpass QL query to get hotels below 14th Street in Manhattan
# # overpass_query = """
# # [out:json];
# # (
# #   node["amenity"="hotel"](40.7000,-74.0200,40.7336,-73.9400);  // Coordinates for below 14th St
# #   way["building"="hotel"](40.7000,-74.0200,40.7336,-73.9400);
# #   relation["building"="hotel"](40.7000,-74.0200,40.7336,-73.9400);
# #   node["tourism"="hotel"](40.7000,-74.0200,40.7336,-73.9400);
# #   way["tourism"="hotel"](40.7000,-74.0200,40.7336,-73.9400);
# #   relation["tourism"="hotel"](40.7000,-74.0200,40.7336,-73.9400);
# # );
# # out body;
# # """

# # # Send the request to the Overpass API
# # response = requests.post(overpass_url, data={'data': overpass_query})

# # # Check if the request was successful
# # if response.status_code == 200:
# #     # Parse the response JSON
# #     data = response.json()

# #     # Extract the list of hotels
# #     hotels = []
# #     for element in data['elements']:
# #         hotel_name = element['tags'].get('name', 'Unnamed Hotel')
# #         category = element['tags'].get('amenity', 'Unknown Category')
# #         hotels.append({
# #             'name': hotel_name,
# #             'category': category
# #         })

# #     # Print the number of hotels found
# #     print(f"Number of hotels found: {len(hotels)}")

# #     # Print the list of hotels
    

# #     # Optionally, save the hotels to a JSON file
# #     with open('manhattan_hotels_below_14th_st.json', 'w') as json_file:
# #         json.dump(hotels, json_file, indent=4)

# #     print("Hotel data saved to 'manhattan_hotels_below_14th_st.json'")
# # else:
# #     print(f"Error: Unable to fetch data (HTTP {response.status_code})")


# import requests
# import json
# import time

# # Define the Overpass API endpoint
# overpass_url = "http://overpass-api.de/api/interpreter"
# target_categories = [
#     "animal_boarding", "bakery", "beauty", "beauty_supply", "boutique", "cafe", "cannabis", "cheese",
#     "childcare", "clinic", "coffee", "coffee;tea", "convenience", "cosmetics", "dentist", "department_store",
#     "doctors", "dry_cleaners;laundry", "dry_cleaning", "electronics", "estate_agent", "fashion_accessories",
#     "fast_food", "funeral_directors", "furniture", "gift", "hairdresser", "hairdresser_supply", "handbags",
#     "hardware", "health_food", "ice_cream", "interior_decoration", "jewelry", "kindergarten", "laundry", "locksmith",
#     "medical_supply", "mobile_phone_repair", "music_school", "music_venue", "musical_instrument", "nail_salon",
#     "nightclub", "parking", "parking_entrance", "parking_space", "pastry", "pawnbroker", "perfumery",
#     "pest_control", "pet", "pet_grooming", "pharmacy", "piercing", "print_shop", "pub", "public_bath",
#     "repair", "restaurant", "salon", "school", "School Supply Store", "shoe_repair", "shoes", "shower", "spa",
#     "stationery", "storage_rental", "sunglasses", "supermarket", "surveillance", "tailor", "tattoo", "taxi",
#     "telecommunication", "theatre", "toys", "trade", "training", "travel_agency", "tyres", "university", "urgent_care",
#     "vacant", "vending_machine", "veterinary", "video", "Video Production", "video_games", "watches", "wellness_center",
#     "wifi","telephone", "device_charging_station", "wine"
# ]

# # Define coordinates for the area below 14th St in Manhattan in smaller bounding boxes
# bounding_boxes = [
#     (40.7000, -74.0200, 40.7168, -73.9900),
#     (40.7168, -74.0200, 40.7336, -73.9900),
#     (40.7000, -73.9900, 40.7168, -73.9600),
#     (40.7168, -73.9900, 40.7336, -73.9600),
# ]

# # Initialize a dictionary to store categories
# categorized_data = {category: [] for category in target_categories}

# # Function to retrieve data for a given bounding box
# def fetch_data(bbox):
#     # Overpass query template with coordinates and categories
#     overpass_query = f"""
#     [out:json];
#     (
#       node["amenity"](bbox);
#       way["amenity"](bbox);
#       relation["amenity"](bbox);
#       node["shop"](bbox);
#       way["shop"](bbox);
#       relation["shop"](bbox);
#       node["tourism"](bbox);
#       way["tourism"](bbox);
#       relation["tourism"](bbox);
#     );
#     out body;
#     """.replace("bbox", f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}")
    
#     # Send request to Overpass API
#     response = requests.post(overpass_url, data={'data': overpass_query})
    
#     # Check for successful response
#     if response.status_code == 200:
#         return response.json().get('elements', [])
#     else:
#         print(f"Error fetching data: HTTP {response.status_code}")
#         return []

# # Loop through each bounding box to fetch data
# for bbox in bounding_boxes:
#     print(f"Fetching data for bounding box: {bbox}")
#     elements = fetch_data(bbox)
    
#     # Process each element and categorize it
#     for element in elements:
#         tags = element.get('tags', {})
#         category = tags.get('amenity') or tags.get('shop') or tags.get('tourism')
        
#         # Only proceed if the category is in target categories
#         if category in target_categories:
#             business_info = {
#                 'name': tags.get('name', 'Unnamed'),
#                 'category': category,
#                 'latitude': element.get('lat'),
#                 'longitude': element.get('lon')
#             }
#             categorized_data[category].append(business_info)
    
#     # Pause between requests to avoid overwhelming the API
#     time.sleep(1)

# # Save each category to its own JSON file
# for category, businesses in categorized_data.items():
#     if businesses:  # Save only if the category has data
#         filename = f"{category}_businesses.json"
#         with open(filename, 'w') as json_file:
#             json.dump(businesses, json_file, indent=4)
#         print(f"Saved {len(businesses)} businesses in '{filename}'")


import requests
import json
import time

# Define the Overpass API endpoint
overpass_url = "http://overpass-api.de/api/interpreter"

# Define main categories with refined tags to increase data retrieval efficiency
target_categories = {
    # "food": ["bakery", "cafe", "convenience", "fast_food", "ice_cream", "restaurant", "wine"],
    "health": ["clinic", "dentist", "doctors", "pharmacy", "veterinary", "wellness_center", "spa", "nail_salon"],
    "education": ["school", "university", "training", "music_school", "kindergarten"],
    # "beauty": ["beauty", "beauty_supply", "hairdresser", "hairdresser_supply", "cosmetics"],
    "shopping": ["department_store", "fashion_accessories", "jewelry", "boutique", "furniture", "stationery", "gift"],
    # "miscellaneous": ["laundry", "dry_cleaning", "clinic", "storage_rental", "pet", "childcare", "nightclub"]
}

# Coordinates for smaller bounding boxes below 14th Street in Manhattan
bounding_boxes = [
    (40.7000, -74.0200, 40.7168, -73.9900),
    (40.7168, -74.0200, 40.7336, -73.9900),
    (40.7000, -73.9900, 40.7168, -73.9600),
    (40.7168, -73.9900, 40.7336, -73.9600),
]

# Initialize a dictionary to store categorized data
categorized_data = {category: [] for category in target_categories.keys()}

# Function to retrieve data for a given bounding box and tags
def fetch_data(bbox, tags):
    # Overpass query template with coordinates and tags
    overpass_query = f"""
    [out:json];
    (
      {''.join([f'node["{tag}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});' for tag in tags])}
      {''.join([f'way["{tag}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});' for tag in tags])}
      {''.join([f'relation["{tag}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});' for tag in tags])}
    );
    out body;
    """

    # Send request to Overpass API
    response = requests.post(overpass_url, data={'data': overpass_query})
    
    # Check for successful response
    if response.status_code == 200:
        return response.json().get('elements', [])
    else:
        print(f"Error fetching data: HTTP {response.status_code}")
        return []

# Loop through each bounding box and category
for category, tags in target_categories.items():
    for bbox in bounding_boxes:
        print(f"Fetching data for category '{category}' in bounding box {bbox}")
        elements = fetch_data(bbox, tags)
        
        # Process each element and categorize it
        for element in elements:
            tags = element.get('tags', {})
            business_info = {
                'name': tags.get('name', 'Unnamed'),
                'category': tags.get('amenity') or tags.get('shop') or tags.get('tourism') or category,
                'latitude': element.get('lat'),
                'longitude': element.get('lon')
            }
            categorized_data[category].append(business_info)

        # Pause between requests to avoid overwhelming the API
        time.sleep(1)

# Save each category to its own JSON file
for category, businesses in categorized_data.items():
    if businesses:  # Save only if the category has data
        filename = f"{category}_businesses.json"
        with open(filename, 'w') as json_file:
            json.dump(businesses, json_file, indent=4)
        print(f"Saved {len(businesses)} businesses in '{filename}'")