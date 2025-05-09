# import subprocess
# import json
# import csv
# import time
# import os
# from typing import List, Dict, Optional

# def geocode_addresses(addresses, output_file: str = "geocoded_results.csv", 
#                        temp_js_file: str = "temp_geocode.js", delay = 1) -> None:
#     """
#     Geocode a list of addresses by calling the Node.js geocoding script for each address.
    
#     Args:
#         addresses: List of tuples containing (id, address) to geocode
#         output_file: CSV file to save results
#         temp_js_file: Temporary JS file that will be created for each address
#         delay: Time delay between API calls in seconds (to avoid rate limiting)
#     """
#     api_key = "AIzaSyBNlRi0I8e1rSme62Vut7mdHMOZ5d82prQ"  # Replace with your actual API key

#     # Track total processing time
#     total_start_time = time.time()
    
#     # Check if output file exists and get existing IDs
#     existing_ids = set()
#     if os.path.exists(output_file):
#         with open(output_file, 'r', newline='', encoding='utf-8') as csvfile:
#             reader = csv.reader(csvfile)
#             header = next(reader, None)  # Skip header row
#             if header:  # If file is not empty
#                 for row in reader:
#                     if row and len(row) > 0:  # Make sure row has data
#                         existing_ids.add(row[0])  # Assuming ID is the first column
    
#     # Create/open the output CSV file in append mode
#     with open(output_file, 'a', newline='') as csvfile:
#         fieldnames = ['id', 'address', 'latitude', 'longitude']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
#         # Write header if file was just created
#         if not os.path.getsize(output_file):
#             writer.writeheader()
        
#         for i, (id, address) in enumerate(addresses):
#             # Skip if ID already exists in CSV
#             if id in existing_ids:
#                 print(f"Skipping ID {id} as it already exists in {output_file}")
#                 continue
                
#             print(f"Processing address {i+1}/{len(addresses)}: {address}")
            
#             # Start timing for this address
#             start_time = time.time()
            
#             # Create a temporary JS file for this specific address
#             create_temp_js_file(address, api_key, temp_js_file)
            
#             # Run the Node.js script and capture the output
#             try:
#                 result = subprocess.run(['node', temp_js_file], 
#                                         capture_output=True, 
#                                         text=True, 
#                                         check=True)
                
#                 # Parse the output to get coordinates
#                 coords = parse_coordinates(result.stdout)
                
#                 # Calculate processing time
#                 end_time = time.time()
#                 processing_time = end_time - start_time
                
#                 if coords:
#                     # Write results to CSV
#                     writer.writerow({
#                         'id': id,
#                         'address': address,
#                         'latitude': coords['lat'],
#                         'longitude': coords['lng']
#                     })
#                     # print(f"  ✓ Successfully geocoded: {coords['lat']}, {coords['lng']}")
#                     # print(f"    Processed in {processing_time:.2f} seconds")
#                 else:
#                     print(f"  ✗ No coordinates found for address {address}")
#                     # print(f"    Processed in {processing_time:.2f} seconds")
                
#             except subprocess.CalledProcessError as e:
#                 # Calculate processing time even for errors
#                 end_time = time.time()
#                 processing_time = end_time - start_time
                
#                 print(f"  ✗ Error processing address: {e}")
#                 print(f"  ✗ Error output: {e.stderr}") 
#                 print(f"    Processed in {processing_time:.2f} seconds")
            
#             # Clean up the temporary file
#             if os.path.exists(temp_js_file):
#                 os.remove(temp_js_file)
                
#             # Add delay to avoid hitting API rate limits
#             if i < len(addresses) - 1:  # No need to delay after the last address
#                 time.sleep(delay)
    
#     # Calculate total processing time
#     total_end_time = time.time()
#     total_processing_time = total_end_time - total_start_time
    
#     print(f"Geocoding complete. Results saved to {output_file}")
#     print(f"Total processing time: {total_processing_time:.2f} seconds for {len(addresses)} addresses")
#     print(f"Average time per address: {total_processing_time/len(addresses):.2f} seconds")


# def create_temp_js_file(address: str, api_key: str, filename: str) -> None:
#     """
#     Create a temporary JavaScript file that calls the geocoding function with a specific address.
    
#     Args:
#         address: The address to geocode
#         api_key: Google Maps API key
#         filename: Name of the temporary JS file to create
#     """
#     # Properly escape the address string for JavaScript
#     address_escaped = json.dumps(address)[1:-1]  # json.dumps adds quotes, so remove them
    
#     js_code = f'''const axios = require('axios');

# async function getCoordinatesWithAxios(address, apiKey) {{
#   try {{
#     const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${{encodeURIComponent(address)}}&key=${{apiKey}}`;
#     const response = await axios.get(url);
    
#     const {{ results }} = response.data;
    
#     if (results && results.length > 0) {{
#       const location = results[0].geometry.location;
#       return {{
#         lat: location.lat,
#         lng: location.lng
#       }};
#     }} else {{
#       console.log("No results found");
#     }}
#   }} catch (error) {{
#     console.log("Geocoding failed: " + error.message);
#   }}
# }}

# const address = "{address_escaped}";
# const API_KEY = "{api_key}";

# getCoordinatesWithAxios(address, API_KEY)
#   .then(coordinates => {{
#     console.log(JSON.stringify(coordinates));
#   }})
#   .catch(error => {{
#     console.error(error);
#   }});
# '''
    
#     with open(filename, 'w', encoding='utf-8') as f:
#         f.write(js_code)


# def parse_coordinates(output: str) -> Optional[Dict[str, float]]:
#     """
#     Parse the JSON output from the Node.js script to extract coordinates.
    
#     Args:
#         output: String output from the Node.js script
    
#     Returns:
#         Dictionary with lat and lng keys, or None if parsing failed
#     """
#     try:
#         # Find the JSON object in the output
#         for line in output.strip().split('\n'):
#             if line.startswith('{') and line.endswith('}'):
#                 return json.loads(line)
#     except json.JSONDecodeError:
#         print(f"Failed to parse coordinates from output: {output}")
    
#     return None


# # if __name__ == "__main__":
# #     # Your Google Maps API key
    
# #     # List of addresses to geocode
# #     addresses = [
# #         "1600 Amphitheatre Parkway, Mountain View, CA",
# #         "Blvd. Venustiano Carranza 3940, Villa Olímpica, 25230 Saltillo, Coah., Mexico",
# #         "350 5th Ave, New York, NY 10118",  # Empire State Building
# #         "Eiffel Tower, Paris, France",
# #         "Sydney Opera House, Sydney, Australia"
# #     ]
    
# #     # You can also load addresses from a file
# #     # with open("addresses.txt", "r", encoding="utf-8") as f:
# #     #     addresses = [line.strip() for line in f if line.strip()]
    
# #     # Run the geocoding process
# #     geocode_addresses(addresses, API_KEY, delay = 0)

import os
import csv
import time
import asyncio
import subprocess
from typing import List, Tuple, Dict, Optional, Set
import aiofiles


async def geocode_addresses(addresses: List[Tuple[str, str]], 
                           output_file: str = "geocoded_results.csv",
                           temp_js_file_prefix: str = "temp_geocode_",
                           max_concurrent: int = 5,
                           delay: float = 0.2) -> None:
    """
    Asynchronously geocode a list of addresses by calling the Node.js geocoding script.
    
    Args:
        addresses: List of tuples containing (id, address) to geocode
        output_file: CSV file to save results
        temp_js_file_prefix: Prefix for temporary JS files that will be created
        max_concurrent: Maximum number of concurrent geocoding operations
        delay: Time delay between API calls in seconds (to avoid rate limiting)
    """
    api_key = "AIzaSyBNlRi0I8e1rSme62Vut7mdHMOZ5d82prQ"  # Replace with your actual API key

    # Track total processing time
    total_start_time = time.time()
    
    # Check if output file exists and get existing IDs
    existing_ids = await get_existing_ids(output_file)
    
    # Create output file with header if it doesn't exist
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        async with aiofiles.open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            await csvfile.write('id,address,latitude,longitude\n')
    
    # Filter out addresses that have already been processed
    addresses_to_process = [(id, address) for id, address in addresses if id not in existing_ids]
    print(f"Processing {len(addresses_to_process)} addresses out of {len(addresses)} total")
    
    # Create a semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create tasks for each address
    tasks = []
    for i, (id, address) in enumerate(addresses_to_process):
        # Create a unique temp file name for each task
        temp_js_file = f"{temp_js_file_prefix}{i}.js"
        # Add a small delay between task creations to avoid overwhelming the API
        task_delay = i * delay if delay > 0 else 0
        
        task = asyncio.create_task(
            process_address(i, id, address, api_key, temp_js_file, output_file, 
                           semaphore, task_delay, len(addresses_to_process))
        )
        tasks.append(task)
    
    # Wait for all tasks to complete
    if tasks:
        await asyncio.gather(*tasks)
    
    # Calculate total processing time
    total_end_time = time.time()
    total_processing_time = total_end_time - total_start_time
    
    print(f"\nGeocoding complete. Results saved to {output_file}")
    print(f"Total processing time: {total_processing_time:.2f} seconds for {len(addresses)} addresses")
    if addresses_to_process:
        print(f"Average time per processed address: {total_processing_time/len(addresses_to_process):.2f} seconds")


async def get_existing_ids(output_file: str) -> Set[str]:
    """Get set of IDs that have already been processed."""
    existing_ids = set()
    if os.path.exists(output_file):
        async with aiofiles.open(output_file, 'r', newline='', encoding='utf-8') as csvfile:
            content = await csvfile.read()
            lines = content.splitlines()
            if lines:  # If file is not empty
                # Skip header
                for line in lines[1:]:
                    if line:  # Make sure line has data
                        row = line.split(',')
                        if row and len(row) > 0:  # Make sure row has data
                            existing_ids.add(row[0])  # Assuming ID is the first column
    return existing_ids


async def create_temp_js_file(address: str, api_key: str, temp_js_file: str) -> None:
    """Create a temporary JS file for geocoding a specific address."""
    js_content = f"""
const {{ Client }} = require("@googlemaps/google-maps-services-js");

const client = new Client({{}});

async function geocode() {{
  try {{
    const response = await client.geocode({{
      params: {{
        address: "{address.replace('"', '\\"')}",
        key: "{api_key}"
      }}
    }});

    if (response.data.results && response.data.results.length > 0) {{
      const location = response.data.results[0].geometry.location;
      console.log(JSON.stringify(location));
    }} else {{
      console.log("No results found");
    }}
  }} catch (error) {{
    console.error("Error:", error.message);
  }}
}}

geocode();
"""
    async with aiofiles.open(temp_js_file, 'w', encoding='utf-8') as f:
        await f.write(js_content)


async def process_address(index: int, id: str, address: str, api_key: str, 
                         temp_js_file: str, output_file: str, 
                         semaphore: asyncio.Semaphore, delay: float,
                         total_count: int) -> None:
    """Process a single address asynchronously."""
    # Add delay if specified
    if delay > 0:
        await asyncio.sleep(delay)
    
    # Use semaphore to limit concurrent operations
    async with semaphore:
        print(f"Processing address {index+1}/{total_count}: {address}")
        start_time = time.time()
        
        try:
            # Create temporary JS file
            await create_temp_js_file(address, api_key, temp_js_file)
            
            # Run Node.js script
            proc = await asyncio.create_subprocess_exec(
                'node', temp_js_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = await proc.communicate()
            
            # Parse coordinates
            coords = parse_coordinates(stdout)
            
            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time
            
            if coords and proc.returncode == 0:
                # Write results to CSV (need to acquire a lock for this)
                await write_to_csv(output_file, id, address, coords)
                print(f"  ✓ Successfully geocoded address {index+1}: {coords['lat']}, {coords['lng']} ({processing_time:.2f}s)")
            else:
                print(f"  ✗ No coordinates found for address {index+1}: {address} ({processing_time:.2f}s)")
                if stderr:
                    print(f"    Error: {stderr}")
                
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"  ✗ Error processing address {index+1}: {e} ({processing_time:.2f}s)")
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_js_file):
                try:
                    os.remove(temp_js_file)
                except:
                    pass


def parse_coordinates(output: str) -> Optional[Dict[str, float]]:
    """Parse coordinates from the output of the Node.js script."""
    if not output or "No results found" in output:
        return None
    
    try:
        import json
        # Strip any extra output before the JSON
        json_start = output.find('{')
        if json_start >= 0:
            output = output[json_start:]
        return json.loads(output)
    except Exception:
        print(f"Failed to parse output: {output}")
        return None


async def write_to_csv(output_file: str, id: str, address: str, coords: Dict[str, float]) -> None:
    """Write geocoding results to CSV file with file locking to prevent conflicts."""
    async with aiofiles.open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
        line = f"{id},{address.replace(',', ' ')},{coords['lat']},{coords['lng']}\n"
        await csvfile.write(line)


# Example usage:
# if __name__ == "__main__":
#     addresses = [("1", "1600 Amphitheatre Parkway, Mountain View, CA"), 
#                  ("2", "1 Infinite Loop, Cupertino, CA")]
#     asyncio.run(geocode_addresses(addresses, max_concurrent=2))