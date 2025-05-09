#IGNORE. USED FOR TESTING PURPOSES.

import json
import os
import re

def analyze_addresses():
    # WSL path to the directory containing JSON files
    directory = "/mnt/c/Users/danqw/Dropbox/PC/Downloads/batch/batch"
    
    # Iterate through all JSON files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            
            try:
                # Read and parse the JSON file
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Check if placeDetails exists and has an address
                if 'placeDetails' in data and data['placeDetails'].get('address'):
                    address = data['placeDetails']['address']
                    address_parts = [part.strip() for part in address.split(',')]
                    
                    # print(f"\nFile: {filename}")
                    # print(f"Business: {data['placeDetails'].get('name', 'Unknown Name')}")
                    # print("Address parts:")
                    if len(address_parts) > 6:
                        for i, part in enumerate(address_parts, 1):
                            print(f"{i}. {part}")
                        print("---")
            
            except json.JSONDecodeError as e:
                print(f"Error decoding {filename}: {e}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

def remove_emojis(string):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    return emoji_pattern.sub('', string)

def analyze_details():
    # WSL path to the directory containing JSON files
    directory = "/mnt/c/Users/danqw/Dropbox/PC/Downloads/batch/batch"
    
    # Compile the regex pattern
    url_pattern = "^\S+$"
    # Store strings that don't match but contain a dot
    non_matching_with_dot = []
    
    # Iterate through all JSON files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            
            try:
                # Read and parse the JSON file
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Check if placeDetails exists and has Details array
                if 'placeDetails' in data and 'Details' in data['placeDetails']:
                    for detail in data['placeDetails']['Details']:
                        if re.match(url_pattern, detail):
                            pass
                            # print(f"File: {filename}")
                            print(f"Matching URL: {remove_emojis(detail)}")
                            # print("---")
                        elif '.' in detail:
                            non_matching_with_dot.append({
                                'file': filename,
                                'detail': detail
                            })
            
            except json.JSONDecodeError as e:
                print(f"Error decoding {filename}: {e}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Print strings that don't match but contain a dot
    if non_matching_with_dot:
        print("\nStrings containing '.' that don't match the URL pattern:")
        for item in non_matching_with_dot:
            # print(f"\nFile: {item['file']}")
            print(f"String: {item['detail']}")

def analyze_prices():
    # WSL path to the directory containing JSON files
    directory = "/mnt/c/Users/danqw/Dropbox/PC/Downloads/batch/batch"
    
    # Track count of businesses with prices
    total_businesses = 0
    businesses_with_prices = 0
    
    # Iterate through all JSON files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            
            try:
                # Read and parse the JSON file
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                total_businesses += 1
                
                # Check if placeDetails exists and has a non-null price
                if 'placeDetails' in data and data['placeDetails'].get('price') is not None:
                    businesses_with_prices += 1
                    print(f"File: {filename}")
                    print(f"Business: {data['placeDetails'].get('name', 'Unknown Name')}")
                    print(f"Price: {data['placeDetails']['price']}")
                    print(f"Category: {data['placeDetails'].get('category', 'No Category')}")
                    print("---")
            
            except json.JSONDecodeError as e:
                print(f"Error decoding {filename}: {e}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Print summary statistics
    print("\nSummary:")
    print(f"Total businesses processed: {total_businesses}")
    print(f"Businesses with price information: {businesses_with_prices}")
    print(f"Percentage with prices: {(businesses_with_prices/total_businesses*100):.2f}%")


def analyze_dates():
    # Path to the directory containing JSON files
    directory = "/mnt/c/Users/danqw/Dropbox/PC/Downloads/batch/batch"
    
    # Time words to check against
    time_words = ['semana', 'mês', 'semanas', 'meses', 'ano', 'anos']
    
    # Iterate through all JSON files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            
            try:
                # Read and parse the JSON file
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Check if reviews exist and is a list
                if 'reviews' in data and isinstance(data['reviews'], list):
                    for review in data['reviews']:
                        if 'date' in review:
                            # Check if the date string contains any of the time words
                            date_string = review['date'].lower()
                            if not any(word in date_string for word in time_words):
                                print(f"File: {filename}")
                                print(f"Unusual date format: \"{review['date']}\"")
                                print(f"Review by: {review['user']}")
                                print("---")
            
            except json.JSONDecodeError as e:
                print(f"Error decoding {filename}: {e}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    # analyze_dates()
    # analyze_prices()
    # analyze_details()
    analyze_addresses()