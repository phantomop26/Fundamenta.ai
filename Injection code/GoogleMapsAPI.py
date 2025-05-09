
import requests
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle




def geocode_address(address, api_key):
    """
    Convert an address to latitude and longitude using Google Maps Geocoding API
    
    Args:
        address (str): The address to geocode
        api_key (str): Your Google Maps API key
        
    Returns:
        tuple: (latitude, longitude) coordinates
    """
    # Prepare the API request
    endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }
    
    # Make the request
    response = requests.get(endpoint, params=params)
    
    # Parse the response
    if response.status_code == 200:
        data = response.json()
        
        # Check if the request was successful
        if data["status"] == "OK":
            # Extract the latitude and longitude
            location = data["results"][0]["geometry"]["location"]
            latitude = location["lat"]
            longitude = location["lng"]
            
            return (latitude, longitude)
        else:
            print(f"Geocoding error: {data['status']}")
            return None
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None

def get_credentials():
    """
    Load credentials from token.pickle or client_secrets.json
    
    Returns:
        Credentials: Google API credentials
    """
    creds = None
    
    # Check if token.pickle exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials don't exist or are invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json',
                scopes=['https://www.googleapis.com/auth/maps']
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def main():
    # Load API key from environment variable or input
    api_key = 'AIzaSyBNlRi0I8e1rSme62Vut7mdHMOZ5d82prQ'
    
    # Get credentials (optional, depends on your API usage)
    # creds = get_credentials()
    addresses = ['Blvd. Venustiano Carranza 3940, Villa Olímpica, 25230 Saltillo, Coah., Mexico']

    for address in addresses:
        coordinates = geocode_address(address, api_key)
    
        if coordinates:
            latitude, longitude = coordinates
            print(f"\nAddress: {address}")
            print(f"Latitude: {latitude}")
            print(f"Longitude: {longitude}")
            print(f"Google Maps link: https://www.google.com/maps?q={latitude},{longitude}")

if __name__ == "__main__":
    main()