import polars as pl
import instaloader
import time
import random
import re
from urllib.parse import urlparse
import json
import ast
import os
import logging

# List of user agents to rotate through
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    
    # Chrome on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    
    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    
    # Firefox on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    
    # Safari on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    
    # Edge on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.66',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.52',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.128',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.112',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91',
    
    # Chrome on Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    
    # Firefox on Linux
    'Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
    
    # Mobile User Agents - iOS
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.6261.89 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.171 Mobile/15E148 Safari/604.1',
    
    # Mobile User Agents - Android
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.144 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.144 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; motorola edge 20 pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SAMSUNG SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/22.0 Chrome/111.0.0.0 Mobile Safari/537.36',
    
    # Tablets
    'Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-T500) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.144 Safari/537.36',
    
    # Older Browsers and Systems
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Mozilla/5.0 (X11; FreeBSD amd64; rv:95.0) Gecko/20100101 Firefox/95.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]

def check_first_part_match(text, address):
    # Normalize both strings - convert to lowercase
    normalized_text = text.lower().strip()
    normalized_address = address.lower().strip()
    
    # Find the longest substring match
    longest_match = ""
    
    # Only check substrings starting from the beginning of address
    i = 0
        
    # Try different lengths of substrings
    for j in range(i + 1, len(normalized_address) + 1):
        substring = normalized_address[i:j]
        
        # If substring is in text and longer than our current longest match
        if substring in normalized_text and len(substring) > len(longest_match):
            longest_match = substring
    
    # Return True if the longest match is greater than 5 characters
    return len(longest_match) > 6

def save_results():
    """Save results to CSV format."""
    global results
    global autoFailVerify
    
    # Save results to CSV format
    if results:
        
        
        # Define a safe conversion function for CSV
        def safe_convert(v):
            if isinstance(v, (dict, list)):
                try:
                    return json.dumps(v)
                except (TypeError, RecursionError):
                    return str(v)
            return v
        
        try:
            # Create a list to hold all rows
            all_rows = []
            
            # Process each profile result
        # for profile in results:
            profile = results[-1]
            csv_filename = "instagramInformation.csv" if profile['verified'] else "instagramInformationFAILED.csv"
            row = {
                # Start with original business columns
                "businessID": profile.get("BusinessID", ""),
                "gmapsURL": profile.get("gmapsURL", ""),
                "address": profile.get("address", ""),
                "category": profile.get("BusinessCategory", ""),
                "categoryGeneral": profile.get("categoryGeneral", ""),
                "name": profile.get("BusinessName", ""),
                "phone": profile.get("phone", ""),
                "website": profile.get("website", ""),
                "verified": profile.get("verified", "")
            }
            
            # Add all Instagram profile data fields
            for k, v in profile.items():
                # print(k,v)
                if k not in ["BusinessID", "BusinessName", "BusinessCategory"]:
                    row[k] = safe_convert(v)
            
            all_rows.append(row)
            
            # Create DataFrame with all fields
            profiles_df = pl.DataFrame(all_rows)
            # print(profiles_df)
            
            # Check if file exists to determine if we need to write headers
            file_exists = os.path.isfile(csv_filename)
            
            # Write to CSV (append mode if file exists)
            if file_exists:
                # Append without headers
                with open(csv_filename, 'a', encoding='utf-8') as f:
                    profiles_df.write_csv(f, include_header=False)
            else:
                # New file with headers
                with open(csv_filename, 'w', encoding='utf-8') as f:
                    profiles_df.write_csv(f)
            
            print(f"Saved {len(results)} profiles to {csv_filename}")
            
        except RecursionError as e:
            print(f"RecursionError during CSV conversion: {e}")
            print(f"Could not save profiles to CSV due to recursion error")
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            print(f"Could not save profiles to CSV")


def process_links(row, row_index, total_rows):
        """Process Instagram links for a single business row."""
        global autoFailVerify
        global instagramsSeen

        
        # Get the instagram links
        instagram_links = row["instagram_link"]
        business_id = row["businessID"]
        business_name = row["name"]
        
        # Select a random user agent for this row
        user_agent = random.choice(USER_AGENTS)
        
        # Initialize Instaloader with the random user agent
        L = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            user_agent=user_agent,
            max_connection_attempts=3
        )
        
        print(f"\nProcessing row {row_index+1}/{total_rows} - Business: {business_name}")
        print(f"Using User-Agent: {user_agent}")
        
        # Skip if no Instagram links or if it's not a string
        if not isinstance(instagram_links, str):
            print(f"Skipping {business_name}: Instagram link not a string")
            return
            
        # Try to parse the links - they might be in different formats
        try:
            # Print the raw value to debug
            # print(f"Raw instagram_links: {instagram_links}")
            
            # Handle various formats of links
            links = []
            
            # Case 1: String representation of a list with square brackets and quotes
            # Example: ['[https://instagram.com/example1', 'https://instagram.com/example2]']
            if instagram_links.startswith("['[") and instagram_links.endswith("]']"):
                # Remove the outer list notation
                cleaned = instagram_links[3:-3]  # Remove ['[ from start and ]'] from end
                
                # Handle any closing bracket in the last link
                if cleaned.endswith("]"):
                    cleaned = cleaned[:-1]
                
                # Split by comma and quote pattern
                split_links = []
                for link in cleaned.split("', '"):
                    link = link.strip()
                    # Make sure there's no trailing bracket
                    if link.endswith("]"):
                        link = link[:-1]
                    split_links.append(link)
                
                links.extend(split_links)
                # print(f"Parsed using list format case, found {len(links)} links")
            
            # Case 2: Curly braces format {link1,link2}
            elif instagram_links.startswith('{') and instagram_links.endswith('}'):
                cleaned = instagram_links[1:-1]  # Remove { and }
                split_links = [link.strip() for link in cleaned.split(',')]
                links.extend(split_links)
                # print(f"Parsed using curly braces format, found {len(links)} links")
            
            # Case 3: Try to parse as JSON/list using ast.literal_eval
            else:
                try:
                    # Try to use ast.literal_eval to safely parse
                    parsed = ast.literal_eval(instagram_links)
                    if isinstance(parsed, list):
                        links.extend(parsed)
                    else:
                        links.append(parsed)
                    # print(f"Parsed using ast.literal_eval, found {len(links)} links")
                except Exception as e:
                    print(f"Literal eval parsing failed: {e}")
                    # If all else fails, just split by commas and semicolons
                    split_links = [link.strip() for link in re.split(r'[,;]', instagram_links)]
                    links.extend(split_links)
                    print(f"Parsed using simple split, found {len(links)} links")
            
            # Clean up links - remove any remaining brackets or quotes
            cleaned_links = []
            for link in links:
                if isinstance(link, str):
                    # Remove any square brackets
                    if link.startswith('['):
                        link = link[1:]
                    if link.endswith(']'):
                        link = link[:-1]
                    # Remove any single quotes
                    link = link.strip("'")
                    
                    # Only add if it looks like a valid Instagram link
                    if 'instagram.com' in link:
                        cleaned_links.append(link)
            
            links = cleaned_links
            # print(f"Final cleaned links: {links}")
                
            # Ensure links is a list even if it's a single string
            if isinstance(links, str):
                links = [links]
                
            # Filter out empty strings
            links = [link for link in links if link]
                
                            # Process all Instagram links regardless of count
            print(f"\nBusiness: {business_name} (ID: {business_id}) - {len(links)} Instagram link(s) found")
            
            if not links:
                print(f"No valid Instagram links found for {business_name}")
                return
            for link_index, link in enumerate(links):
                # Skip empty links
                if not link or not isinstance(link, str):
                    continue
                    
                # Make sure the link is a valid Instagram URL
                if 'instagram.com' in link:
                    if link in instagramsSeen:
                        continue
                    else:
                        instagramsSeen.add(link) #do not repeat instagram checks.
                    print(f"Processing link {link_index+1}/{len(links)}: {link}")
                    try:
                        profile_data = download_profile_data(link, L)
                        contains = False
                        if not row['verified'] and row['businessID'] not in autoFailVerify:
                            toCheck = [row['website'], row['phone']] #, row['address']
                            for item in toCheck:
                               if not item:
                                   continue
                               if any(item in str(value) for value in profile_data.values() if value): # match in for the website or the phone number
                                   autoFailVerify.add(row['businessID'])
                                   profile_data['accuracyProb'] = 'high'
                                   contains = True
                                   break
                            else:
                                if any(row['name'].lower() in str(value).lower() for value in profile_data.values() if value):
                                    contains = True #if it it just a name match, we can not be certain so it is not added to autoFailVerify

                                if any(check_first_part_match(str(value), row['address']) for value in profile_data.values() if value):
                                    autoFailVerify.add(row['businessID']) #the instagram has already been found. do not continue checking.
                                    profile_data['accuracyProb'] = 'high'
                                    contains = True

                            

                                        
                            
                            
                        if profile_data:
                            # Add business info to profile data
                            profile_data["BusinessID"] = business_id
                            profile_data["BusinessName"] = business_name
                            profile_data["gmapsURL"] = row['gmapsURL']
                            profile_data["gmapsURL"] = row['gmapsURL']
                            profile_data["address"] = row['address']
                            profile_data["categoryGeneral"] = row['categoryGeneral']
                            profile_data["phone"] = row['phone']
                            # profile_data['instagram_link_verified'] = row['instagram_link']
                            profile_data["website"] = row['website']
                            profile_data["verified"] = row['verified'] if row['verified'] else contains
                            profile_data['accuracyProb'] = row['accuracyProb']
                            
                            # Add category if available
                            if "category" in row:
                                profile_data["BusinessCategory"] = row["category"]
                            results.append(profile_data)
                            # Save results after each profile to avoid losing data
                            save_results()
                            
                            # Add varying delay between fetching profiles from the same business
                            if link_index < len(links) - 1:
                                delay = random.uniform(5, 15) 
                                print(f"Waiting {delay:.2f} seconds before next profile...")
                                time.sleep(delay)
                        else:
                            print(f"No profile data returned for {link}")
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        print(f"Error processing link {link}: {e}")
                else:
                    print(f"Skipping invalid Instagram link: {link}")
        except Exception as e:
            print(f"Error processing links for {business_name}: {e}")
    

# Reusing your provided functions
def extract_username_from_url(url):
    """Extract username from an Instagram profile URL."""
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Check if this is an Instagram URL
    if 'instagram.com' not in parsed_url.netloc:
        raise ValueError(f"Not an Instagram URL: {url}")
    
    # Get the path and remove leading/trailing slashes
    path = parsed_url.path.strip('/')
    
    # The username should be the first part of the path
    # Ignore special paths like 'p' (posts), 'explore', etc.
    if path and path not in ['p', 'explore', 'reels', 'stories']:
        # Remove trailing slash if any and get the username
        username = path.split('/')[0]
        return username
    else:
        raise ValueError(f"Could not extract a valid username from this URL: {url}")

def extract_links_from_bio(bio_text):
    """Extract links from a biography text."""
    # Regular expression to find URLs in text
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    return re.findall(url_pattern, bio_text)

def random_delay(min_seconds, max_seconds):
    """Add a random delay between operations to mimic human behavior."""
    # Add some randomness to the delay range (±20%)
    min_seconds = min_seconds * (0.8 + 0.4 * random.random())
    max_seconds = max_seconds * (0.8 + 0.4 * random.random())
    
    # Generate the random delay within the adjusted range
    delay = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def download_profile_data(profile_url, L, max_comments_per_post=50):
    """Download data from a single Instagram profile."""
    try:
        # Extract username from URL
        username = extract_username_from_url(profile_url)
        print(f"\n{'='*50}")
        print(f"Processing profile: {username} from {profile_url}")
        print(f"{'='*50}")
        
        # Add a random delay before starting
        random_delay(5, 15)  # Reduced delay for testing
        
        # Get profile
        print(f"Fetching profile information for {username}...")
        profile = instaloader.Profile.from_username(L.context, username)
        
        # Extract and save links from bio
        bio_links = extract_links_from_bio(profile.biography)
        
        profile_info = {
            "URL": profile_url,
            "Username": profile.username,
            "Full Name": profile.full_name.replace("\n", " ") if profile.full_name else "",
            "Biography": profile.biography.replace("\n", " ") if profile.biography else "",
            "External URL": profile.external_url.replace("\n", " ") if profile.external_url else "",
            "Followers": profile.followers,
            "Following": profile.followees,
            "Posts Count": profile.mediacount,
            "Is_Private": profile.is_private,
        }
        # print(profile_info)
        return profile_info
        
    except Exception as e:
        print(f"An error occurred processing {profile_url}: {e}")
        return {
            "URL": profile_url,
            "Error": str(e),
        }

def main():
    # Initialize global results list
    global results
    global autoFailVerify
    global instagramsSeen
    results = []
    autoFailVerify = set()
    instagramsSeen = set()

    
    # Create output directory if it doesn't exist
    
    # Read the CSV file using Polars
    logging.info("Reading CSV file...")
    try:
        # Read with explicit schema to handle the format of the data
        df = pl.read_csv(
            "COMPLETEinstaTesting.csv",
            has_header=True,
            infer_schema_length=None,
            # Try to parse the Instagram links as strings to preserve the format
            dtypes={"instagram_link": pl.Utf8}

        )
        logging.info(f"Successfully loaded CSV with {df.shape[0]} rows")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return
    
    # Check if the required columns exist
    if "instagram_link" not in df.columns:
        logging.error("Error: 'instagram_link' column not found in CSV")
        return
    
    # Process each row in the dataframe with a row index for tracking progress
    for i, row in enumerate(df.iter_rows(named=True)):
        
        try:
            process_links(row, i, df.shape[0])
        except Exception as e:
            logging.error(f"Error processing row {i+1}: {e}")
            # Continue with the next row instead of aborting the whole script
            continue
        
        # Add extra delay between businesses to be more human-like
        if i < df.shape[0]-1:  # Not the last row
            delay = random.uniform(10, 30)
            logging.info(f"Moving to next business in {delay:.2f} seconds...")
            time.sleep(delay)
    
    # Final save
    save_results()
    logging.info("Finished processing all businesses with Instagram links.")
  
