
import requests
import geopandas as gpd
from geopy.geocoders import Nominatim
from time import sleep

# Set up geolocator
geolocator = Nominatim(user_agent="company_locator")

# Overpass API URL
overpass_url = "http://overpass-api.de/api/interpreter"

   
# Full list of company names to search for
company_names = [
     "Urban Outfitters", "J.Crew", "Gap", "Mango", "COS", "Topshop", "Forever 21", "American Eagle", "PacSun", "Uniqlo",
     "Boohoo", "Nasty Gal", "Missguided", "PrettyLittleThing", "Bershka", "Pull&Bear", "Charlotte Russe",
     "Abercrombie & Fitch", "Zara", "H&M", "Reformation", "Everlane", "Anthropologie", "Madewell", "Free People", "Vince",
    "AllSaints", "Zadig & Voltaire", "Equipment", "Helmut Lang", "Tibi", "3.1 Phillip Lim", "Alice + Olivia", "IRO",
    "Isabel Marant", "Alexander Wang", "Rag & Bone", "Theory", "Club Monaco", "Maje & Sandro", "NAP (Net-a-Porter)", 
    "Farfetch", "Zalando", "Fashion Nova", "In The Style", "Miss Selfridge", "SHEIN", "Lulus", "ModCloth", "ASOS", 
    "Revolve", "Shopbop", "Fabletics", "Sweaty Betty", "Girlfriend Collective", "Beyond Yoga", "Athleta", "Vuori", 
    "Lorna Jane", "Varley", "Carbon38", "PE Nation", "Lululemon", "Alo Yoga", "Outdoor Voices", "Nordstrom", 
    "Bloomingdale’s", "Saks Fifth Avenue", "Patagonia", "Outerknown", "Allbirds", "Banana Republic", "Old Navy", 
    "Hollister", "Victoria’s Secret", "Pink", "Talbots", "Chico’s", "Ann Taylor", "LOFT", "J.Jill", "Brooks Brothers", 
    "Tory Burch", "Kate Spade", "Michael Kors", "Coach", "Ralph Lauren", "Tommy Hilfiger", "Calvin Klein", "Diesel", 
    "Levi’s", "Guess", "True Religion", "Lucky Brand", "DKNY", "Marc Jacobs", "Loft", "A Pea in the Pod", "Torrid", 
    "Lane Bryant", "Cato Fashions", "Dressbarn", "Maurices", "NY & Company", "Chico’s", "White House Black Market", 
    "The Limited", "Avenue", "Talbots", "Coldwater Creek", "Soft Surroundings", "Chico's Off the Rack", "Vineyard Vines", 
    "Lilly Pulitzer", "Francesca’s", "Cache", "Free People", "Soma", "Justice", "Boden", "J.Jill", "ModCloth", 
    "Kendra Scott", "Ann Taylor", "Lane Bryant", "Eileen Fisher", "Frette", "Earthbound Trading Co.", "Anthropologie", 
    "Lulus", "Cotton On", "Garage", "Ardene", "Zales", "Kay Jewelers", "David’s Bridal", "Pandora", "Kendra Scott", 
    "Alex and Ani", "Tiffany & Co.", "Swarovski", "James Avery", "Jared", "Claire’s", "Charming Charlie", "Fossil", 
    "Brighton", "The Buckle", "Spencer’s", "Claire’s", "Aldo", "DSW (Designer Shoe Warehouse)", "Steve Madden", 
    "Foot Locker", "Journeys", "Finish Line", "Nike", "Adidas", "Under Armour", "Puma", "New Balance", "Skechers", 
    "Vans", "Converse", "L.L.Bean", "Eddie Bauer", "Columbia Sportswear", "The North Face", "Patagonia", "REI", 
    "Timberland", "Dr. Martens", "UGG Australia", "Crocs", "Birkenstock", "Clarks", "Merrell", "Hush Puppies", 
    "Skechers", "Crocs", "Famous Footwear", "Payless", "Zappos", "Dick's Sporting Goods", "Academy Sports + Outdoors", 
    "Cabela’s", "Bass Pro Shops", "Orvis"
]

bounding_boxes = {
    "europe": [36.0, -11.0, 71.0, 40.0],  
    "north_america": [15.0, -170.0, 72.0, -50.0],  
    "asia": [-10.0, 25.0, 55.0, 180.0],  
    "australia": [-45.0, 110.0, -10.0, 180.0],  
    "africa": [-35.0, -20.0, 37.0, 52.0],  
    "south_america": [-60.0, -90.0, 12.0, -30.0], 
}


for company in company_names:
    for region_name, bbox in bounding_boxes.items():
        print(f"Fetching data for {company} in {region_name}...")
        query = f"""
        [out:json][timeout:1800];
        (
            node["name"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            way["name"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            relation["name"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            node["brand"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            way["brand"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            relation["brand"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            node["shop"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            way["shop"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            relation["shop"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            node["operator"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            way["operator"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            relation["operator"="{company}"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out body;
        >;
        out skel qt;
        """

        response = requests.get(overpass_url, params={'data': query})
        locations = []
        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])
            
            for el in elements:
                lat = el.get('lat')
                lon = el.get('lon')
                if lat and lon:
                    name = el.get('tags', {}).get('name', company)
                    street = el.get('tags', {}).get('addr:street', '')
                    city = el.get('tags', {}).get('addr:city', '')
                    postcode = el.get('tags', {}).get('addr:postcode', '')
                    address = f"{street}, {city}, {postcode}"
                    
                    if not street and not city and not postcode:
                        try:
                            location = geolocator.reverse((lat, lon), timeout=10)
                            address = location.address if location else 'Not found'
                        except Exception as e:
                            address = 'Not found'
                        sleep(1) 
                    locations.append((lat, lon, name, address))

            if locations:
                gdf = gpd.GeoDataFrame(locations, columns=['latitude', 'longitude', 'name', 'address'])
                
                gdf.to_csv(f'{company.replace(" ", "_").replace("/", "_")}_{region_name}_locations.csv', index=False)
                print(f"Saved {company} data for {region_name} to {company.replace(" ", "_").replace("/", "_")}_{region_name}_locations.csv")
            else:
                print(f"No data found for {company} in {region_name}.")
        else:
            print(f"Error with Overpass API for {company} in {region_name}: {response.status_code}")
