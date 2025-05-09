import psycopg2
from psycopg2 import sql
import time
import pandas as pd
import json
import os
import csv
from collections import defaultdict
from functions.downloadFunctions import (
    get_drive_service,
    get_zip_files,
    download_zip,
    extract_and_process_jsons,
)
from functions.instagramScrape import scrapeURL
from functions.hashingFunctions import hash_to_uuid



def close_db_connection(conn, cursor):
    """Close cursor and connection to database."""
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()
        print("Database connection closed")

def update_shopping_center_business_counts(conn, cursor):
    """Update business counts for shopping centers in the database."""

    if conn is None or cursor is None:
        return
    
    try:
        # First, get counts of businesses grouped by shoppingCenterID
        cursor.execute("""
            SELECT "shoppingCenterID", COUNT(*) as business_count
            FROM business
            WHERE "shoppingCenterID" IS NOT NULL
            GROUP BY "shoppingCenterID"
        """)
        
        # Fetch all results
        shopping_center_counts = cursor.fetchall()
        
        # For each shopping center, update the business count only for existing entries
        for shopping_center_id, count in shopping_center_counts:
            # Update only if the row exists in ShoppingCenterBusinesses
            cursor.execute("""
                UPDATE ShoppingCenterBusinesses
                SET "businessCount" = %s
                WHERE "shoppingCenterID" = %s
            """, (count, shopping_center_id))
            
            # Check if any row was updated
            if cursor.rowcount > 0:
                print(f"Updated shopping center {shopping_center_id} with {count} businesses")
            else:
                print(f"Shopping center {shopping_center_id} not found in ShoppingCenterBusinesses table")
        
        # Commit the transaction
        conn.commit()
        print("Successfully updated all shopping center business counts")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
        if conn is not None:
            conn.rollback()
    




def analyze_business_substrings(conn, cursor):
    """
    Connects to database, executes query, and analyzes business data to find cases
    where businesses sharing the same URL have names where one is a prefix of another.
    
    This function handles the entire process:
    1. Connecting to the database
    2. Executing the SQL query to find businesses sharing URLs
    3. Processing the results to find prefix matches (one name starts with the other)
    4. Printing statistics and match details
    5. Tracking chain businesses and ensuring consistent locationCount across all chain members
    6. Updating the business table to set isChain=True and locationCount for chain businesses
    
    Ensures accurate locationCount values match the actual number of locations in each chain.
    
    Note: Requires get_db_config() and connect_to_db() functions to be defined elsewhere
    """
    # # Get database configuration
    # config = get_db_config()
    
    # # Connect to the PostgreSQL database
    # conn, cursor = connect_to_db(config)
    
    try:
        # SQL query to get businesses sharing a URL with contact counts
        query = """
        WITH contact_counts AS (
            SELECT 
                contact."businessURL",
                COUNT(*) AS contact_count
            FROM 
                contact
            WHERE 
                contact."businessURL" IS NOT NULL
            GROUP BY 
                contact."businessURL"
            HAVING 
                COUNT(*) > 1
        )
        SELECT 
            b."businessID", b."name",
            c."businessURL",
            cc.contact_count
        FROM 
            business b
        JOIN 
            contact c ON b."businessID" = c."businessID"
        JOIN 
            contact_counts cc ON c."businessURL" = cc."businessURL"
        ORDER BY 
            cc.contact_count DESC;
        """
        
        # Execute the query
        cursor.execute(query)
        
        # Convert query results to DataFrame
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        # Group by businessURL
        url_groups = defaultdict(list)
        
        # Create groups based on matching businessURL
        for _, row in df.iterrows():
            business_id = row['businessID']
            name = row['name'].lower().strip()  # Normalize by lowercasing and stripping whitespace
            business_url = row['businessURL']
            
            url_groups[business_url].append((business_id, name))
        
        # Track all business IDs and names in the dataset
        all_business_ids = set()
        business_name_map = {}  # Map business IDs to original names
        business_lower_map = {}  # Map business IDs to lowercase names
        
        # Fill the tracking maps
        for _, row in df.iterrows():
            business_id = row['businessID']
            all_business_ids.add(business_id)
            business_name_map[business_id] = row['name']  # Original name
            business_lower_map[business_id] = row['name'].lower().strip()  # Lowercase name
        
        # Counter for prefix matches
        prefix_count = 0
        matching_pairs = []
        
        # Keep track of matched pairs to avoid duplicates
        matched_pairs = set()
        
        # Track businesses in the same chain (based on prefix matching)
        chain_groups = defaultdict(set)
        
        # Process each URL group
        for url, businesses in url_groups.items():
            # Skip if only one business with this URL
            if len(businesses) <= 1:
                continue
                
            # Check all pairs of businesses in this URL group
            for i in range(len(businesses)):
                for j in range(i+1, len(businesses)):
                    id1, name1 = businesses[i]
                    id2, name2 = businesses[j]
                    
                    # Create a unique identifier for this pair
                    pair_id = frozenset([id1, id2])
                    
                    # Check if one name begins with the other (prefix match)
                    if name1.startswith(name2) or name2.startswith(name1):
                        # Check if we've already counted this pair
                        if pair_id not in matched_pairs:
                            prefix_count += 1
                            matching_pairs.append((id1, name1, id2, name2, url))
                            matched_pairs.add(pair_id)
                            
                            # Group these businesses into the same chain
                            chain_id = min(id1, id2)
                            chain_groups[chain_id].add(id1)
                            chain_groups[chain_id].add(id2)
        
        # Merge chain groups that share common businesses
        # Use an iterative approach to ensure full merging
        merged = True
        while merged:
            merged = False
            chain_ids = list(chain_groups.keys())
            
            for i in range(len(chain_ids)):
                for j in range(i+1, len(chain_ids)):
                    id1 = chain_ids[i]
                    id2 = chain_ids[j]
                    
                    # Skip if either chain has been processed already
                    if id1 not in chain_groups or id2 not in chain_groups:
                        continue
                        
                    # Check for intersection
                    if chain_groups[id1].intersection(chain_groups[id2]):
                        # Merge chains
                        chain_groups[id1].update(chain_groups[id2])
                        del chain_groups[id2]
                        merged = True
                        break
                        
                if merged:
                    break
        
        # Convert to list of sets for easier handling
        merged_chains = list(chain_groups.values())
        
        # Print results
        print(f"Total number of business pairs with prefix name matches: {prefix_count}")
        print(f"Number of distinct chain groups: {len(merged_chains)}")
        
        # Process each chain
        for chain in merged_chains:
            chain_size = len(chain)
            chain_ids_list = list(chain)
            
            # Skip if only one business (not a chain)
            if chain_size <= 1:
                continue
                
            # Print chain information for debugging
            print(f"\nChain with {chain_size} locations:")
            for business_id in chain_ids_list:
                print(f"  - {business_name_map.get(business_id, 'Unknown')}")
            
            # Check for additional chain members by prefix matching
            # For each business in the chain, check for other businesses with prefix relationship
            current_chain = set(chain_ids_list)
            additions_found = True
            
            while additions_found:
                additions_found = False
                current_chain_copy = set(current_chain)
                
                # Check every business in our dataset against our current chain
                for chain_id in current_chain_copy:
                    chain_name = business_lower_map.get(chain_id, '').lower().strip()
                    
                    for other_id in all_business_ids:
                        # Skip if already in chain
                        if other_id in current_chain:
                            continue
                            
                        other_name = business_lower_map.get(other_id, '').lower().strip()
                        
                        # Check for prefix relationship
                        if chain_name.startswith(other_name) or other_name.startswith(chain_name):
                            current_chain.add(other_id)
                            additions_found = True
                
                # If we found additions, update the chain size
                if additions_found:
                    chain_size = len(current_chain)
                    chain_ids_list = list(current_chain)
                    print(f"Chain expanded to {chain_size} locations")
            
            # Create placeholders for the IN clause
            placeholders = ', '.join(['%s'] * chain_size)
            
            # Update the business table for all chain members
            update_query = f"""
            UPDATE business
            SET "chain" = TRUE, "locationCount" = %s
            WHERE "businessID" IN ({placeholders})
            """
            
            try:
                # Execute the update query with all parameters
                cursor.execute(update_query, [chain_size] + chain_ids_list)
                
                # Get the number of rows updated
                updated_rows = cursor.rowcount
                print(f"Updated {updated_rows} businesses in this chain with locationCount = {chain_size}")
                
                
                # Verify the update
                verify_query = f"""
                SELECT "businessID", "name", "chain", "locationCount" 
                FROM business 
                WHERE "businessID" IN ({placeholders})
                ORDER BY "name"
                """
                cursor.execute(verify_query, chain_ids_list)
                verification_results = cursor.fetchall()
                print("Chain members after update:")
                for result in verification_results:
                    print(f"  ID: {result[0]}, Name: {result[1]}, Chain: {result[2]}, LocationCount: {result[3]}")
                
            except Exception as e:
                print(f"Error updating chain: {e}")
                conn.rollback()
        
        # Commit the changes to the database
        conn.commit()
        print("All database updates committed successfully.")
        
        # Return chain info for verification
        return merged_chains, business_name_map
        
    except Exception as e:
        print(f"Error: {e}")
        # Rollback in case of error
        conn.rollback()
        return [], {}
    

def check_history_list(history_list):
    
    # Check for empty list
    if not history_list:
        print("The entire history list is empty!")
        return True
    
    # Check for empty items
    empty_items = []
    for i, history in enumerate(history_list[0]):
        # Check if the history object is None
        if history is None:
            empty_items.append(i)
            continue
            
        # Check if all attributes are None or empty
        all_empty = all(
            getattr(history, attr) is None or 
            (isinstance(getattr(history, attr), str) and getattr(history, attr) == "") or
            (isinstance(getattr(history, attr), list) and len(getattr(history, attr)) == 0)
            for attr in vars(history) if attr != "reviewerID"  # Skip reviewerID for emptiness check
        )
        if all_empty:
            empty_items.append(i)
    
    if empty_items:
        print(f"Found {len(empty_items)} empty items at positions: {empty_items[:10]}...")
        
    # Check for duplicates based on a unique combination of fields
    seen = {}
    duplicates = []
    print(history_list[0])
    for i, history in enumerate(history_list[0]):
        
        if history is None:
            continue
            
        # Create a unique key based on fields that should make a record unique
        # Adjust these fields as needed for your definition of a duplicate
        unique_key = (
            str(history.reviewerID),
            history.businessName,
            history.reviewText,
            history.ratingTime,
            history.businessRating
        )
        
        if unique_key in seen:
            duplicates.append((i, seen[unique_key]))
        else:
            seen[unique_key] = i
    
    if duplicates:
        print(f"Found {len(duplicates)} duplicate records!")
        # Print sample of duplicates
        for i, (current, original) in enumerate(duplicates[:5]):
            print(f"Duplicate {i+1}: Position {current} is duplicate of position {original}")
            
    return len(empty_items) > 0 or len(duplicates) > 0
    
def addReviewers(conn, cursor):
    # from psycopg2.extras import execute_values
    cursor.execute("DROP TABLE IF EXISTS reviewerHistory;")
    conn.commit()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviewerHistory (
            "reviewerID" UUID NOT NULL,
            reviewerName TEXT,
            reviewerProfilePictureURL TEXT,
            reviewPoints INTEGER,
            userTagOrContributions TEXT,
            profileLink TEXT,
            businessName TEXT,
            businessAddress TEXT,
            businessRating DECIMAL,
            ratingTime TEXT,
            reviewText TEXT,
            reviewTags TEXT[],
            photos TEXT[],
            ownerResponse BOOLEAN,
            updateDate date,
            FOREIGN KEY ("reviewerID") REFERENCES reviewer("reviewerID")
        );
        """)
    #CONSTRAINT reviewerhistory_unique_id UNIQUE ("reviewerID", reviewText, businessName, ratingTime)
    conn.commit()  # Adding a commit to ensure the table creation is saved

    service = get_drive_service()


    folder_id = "1BbQehC-MI4nGL-mUZc4byUxan-0AAPK2" #final set, finaltotal.zip

    zip_files = get_zip_files(service, folder_id)

    if not zip_files:
        print("No ZIP files found in the specified folder")
        return

    

    for zip_file in zip_files:
        total = 0
        
        
        start = time.time()
        print(f"\nProcessing ZIP file: {zip_file['name']}")
        # if zip_file['name'] != "consolidated_json.zip":
        #     continue
        try:
            # Download ZIP
            zip_path = download_zip(service, zip_file["id"], zip_file["name"])
            
            for historyList in extract_and_process_jsons(zip_path, False, "reviewers"): #first run through, only add the shopping centers

                for history in historyList:
                    history = history[0]
                    total += 1
                   
                    check_query = """
                    SELECT EXISTS(SELECT 1 FROM reviewer WHERE "reviewerID" = %(reviewerID)s) AS reviewer_exists
                    """
                    

                    cursor.execute(check_query, {"reviewerID": history.reviewerID})
                    result = cursor.fetchone()
                    
                    # If reviewer_exists is False (0), print a message
                    # print(result)
                    if not result[0]:
                        print(f"Warning: reviewerID {history.reviewerID} does not exist in reviewer table")
                        csv_filename = "missing_reviewers.csv"
                        file_exists = os.path.isfile(csv_filename)
                        
                        # Open the CSV file in append mode
                        with open(csv_filename, 'a', newline='') as csvfile:
                            fieldnames = ['reviewerID', 'profileLink']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            
                            # Write header only if the file is being created for the first time
                            if not file_exists:
                                writer.writeheader()
                            
                            # Write the missing reviewer information
                            writer.writerow({
                                'reviewerID': history.reviewerID,
                                'profileLink': history.profileLink
                            })
                        
                        continue
                    
                    query = """
                    INSERT INTO reviewerHistory (
                        "reviewerID", reviewerName, reviewerProfilePictureURL, reviewPoints, 
                        userTagOrContributions, profileLink, businessName, businessAddress, 
                        businessRating, ratingTime, reviewText, reviewTags, photos, 
                        ownerResponse, updateDate
                    ) 
                    VALUES (
                        %(reviewerID)s, %(reviewerName)s, %(reviewerProfilePictureURL)s, %(reviewPoints)s,
                        %(userTagOrContributions)s, %(profileLink)s, %(businessName)s, %(businessAddress)s,
                        %(businessRating)s, %(ratingTime)s, %(reviewText)s, %(reviewTags)s, %(photos)s,
                        %(ownerResponse)s, %(updateDate)s
                    )
                    """
                    #                    ON CONFLICT ON CONSTRAINT reviewerhistory_unique_id DO NOTHING

                    # Create a dictionary of parameters
                    params = {
                        'reviewerID': history.reviewerID,
                        'reviewerName': history.reviewerName,
                        'reviewerProfilePictureURL': history.reviewerProfilePictureURL,
                        'reviewPoints': history.reviewPoints,
                        'userTagOrContributions': history.userTagOrContributions,
                        'profileLink': history.profileLink,
                        'businessName': history.businessName,
                        'businessAddress': history.businessAddress,
                        'businessRating': history.businessRating,
                        'ratingTime': history.ratingTime,
                        'reviewText': history.reviewText,
                        'reviewTags': history.reviewTags,
                        'photos': history.photos,
                        'ownerResponse': history.ownerResponse,
                        'updateDate': history.updateDate
                    }
                    
                    # Execute the query with parameters
                    cursor.execute(query, params)
                    
                    # Commit after each insert or in batches
                    # If inserting many records, you might want to commit in batches
                    conn.commit()
                
                
            
        except Exception as e:
            # Roll back the transaction in case of error
            conn.rollback()
            print(f"Error inserting records: {e}")
        
        

                
                
        print("AJJJJJJJJJJJJJJJJJJJJJJ")
            

        

        end = time.time()
        print(f"{zip_file['name']} executed in {end-start} seconds. {total} rows were attempted to be inserted\n\n")


def update_derived_signals(conn, cursor): #NOT WORKING YET


    try:
        df1 = pd.read_csv("/home/dan_gon_db_repo/thirdPartyDataUpload/functions/csv/sentimnent_llm.csv", encoding='utf-8', errors='replace').iloc[:, 2:] 
        df2 = pd.read_csv("csv/sentimnent_llm_second_part.csv").iloc[:, 3:]
        df3 = pd.read_csv("csv/sentimnent_llm_third_part.csv").iloc[:, 3:]
        df4 = pd.read_csv("csv/sentimnent_llm_fourth_part.csv").iloc[:, 3:]

        combined_df = pd.concat([df1, df2, df3, df4], ignore_index=True)

        combined_df = combined_df[combined_df['isShoppingCenter'] != True]

        combined_df = combined_df[combined_df['permclosed'] != True]

        df = combined_df

       

        update_query = """
        UPDATE review
        SET "derivedSignals" = %s
        WHERE "businessID" = %s
        """

        # List to store the batch of updates
        batch = []

        # Iterate through the dataframe and update the derivedSignals column
        for index, row in df.iterrows():
            business_id = row['businessID']
            
            # Check for NaN values and set them to None (which will be inserted as NULL)
            sentiment = row['sentiment'] if not pd.isna(row['sentiment']) else None
            negativeOverall = row['negativeOverall'] if not pd.isna(row['negativeOverall']) else None
            positiveOverall = row['positiveOverall'] if not pd.isna(row['positiveOverall']) else None
            neutral = row['neutral'] if not pd.isna(row['neutral']) else None
            Satisfaction = row['Satisfaction'] if not pd.isna(row['Satisfaction']) else None
            buyAgain = row['buyAgain'] if not pd.isna(row['buyAgain']) else None
            Convenience = row['Convenience'] if not pd.isna(row['Convenience']) else None
            Capacity = row['Capacity'] if not pd.isna(row['Capacity']) else None
            Trendiness = row['Trendiness'] if not pd.isna(row['Trendiness']) else None
            Criminality = row['Criminality'] if not pd.isna(row['Criminality']) else None
            CompetitionComparison = row['CompetitionComparison'] if not pd.isna(row['CompetitionComparison']) else None
            NoiseLevel = row['NoiseLevel'] if not pd.isna(row['NoiseLevel']) else None
            EmployeeBehavior = row['EmployeeBehavior'] if not pd.isna(row['EmployeeBehavior']) else None
            OnlinePresence = row['OnlinePresence'] if not pd.isna(row['OnlinePresence']) else None
            tags = row['tags'] if not pd.isna(row['tags']) else None  # Assuming tags can also be NaN

            try:
                # Query to get the current JSON in the derivedSignals column
                select_query = """
                SELECT "derivedSignals" FROM review WHERE "businessID" = %s
                """
                cursor.execute(select_query, (business_id,))
                result = cursor.fetchone()

                # If derivedSignals already exists, load it, otherwise create a new one
                if result and result[0]:
                    # Update the existing JSON
                    derived_signals = result[0]
                    derived_signals = json.loads(derived_signals) if isinstance(derived_signals, str) else derived_signals
                else:
                    # If no existing value, create a new empty dictionary
                    derived_signals = {}

                # Update or add the relevant derived signals, setting NaN values to None
                derived_signals['sentiment'] = sentiment
                derived_signals['negativeOverall'] = negativeOverall
                derived_signals['positiveOverall'] = positiveOverall
                derived_signals['neutral'] = neutral
                derived_signals['Satisfaction'] = Satisfaction
                derived_signals['buyAgain'] = buyAgain
                derived_signals['Convenience'] = Convenience
                derived_signals['Capacity'] = Capacity
                derived_signals['Trendiness'] = Trendiness
                derived_signals['Criminality'] = Criminality
                derived_signals['CompetitionComparison'] = CompetitionComparison
                derived_signals['NoiseLevel'] = NoiseLevel
                derived_signals['EmployeeBehavior'] = EmployeeBehavior
                derived_signals['OnlinePresence'] = OnlinePresence
                derived_signals['tags'] = tags

                # Convert the updated dictionary back to JSON
                updated_json = json.dumps(derived_signals)

                # Append the tuple (updated_json, business_id) to the batch
                batch.append((updated_json, business_id))

                # Commit every 10 updates
                if len(batch) >= 10:
                    cursor.executemany(update_query, batch)
                    conn.commit()  # Commit the batch
                    batch.clear()  # Clear the batch for the next set of updates

            except Exception as e:
                print(f"Error updating businessID {business_id}: {e}")

        # Final commit for any remaining updates
        if batch:
            cursor.executemany(update_query, batch)
            conn.commit()

    except Exception as e:
        print(f"Error connecting to the database or executing queries: {e}")

    # finally:
    #     # Ensure that the cursor and connection are always closed
    #     if cursor:
    #         cursor.close()
    #     if conn:
    #         conn.close()

   
def changeCoordinates(conn, cursor):
    from functions.geocode import geocode_addresses
    import csv
    import os

    cursor.execute("""SELECT 
    address."businessID",
    address."addressFull"
FROM 
    BUSINESS
JOIN
    address ON BUSINESS."businessID" = address."businessID"
WHERE 
    (6371 * ACOS(
        COS(RADIANS(25.4383)) * COS(RADIANS(BUSINESS.latitude)) * COS(RADIANS(BUSINESS.longitude) - RADIANS(-100.9737)) + 
        SIN(RADIANS(25.4383)) * SIN(RADIANS(BUSINESS.latitude))
    ) <= 60)
                   """)

    businesses = cursor.fetchall()
    geocode_addresses(businesses, delay = 0 )

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    csv_file_path = os.path.join(parent_dir,'geocoded_results.csv')
    success_count = 0
    error_count = 0

    with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
            
            # Loop through each row in the CSV
            for row in csv_reader:
                try:
                    # Extract data from row
                    business_id = row[0]
                    # address is row[1] but not needed for the update
                    latitude = row[2]
                    longitude = row[3]
                    
                    # Update the business table
                    update_query = """
                    UPDATE BUSINESS 
                    SET latitude = %s, longitude = %s 
                    WHERE "businessID" = %s
                    """
                    
                    cursor.execute(update_query, (latitude, longitude, business_id))
                    
                    # Check if the update affected any rows
                    if cursor.rowcount > 0:
                        success_count += 1
                        print(f"Updated coordinates for business {business_id}: {latitude}, {longitude}")
                    else:
                        error_count += 1
                        print(f"No business found with ID {business_id}")
                        
                except Exception as e:
                    error_count += 1
                    print(f"Error updating business {business_id}: {str(e)}")
            
            # Commit the changes
            conn.commit()
            
            print(f"\nUpdate complete: {success_count} businesses updated successfully, {error_count} errors")
            return success_count, error_count
    
#=================================================================================================================
import asyncio
import ee
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional, Dict
import threading

async def addOpenBuildingsAsync(conn, cursor, max_concurrent, batch_size):
    """
    Asynchronously fetch building areas and plus codes from Google Earth Engine and update database.
    
    Args:
        conn: Existing database connection (psycopg2)
        cursor: Existing database cursor
        max_concurrent: Maximum number of concurrent API requests
        batch_size: Number of businesses to process in each batch
    """
    print("Starting async Open Buildings integration...")
    start_time = time.time()
    
    # Initialize Earth Engine in the main thread if not already done
    try:
        ee.Initialize(project='oaxaca-450415')
    except ee.EEException:
        # Already initialized
        pass
        
    buildings = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons')
    
    # Check if buildingArea column exists, create if not
    cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='business' AND column_name='buildingarea';
    """)
    
    if cursor.fetchone() is None:
        print("Creating buildingArea column...")
        cursor.execute("ALTER TABLE business ADD COLUMN buildingArea FLOAT;")
        conn.commit()
    
    # Check if buildingPlusCode column exists, create if not
    cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='business' AND column_name='buildingpluscode';
    """)
    
    if cursor.fetchone() is None:
        print("Creating buildingPlusCode column...")
        cursor.execute("ALTER TABLE business ADD COLUMN buildingPlusCode VARCHAR(20);")
        conn.commit()
    
    # Fetch businesses that need processing
    cursor.execute("""
    SELECT 
        "businessID",
        "name",
        "latitude",
        "longitude"
    FROM 
        BUSINESS
    WHERE 
        (6371 * ACOS(
            COS(RADIANS(25.4383)) * COS(RADIANS(BUSINESS.latitude)) * COS(RADIANS(BUSINESS.longitude) - RADIANS(-100.9737)) + 
            SIN(RADIANS(25.4383)) * SIN(RADIANS(BUSINESS.latitude))
        ) <= 60) AND ("buildingarea" is null OR "buildingpluscode" is null)
    """)
    
    businesses = cursor.fetchall()
    
    print(f"Found {len(businesses)} businesses to process")
    if not businesses:
        print("No businesses to process.")
        return
    
    # Create a lock for database operations
    db_lock = threading.Lock()
    
    # Process in batches to avoid overwhelming the system
    total_processed = 0
    total_businesses = len(businesses)
    
    for i in range(0, total_businesses, batch_size):
        batch = businesses[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (total_businesses + batch_size - 1)//batch_size
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} businesses)")
        
        # Start timing for this batch
        batch_start_time = time.time()
        
        # Create a semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Process batch
        tasks = []
        for business in batch:
            business_id, name, latitude, longitude = business
            task = asyncio.create_task(
                process_business(
                    business_id, name, latitude, longitude, 
                    buildings, conn, cursor, semaphore, db_lock
                )
            )
            tasks.append(task)
        
        # Wait for all tasks in this batch to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate batch completion time
        batch_end_time = time.time()
        batch_duration = batch_end_time - batch_start_time
        
        # Count successful updates and handle exceptions
        successful = 0
        for r in results:
            if isinstance(r, Exception):
                print(f"Error in task: {str(r)}")
            elif r is True:
                successful += 1
                
        total_processed += successful
        
        # Print batch timing information
        print(f"Batch {batch_num}/{total_batches} complete: {successful}/{len(batch)} buildings updated successfully")
        print(f"Batch time: {batch_duration:.2f} seconds ({batch_duration/len(batch):.2f} seconds per business)")
        
        # Calculate and display estimated time remaining
        if batch_num < total_batches:
            avg_time_per_batch = batch_duration
            remaining_batches = total_batches - batch_num
            est_time_remaining = avg_time_per_batch * remaining_batches
            print(f"Estimated time remaining: {est_time_remaining:.2f} seconds ({est_time_remaining/60:.2f} minutes)")

        

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Done adding Open Building Data. Processed {total_processed}/{total_businesses} businesses in {elapsed_time:.2f} seconds")
    if total_businesses > 0:
        print(f"Average time per business: {elapsed_time/total_businesses:.2f} seconds")


async def process_business(business_id, name, latitude, longitude, buildings, conn, cursor, semaphore, db_lock):
    """Process a single business asynchronously."""
    if longitude is None or latitude is None:
        print(f"  Skipping business {business_id}: Missing coordinates")
        return False
    
    try:
        # Use semaphore to limit concurrent API calls
        async with semaphore:
            # Get building area and plus code from Earth Engine
            # We need to run EE calls in a thread pool since they're blocking
            building_data = await get_building_data_async(latitude, longitude, buildings)
            
            # Update database if we found a building
            if building_data and building_data.get('area') is not None:
                # Use a lock for database operations since we're using a synchronous connection
                with db_lock:
                    cursor.execute(
                        """UPDATE "business" 
                           SET buildingarea = %s, buildingPlusCode = %s 
                           WHERE "businessID" = %s""",
                        (building_data.get('area'), building_data.get('plus_code'), business_id)
                    )
                    conn.commit()
                # print(f"  Updated business {business_id}: {building_data.get('area')} sq meters, plus code: {building_data.get('plus_code')}")
                return True
            else:
                # print(f"  No building found for business {business_id} at ({latitude}, {longitude})")
                return False
    except Exception as e:
        print(f"  Error processing business {business_id}: {str(e)}")
        return False


async def get_building_data_async(latitude, longitude, buildings):
    """
    Get building data (area and plus code) at a point from Earth Engine asynchronously.
    
    Earth Engine operations are not natively async, so we run them in a ThreadPoolExecutor.
    """
    # Run the Earth Engine operation in a thread pool
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, 
            get_building_data_sync, 
            latitude, longitude, buildings
        )


def get_building_data_sync(latitude, longitude, buildings):
    """Synchronous function to get building data that runs in a thread."""
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        point = ee.Geometry.Point([longitude, latitude])
        building = buildings.filterBounds(point).first()
        
        if building.getInfo() is not None:
            area = building.getNumber('area_in_meters').getInfo()
            plus_code = building.getString('full_plus_code').getInfo()
            return {
                'area': area,
                'plus_code': plus_code
            }
        else:
            return None
    except Exception as e:
        print(f"  Error in Earth Engine API: {str(e)}")
        return None


def addOpenBuildings(conn, cursor, max_concurrent: int = 20, batch_size: int = 100):
    """
    Entry point that takes the existing connection and cursor.
    This function will call the async implementation.
    
    Args:
        conn: Existing database connection (psycopg2)
        cursor: Existing database cursor
        max_concurrent: Maximum number of concurrent API requests
        batch_size: Number of businesses to process in each batch
    """
    import ee
    
    # Authenticate if needed
    try:
        ee.Authenticate()
    except Exception as e:
        print(f"Authentication error: {e}")
        print("Continuing with existing credentials...")
    
    # Run the async implementation
    asyncio.run(addOpenBuildingsAsync(conn, cursor, max_concurrent, batch_size))

    cursor.execute("""
    ALTER TABLE business ADD COLUMN IF NOT EXISTS buildingAreaAdjusted FLOAT;
    
    WITH code_counts AS (
        SELECT buildingpluscode, COUNT(*) as occurrence_count
        FROM business
        WHERE buildingpluscode IS NOT NULL
        GROUP BY buildingpluscode
    )
    UPDATE business b
    SET buildingAreaAdjusted = b.buildingarea / r.occurrence_count
    FROM code_counts r
    WHERE b.buildingpluscode = r.buildingpluscode;

    UPDATE business
    SET buildingAreaAdjusted = buildingarea 
    WHERE buildingpluscode IS NULL;
                   

""")
    conn.commit()
    print("open building information added. adjusted areas stored in new column.")


#=================================================================================================================

def generalizeCategories(conn, cursor):
    import pickle
    category_mapping = {}

    pickle_path = "categoryGeneralization.pkl"
    with open(pickle_path, 'rb') as pickle_file:
        category_mapping = pickle.load(pickle_file)

    if category_mapping:
        try:
            # First check if the categoryGeneral column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='business' AND column_name='categorygeneral'
            """)
            
            # Add the column if it doesn't exist
            if not cursor.fetchone():
                print("Adding categoryGeneral column to business table")
                cursor.execute("ALTER TABLE business ADD COLUMN categoryGeneral TEXT")
            
            # Get all businesses and their categories
            cursor.execute('SELECT "businessID", "category" FROM business')
            businesses = cursor.fetchall()
            print(f"Found {len(businesses)} businesses to update")
            
            # Update each business with its general category
            update_count = 0
            for business in businesses:
                business_id = business['businessID']
                category = business['category'].strip().replace("’"," ").replace("'", " ") if business['category'] else business['category']
                
                if category == "Men's clothing store":
                    print(category)
                    # print(category_mapping["Men's clothing store"])
                if category in category_mapping:
                    general_category = category_mapping[category]
                    # print(general_category)
                    cursor.execute(
                        'UPDATE business SET categoryGeneral = %s WHERE "businessID" = %s',
                        (general_category, business_id)
                    )
                    update_count += 1
            
            # Commit the changes
            conn.commit()
            print(f"Successfully updated {update_count} businesses with general categories")
            
        except Exception as e:
            conn.rollback()
            print(f"Error updating business table: {e}")
            

# def scrapeInstagram(conn, cursor):
    
#     def check_and_create_column(table_name, column_name):
#         """Check if column exists, and create it if it doesn't."""
#         try:
#             # Check if column exists
#             cursor.execute(f"""
#                 SELECT EXISTS (
#                     SELECT 1 
#                     FROM information_schema.columns 
#                     WHERE table_name = '{table_name}' 
#                     AND column_name = '{column_name}'
#                 );
#             """)
            
#             column_exists = cursor.fetchone()['exists']
            
#             if not column_exists:
#                 print(f"Column '{column_name}' does not exist. Creating it now...")
#                 cursor.execute(f"""
#                     ALTER TABLE {table_name} 
#                     ADD COLUMN "{column_name}" TEXT;
#                 """)
#                 conn.commit()
#                 print(f"Column '{column_name}' created successfully.")
#             else:
#                 print(f"Column '{column_name}' already exists.")
                
#             return True
#         except psycopg2.DatabaseError as error:
#             print(f"Error checking/creating column: {error}")
#             conn.rollback()
#             return False

#     def update_instagram_links(csv_path):
        
#         if not conn or not cursor:
#             print("Failed to connect to the database.")
#             return
        
#         try:
#             # Hard-coded to use the "contact" table
#             table_name = "contact"
            
#             # Check and create column if needed
#             if not check_and_create_column(table_name, "businessInstaExact"):
#                 return
            
#             # Read CSV and update database
#             with open(csv_path, 'r') as csv_file:
#                 csv_reader = csv.DictReader(csv_file)
                
#                 updated_count = 0
#                 error_count = 0
                
#                 for row in csv_reader:
#                     business_id = row['businessid']
#                     instagram_link = row['instagram_link']
                    
#                     if business_id and instagram_link:
#                         try:
#                             cursor.execute("""
#                                 UPDATE contact
#                                 SET "businessInstaExact" = %s
#                                 WHERE "businessID" = %s
#                             """, (instagram_link, business_id))
#                             updated_count += 1
#                         except psycopg2.DatabaseError as error:
#                             print(f"Error updating row with business ID {business_id}: {error}")
#                             error_count += 1
                
#                 conn.commit()
#                 print(f"Update completed: {updated_count} rows updated, {error_count} errors.")
        
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             conn.rollback()
        
#     csv_path = "scrapedInsta.csv"
#     update_instagram_links(csv_path)
#     with open(csv_path, 'r') as csv_file:
#         csv_reader = csv.DictReader(csv_file)
        
#         for row in csv_reader:
#             business_id = row['businessid']
#             instagram_link = row['instagram_link']
#             profile = scrapeURL(instagram_link)


def scrapeInstagram(conn, cursor):

    
    def check_and_create_column(table_name, column_name):
        """Check if column exists, and create it if it doesn't."""
        try:
            # Check if column exists
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_name = '{column_name}'
                );
            """)
            
            column_exists = cursor.fetchone()[0]
            
            if not column_exists:
                print(f"Column '{column_name}' does not exist. Creating it now...")
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN "{column_name}" TEXT;
                """)
                conn.commit()
                print(f"Column '{column_name}' created successfully.")
            else:
                print(f"Column '{column_name}' already exists.")
                
            return True
        except psycopg2.DatabaseError as error:
            print(f"Error checking/creating column: {error}")
            conn.rollback()
            return False

    def check_and_fix_social_table():
        """Check Social table structure and fix data types and missing columns."""
        try:
            # Fix data types of existing columns
            cursor.execute("""
                DO $$
                BEGIN
                    -- Check and convert url column from bigint to text
                           
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'social' AND column_name = 'businessID' 
                        AND data_type = 'uuid'
                    ) THEN
                        ALTER TABLE "social" ALTER COLUMN "businessID" TYPE uuid
                    END IF;
                           

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'social' AND column_name = 'externalURL' 
                        AND data_type = 'text'
                    ) THEN
                        ALTER TABLE "social" ALTER COLUMN "externalURL" TYPE text[] 
                        USING string_to_array("externalURL"::text, ',')
                    END IF;
                           
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'social' AND column_name = 'url' 
                        AND data_type = 'bigint'
                    ) THEN
                        ALTER TABLE "social" ALTER COLUMN "url" TYPE text USING "url"::text;
                    END IF;
                    
                    -- Check and convert bio column from bigint to text
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'social' AND column_name = 'bio' 
                        AND data_type = 'bigint'
                    ) THEN
                        ALTER TABLE "social" ALTER COLUMN "bio" TYPE text USING "bio"::text;
                    END IF;
                    
                    -- Check and convert numPosts column from text to integer
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'social' AND column_name = 'numPosts' 
                        AND data_type = 'text'
                    ) THEN
                        ALTER TABLE "social" ALTER COLUMN "numPosts" TYPE integer USING "numPosts"::integer;
                    END IF;
                    
                    -- Check and convert followers column
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'social' AND column_name = 'followers' 
                        AND data_type = 'character varying'
                    ) THEN
                        ALTER TABLE "social" ALTER COLUMN "followers" TYPE integer USING "followers"::integer;
                    END IF;
                    
                    -- Check and convert following column
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'social' AND column_name = 'following' 
                        AND data_type = 'bigint'
                    ) THEN
                        ALTER TABLE "social" ALTER COLUMN "following" TYPE integer USING "following"::integer;
                    END IF;
                END
                $$;
            """)
            
            # Add missing columns
            missing_columns = [ #"bioLinks",
                "username", "fullName", "externalURL", "isPrivate", "businessID"
            ]
            
            for column in missing_columns:
                column_type = "boolean" if column == "isPrivate" else "json" if column == "bioLinks" else "text"
                check_and_create_column("social", column)
                
                # If column exists but with wrong type, fix it
                if column == "isPrivate" : #or column == "bioLinks"
                    cursor.execute(f"""
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'social' AND column_name = '{column}' 
                                AND data_type != '{column_type}'
                            ) THEN
                                ALTER TABLE "social" ALTER COLUMN "{column}" TYPE {column_type} 
                                USING "{column}"::{column_type};
                            END IF;
                        END
                        $$;
                    """)
            
            conn.commit()
            print("Social table structure updated successfully.")
            return True
        except psycopg2.DatabaseError as error:
            print(f"Error updating Social table structure: {error}")
            conn.rollback()
            return False

    def update_instagram_links(csv_path):
        
        if not conn or not cursor:
            print("Failed to connect to the database.")
            return
        
        try:
            # Hard-coded to use the "contact" table
            table_name = "contact"
            
            # Check and create column if needed
            if not check_and_create_column(table_name, "businessInstaExact"):
                return
            
            # Read CSV and update database
            with open(csv_path, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                
                updated_count = 0
                error_count = 0
                
                for row in csv_reader:
                    business_id = row['businessid']
                    instagram_link = row['instagram_link']
                    
                    if business_id and instagram_link:
                        try:
                            cursor.execute("""
                                UPDATE contact
                                SET "businessInstaExact" = %s
                                WHERE "businessID" = %s
                            """, (instagram_link, business_id))
                            updated_count += 1
                        except psycopg2.DatabaseError as error:
                            print(f"Error updating row with business ID {business_id}: {error}")
                            error_count += 1
                
                conn.commit()
                print(f"Update completed: {updated_count} rows updated, {error_count} errors.")
        
        except Exception as e:
            print(f"An error occurred: {e}")
            conn.rollback()
    
    def insert_instagram_profile(business_id, profile):
        """Insert scraped Instagram profile into Social table."""
        try:
            # Generate a UUID for socialID
            # social_id = uuid.uuid4()
            print(type(profile['External URL']))
            social_id = hash_to_uuid("Instagram" + profile["Full Name"])
            today = datetime.now().date()
            
            # Convert bio_links to JSON if needed
            # bio_links_json = json.dumps(profile["Bio_Links"]) if isinstance(profile["Bio_Links"], (list, dict)) else profile["Bio_Links"]
            
            # Check if a record already exists for this business_id
            cursor.execute("""
                SELECT "socialID" FROM "social" 
                WHERE "socialID" = %s;
            """, (social_id,))
            
            existing_record = cursor.fetchone()
            # x = [profile["External URL"]] if profile["External URL"] else []
            # print(x)
            # if existing_record:
            #     print(f"skipping {profile['Username']}, already in the database")
            
            if existing_record:
                # Update existing record # "bioLinks" "bioLinks" = EXCLUDED."bioLinks"
                cursor.execute("""
                    INSERT INTO "social" (
                        "socialID", 
                        "platform", 
                        "url", 
                        "bio", 
                        "numPosts", 
                        "followers", 
                        "following", 
                        "updateDate", 
                        "username", 
                        "fullName", 
                        "externalURL", 
                        "isPrivate",
                        "businessID"
                       
                    ) VALUES (
                        %s, 'Instagram', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT ("socialID") 
                    DO UPDATE SET
                        "platform" = 'Instagram',
                        "url" = EXCLUDED."url",
                        "bio" = EXCLUDED."bio",
                        "numPosts" = EXCLUDED."numPosts",
                        "followers" = EXCLUDED."followers",
                        "following" = EXCLUDED."following",
                        "updateDate" = EXCLUDED."updateDate",
                        "username" = EXCLUDED."username",
                        "fullName" = EXCLUDED."fullName",
                        "externalURL" = EXCLUDED."externalURL",
                        "isPrivate" = EXCLUDED."isPrivate",
                        "businessID" = EXCLUDED."businessID"
                        
                    """, (
                        social_id,
                        profile['URL'],
                        profile["Biography"],
                        profile["Posts Count"],
                        profile["Followers"],
                        profile["Following"],
                        today,
                        profile["Username"],
                        profile["Full Name"],
                        ([profile['External URL']],) if profile["External URL"] else [],  # Convert to list for array column
                        profile["Is_Private"],
                        business_id
                    )) #bio_links_json

                print(f"Updated Instagram profile for business ID: {business_id}")
            else:
                # Insert new record "bioLinks",
                cursor.execute("""
                    INSERT INTO "social" (
                        "socialID", "platform", "url", "bio", "numPosts", 
                        "followers", "following", "created", "updateDate", 
                        "username", "fullName", "externalURL", "isPrivate", 
                        "businessID"
                    ) VALUES (
                        %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, 
                        %s, %s, %s, %s, 
                        %s
                    )
                """, (
                    social_id,
                    'Instagram',
                    profile['URL'],
                    profile["Biography"],
                    profile["Posts Count"],
                    profile["Followers"],
                    profile["Following"],
                    today,
                    today,
                    profile["Username"],
                    profile["Full Name"],
                    ([profile['External URL']],) if profile["External URL"] else [],
                    profile["Is_Private"],
                    business_id
                )) #bio_links_json,

                print(f"Inserted new Instagram profile for business ID: {business_id}")
            
            conn.commit()
            return True
        except psycopg2.DatabaseError as error:
            print(f"Error inserting/updating Instagram profile for business ID {business_id}: {error}")
            conn.rollback()
            return False
    
    # Main execution flow
    import uuid
    import json
    from datetime import datetime
    
    # First ensure the Social table has the correct structure
    if not check_and_fix_social_table():
        print("Failed to update Social table structure. Continuing with caution.")
    
    # Update the businessInstaExact column in contact table
    # csv_path = "thirdPartyDataUpload/functions/scrapedInsta.csv"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "scrapedInsta.csv")

    update_instagram_links(csv_path)
    
    # Process Instagram profiles and insert into Social table
    processed_count = 0
    error_count = 0
    
    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for i, row in enumerate(csv_reader):
            if i < 86:
                continue

            business_id = row['businessid']
            instagram_link = row['instagram_link']
            
            if not business_id or not instagram_link:
                print(f"Skipping row: Missing business ID or Instagram link")
                continue
                
            try:
                # Scrape Instagram profile
                profile = scrapeURL(instagram_link)
                
                # Insert/update profile in database
                if insert_instagram_profile(business_id, profile):
                    processed_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error processing Instagram profile for business ID {business_id}: {e}")
                error_count += 1
    
    print(f"Instagram scraping completed: {processed_count} profiles processed, {error_count} errors.")

            

"""
profile_info = {
            "Username": profile.username,
            "Full Name": profile.full_name,
            "Biography": profile.biography,
            "External URL": profile.external_url,
            "Followers": profile.followers,
            "Following": profile.followees,
            "Posts Count": profile.mediacount,
            "Is_Private": profile.is_private,
            "Bio_Links" : bio_links
        }
"""

def convert_column_to_uuid(conn, cursor, table_name="social", column_name="businessID"):
    """
    Converts a column from TEXT type to UUID type in PostgreSQL.
    
    Parameters:
    conn -- Database connection object
    cursor -- Database cursor object
    table_name -- Name of the table containing the column
    column_name -- Name of the column to convert (case sensitive)
    """
    try:
        # Start a transaction
        conn.autocommit = False
        
        # Use double quotes around identifiers to preserve case
        # Step 1: Create a temporary column of UUID type
        cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "temp_uuid" UUID;')
        
        # Step 2: Update the temporary column with UUID values from the text column
        cursor.execute(f'UPDATE "{table_name}" SET "temp_uuid" = "{column_name}"::UUID;')
        
        # Step 3: Drop the original text column
        cursor.execute(f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}";')
        
        # Step 4: Rename the temporary column to the original column name
        cursor.execute(f'ALTER TABLE "{table_name}" RENAME COLUMN "temp_uuid" TO "{column_name}";')
        
        # Commit the transaction
        conn.commit()
        print(f"Successfully converted column '{column_name}' from TEXT to UUID type in table '{table_name}'")
        
    except Exception as e:
        # Rollback in case of any error
        conn.rollback()
        print(f"Error converting column: {e}")
    finally:
        # Restore autocommit setting
        conn.autocommit = True


def allPostProcessing(conn, cursor, toExecute):
    processing_functions = {
        "analyze_business_substrings": analyze_business_substrings,
        "update_shopping_center_business_counts": update_shopping_center_business_counts,
        "changeCoordinates": changeCoordinates,
        "addOpenBuildings": addOpenBuildings,
        "addReviewers": addReviewers,
        "generalizeCategories": generalizeCategories,
        "scrapeInstagram": scrapeInstagram,
        "convert_column_to_uuid":convert_column_to_uuid
        # "update_derived_signals": update_derived_signals
    }
    
    if not toExecute:
        print("Executing all available post-processing functions...")
        for func_name, func in processing_functions.items():
            print(f"Running {func_name}...")
            func(conn, cursor)

    else:
        # Execute only the functions specified in toExecute
        for func_name in toExecute:
            if func_name in processing_functions:
                print(f"Running {func_name}...")
                processing_functions[func_name](conn, cursor)
            else:
                print(f"Warning: Function '{func_name}' not found or not available.")
  



    
   
 