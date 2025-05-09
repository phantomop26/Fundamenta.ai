from fuzzywuzzy import fuzz
import requests
import time
import pandas as pd
import numpy as np  # For NaN values

def fuzzy_match(string1, string2, threshold):
    '''
        - 'ratio': Simple ratio (default Levenshtein distance)
        - 'partial_ratio': Partial ratio for substring matching
        - 'token_sort_ratio': Token sorting before comparing
        - 'token_set_ratio': Token set ratio for out-of-order tokens
        - 'weighted': Average of token_sort_ratio and ratio
    '''

    if not isinstance(string1, str) or not isinstance(string2, str):
        raise TypeError("Both inputs must be strings")
    
  
    return fuzz.token_set_ratio(string1, string2) >= threshold




def get_location_details(address: str):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "addressdetails": 1}

    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()

    if not data:
        return None  # If no data found, return None

    location = data[0]
    lat, lon = float(location["lat"]), float(location["lon"])
    address_details = location.get("address", {})

    city = (
        address_details.get("city")
        or address_details.get("town")
        or address_details.get("village")
        or "Unknown"
    )
    postal_code = address_details.get("postcode", "Unknown")
    municipality = address_details.get(
        "municipality", address_details.get("county", "Unknown")
    )
    country = address_details.get("country", "Unknown")
    country_code = address_details.get("country_code", "Unknown")
    road = address_details.get("road", "Unknown")
    state = address_details.get("state", "Unknown")  # Additional info
    county = address_details.get("county", "Unknown")  # Additional info
    formatted_address = location.get(
        "display_name", "Unknown"
    )  # Full formatted address

    location_info = {
        "latitude": lat,
        "longitude": lon,
        "address": address,
        "road": road,
        "city": city,
        "municipality": municipality,
        "postal_code": postal_code,
        "country": country,
        "country_code": country_code,
        "state": state,  # Add state information
        "county": county,  # Add county information
        "formatted_address": formatted_address,  # Add formatted address
    }

    return location_info


def process_addresses(df, address_column="address"):
    data = []

    for address in df[address_column]:
        try:
            details = get_location_details(address)
            if details is None:
                # If no location found, append NaN for all fields
                details = {
                    key: np.nan
                    for key in [
                        "latitude",
                        "longitude",
                        "address",
                        "road",
                        "city",
                        "municipality",
                        "postal_code",
                        "country",
                        "country_code",
                        "state",
                        "county",
                        "formatted_address",
                    ]
                }
            data.append(details)
            time.sleep(0.1)  # Delay of 0.1 seconds between requests
        except Exception as e:
            # In case of any other error, append NaN for all fields
            print(f"Error for address {address}: {e}")
            details = {
                key: np.nan
                for key in [
                    "address",
                    "latitude",
                    "longitude",
                    "road",
                    "city",
                    "municipality",
                    "postal_code",
                    "country",
                    "country_code",
                    "state",
                    "county",
                    "formatted_address",
                    "error",
                ]
            }
            details["error"] = str(e)  # Add the error message
            data.append(details)

    # Convert the data into a DataFrame and concatenate it with the original
    location_df = pd.DataFrame(data)
    df_extended = pd.concat([df, location_df], axis=1)

    return df_extended


addresses = [
    "rua professor reinaldo dos santos",
    "Avenida 5 de Outubro, Nº 124 , Lisboa",
]

df = pd.DataFrame(addresses, columns=["address"])

df_extended = process_addresses(df)
df.head()
df_extended.head()
 