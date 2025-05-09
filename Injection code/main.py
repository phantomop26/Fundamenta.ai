from functions.downloadFunctions import (
    get_drive_service,
    get_zip_files,
    download_zip,
    extract_and_process_jsons,
)
import psycopg2
from psycopg2.extras import Json
import traceback
import argparse
import json
from datetime import datetime
from functions.parsingFunctions import process_google_json
import time
import os
import csv
from functions.postProcess import allPostProcessing


def load_db_config(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


# Load DB configuration
db_config = load_db_config("db_config.json")

def execute_sql_file(conn, sql_file_path):
    """
    Execute SQL commands from a file
    """

    try:
        with open(sql_file_path, "r") as sql_file:
            sql_commands = sql_file.read()

        cursor = conn.cursor()
        cursor.execute(sql_commands)
        conn.commit()
        cursor.close()
        print("Successfully executed create-tables.sql")
    except Exception as e:
        print(f"Error executing SQL file: {str(e)}")
        raise


def insert_business_data(conn, data_list, firstRunThrough):
    """
    Insert business-related data into PostgreSQL database.

    Args:
        conn: PostgreSQL connection object
        data_list: List of dictionaries containing business data
    """
    with conn.cursor() as cursor:
        for data in data_list:
            if data.get("shoppingCenterBusinesses") and firstRunThrough:
                scb_data = vars(data['shoppingCenterBusinesses'])

                try:
                    cursor.execute(
                        """
                        INSERT INTO ShoppingCenterBusinesses(
                          "shoppingCenterID",
                          "businessCount",
                          "otherInfo" 

                        ) VALUES (
                          %(shoppingCenterID)s,
                          %(businessCount)s,
                          %(otherInfo)s 
                        )
                        ON CONFLICT ("shoppingCenterID") DO NOTHING

                    """, scb_data
                    )
                except psycopg2.Error as e:
                    print(
                        f"Failed to insert shopping center {scb_data.get('shoppingCenterID')}: {str(e)}"
                    )
                    conn.rollback()

            if data.get("business"):
                business_data = vars(data["business"])

                existing = True
                if business_data.get('shoppingCenterID') is not None:
                    cursor.execute(
                        """
                        SELECT "shoppingCenterID" FROM ShoppingCenterBusinesses 
                        WHERE "shoppingCenterID" = %(shoppingCenterID)s
                        """,
                        {'shoppingCenterID': business_data['shoppingCenterID']}
                    )
                    
                    existing = cursor.fetchone()
                if not existing:
                #     # with open("missingMalls.csv", )
                #     # print(f"Warning: shoppingCenterID {business_data['shoppingCenterID']} does not exist in ShoppingCenterBusinesses table")
                    
                    
                    business_data['shoppingCenterID'] = None

                #     with open("missingMalls.csv", 'a', newline='', encoding='utf-8') as csvfile:
                        
                #         fieldnames = ['name', 'gmapsURL']
                #         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                #         if not os.path.isfile("missingMalls.csv"):
                #             writer.writeheader()
                        
                #         # Write headers only if file is being created for the first time
                        
                        
                #         # Write only the name and gmapsURL from the business data
                #         writer.writerow({
                #             'name': business_data['name'],
                #             'gmapsURL': business_data['gmapsURL']
                #         })

                # print(business_data['name'])
                business_data["financials"] = (
                    Json(business_data["financials"])
                    if business_data["financials"]
                    else None
                )
               

                try:

                    cursor.execute(
                        """
                        INSERT INTO Business (
                            "businessID", name,"gmapsURL", "isVerified", "businessStartDate",
                            "businessAge", "shoppingCenterID", "isShoppingCenter",
                            defunct, chain, financials,
                            "metricsID", created, summary,
                            longitude, latitude, "updateDate", alias,
                            "rating", "ratingScaled", "price", "totalReviews", "category", "permclosed","locationCount"
                        ) VALUES (
                            %(businessID)s, %(name)s, %(gmapsURL)s, %(isVerified)s,
                            %(businessStartDate)s, %(businessAge)s,
                            %(shoppingCenterID)s, %(isShoppingCenter)s,
                            %(defunct)s, %(chain)s,
                            %(financials)s, %(metricsID)s, %(created)s,
                            %(summary)s,
                            %(longitude)s, %(latitude)s, %(updateDate)s,
                            %(alias)s, %(rating)s, %(ratingScaled)s, %(price)s, %(totalReviews)s, %(category)s, %(permclosed)s, %(locationCount)s
                        )
                       
                        ON CONFLICT ("businessID") DO UPDATE SET
                            name = EXCLUDED.name,
                            "gmapsURL" = EXCLUDED."gmapsURL",
                            "isVerified" = EXCLUDED."isVerified",
                            "businessStartDate" = EXCLUDED."businessStartDate",
                            "businessAge" = EXCLUDED."businessAge",
                            "shoppingCenterID" = EXCLUDED."shoppingCenterID",
                            "isShoppingCenter" = EXCLUDED."isShoppingCenter",
                            defunct = EXCLUDED.defunct,
                            chain = EXCLUDED.chain,
                            financials = EXCLUDED.financials,
                            "metricsID" = EXCLUDED."metricsID",
                            created = EXCLUDED.created,
                            summary = EXCLUDED.summary,
                            longitude = EXCLUDED.longitude,
                            latitude = EXCLUDED.latitude,
                            "updateDate" = EXCLUDED."updateDate",
                            alias = EXCLUDED.alias,
                            "rating" = EXCLUDED."rating",
                            "ratingScaled" = EXCLUDED."ratingScaled",
                            "price" = EXCLUDED."price",
                            "totalReviews" = EXCLUDED."totalReviews",
                            "category" = EXCLUDED."category",
                            "permclosed" = EXCLUDED."permclosed",
                            "locationCount" = EXCLUDED."locationCount"

                    """,
                        business_data,
                    )

                    
                except psycopg2.Error as e:
                   
                    print(
                        f"Failed to insert business {business_data.get('businessID')}: {str(e)}"
                    )
                    conn.rollback()

                if data.get("address"):
                    cursor.execute(
                        """
                        INSERT INTO Address (
                            "businessID", "addressName", "addressNumber", "addressStreet",
                            "addressUnit", "addressLevel", "addressDetails", "addressPOBox",
                            "addressCity", "addressProvState", "addressRegion",
                            "addressNeighborhood", "addressPostalCode", "addressCountry",
                            "addressw3w", sources, "updateDate", "addressFull", "addressSimple"
                        ) VALUES (
                            %(businessID)s, %(addressName)s, %(addressNumber)s,
                            %(addressStreet)s, %(addressUnit)s, %(addressLevel)s,
                            %(addressDetails)s, %(addressPOBox)s, %(addressCity)s,
                            %(addressProvState)s, %(addressRegion)s, %(addressNeighborhood)s,
                            %(addressPostalCode)s, %(addressCountry)s, %(addressw3w)s,
                            %(sources)s, %(updateDate)s, %(addressFull)s, %(addressSimple)s
                        )
                        ON CONFLICT ("businessID") DO UPDATE SET
                            "addressName" = EXCLUDED."addressName",
                            "addressNumber" = EXCLUDED."addressNumber",
                            "addressStreet" = EXCLUDED."addressStreet",
                            "addressUnit" = EXCLUDED."addressUnit",
                            "addressLevel" = EXCLUDED."addressLevel",
                            "addressDetails" = EXCLUDED."addressDetails",
                            "addressPOBox" = EXCLUDED."addressPOBox",
                            "addressCity" = EXCLUDED."addressCity",
                            "addressProvState" = EXCLUDED."addressProvState",
                            "addressRegion" = EXCLUDED."addressRegion",
                            "addressNeighborhood" = EXCLUDED."addressNeighborhood",
                            "addressPostalCode" = EXCLUDED."addressPostalCode",
                            "addressCountry" = EXCLUDED."addressCountry",
                            "addressw3w" = EXCLUDED."addressw3w",
                            sources = EXCLUDED.sources,
                            "updateDate" = EXCLUDED."updateDate",
                            "addressFull" = EXCLUDED."addressFull",
                            "addressSimple" = EXCLUDED."addressSimple"
                    """,
                        vars(data["address"]),
                    )

                # Insert Contact
                if data.get("contact"):
                    cursor.execute(
                        """
                        INSERT INTO Contact (
                            "businessID", "businessEmail", "businessURL", "socialID",
                            phone, email, "updateDate"
                        ) VALUES (
                            %(businessID)s, %(businessEmail)s, %(businessURL)s,
                            %(socialID)s, %(phone)s, %(email)s, %(updateDate)s
                        )
                        ON CONFLICT ("businessID") DO UPDATE SET
                            "businessEmail" = EXCLUDED."businessEmail",
                            "businessURL" = EXCLUDED."businessURL",
                            "socialID" = EXCLUDED."socialID",
                            phone = EXCLUDED.phone,
                            email = EXCLUDED.email,
                            "updateDate" = EXCLUDED."updateDate"
                    """,
                        vars(data["contact"]),
                    )

                # Insert Detail
                if data.get("detail"):
                    detail_data = vars(data["detail"])
                    
                    detail_data["links"] = (
                        Json(detail_data["links"]) if detail_data["links"] else None
                    )

                    detail_data["amenities"] = json.dumps(detail_data["amenities"])

                    cursor.execute(
                        """
                        INSERT INTO Detail (
                            "businessID", "amenities",
                            links, "updateDate", "previousID", "about"
                        ) VALUES (
                            %(businessID)s, %(amenities)s,
                            %(links)s, %(updateDate)s, %(previousID)s, %(about)s
                        )
                        ON CONFLICT ("businessID") DO UPDATE SET
                            "amenities" = EXCLUDED."amenities",
                            links = EXCLUDED.links,
                            "updateDate" = EXCLUDED."updateDate",
                            "previousID" = EXCLUDED."previousID",
                            "about" = EXCLUDED."about"
                    """,
                        detail_data,
                    )

                # Insert busyTimes

                if data.get("busyTimes"):
                    busyTimes = data["busyTimes"]
                    try:
                        # Convert the busyTime object to a dictionary
                        for item in busyTimes:
                            busy_time_data = vars(item)

                            cursor.execute(
                                """
                                INSERT INTO OpenedHoursBusy (
                                    "businessID", "date", "dayOfWeek", "hour", "percent"
                                ) VALUES (
                                    %(businessID)s, %(date)s, %(DayOfWeek)s, %(Hour)s, %(Percent)s
                                )
                                
                                """,
                                busy_time_data,
                            )
                    except psycopg2.Error as e:
                        print(f"Failed to insert busy time record: {str(e)}")
                        conn.rollback()

                # Insert Reviews
                if data.get("reviewers"):
                    for reviewer in data["reviewers"]:
                        reviewer_data = vars(reviewer)
                        reviewer_data["photoUrls"] = (
                            Json(reviewer_data["photoUrls"])
                            if reviewer_data["photoUrls"]
                            else None
                        )
                        reviewer_data["locPatterns"] = (
                            Json(reviewer_data["locPatterns"])
                            if reviewer_data["locPatterns"]
                            else None
                        )
                        reviewer_data["associatedURLs"] = (
                            Json(reviewer_data["associatedURLs"])
                            if reviewer_data["associatedURLs"]
                            else None
                        )
                        reviewer_data["assosciatedUsernames"] = (
                            Json(reviewer_data["assosciatedUsernames"])
                            if reviewer_data["assosciatedUsernames"]
                            else None
                        )
                        # print(reviewer_data['reviewerID'])
                        cursor.execute(
                            """
                            INSERT INTO Reviewer (
                                "reviewerID", "userName", bio, followers,
                                following, "userProfileLink", "userProfilePicture",
                                "photoUrls", "postID", email, occupation, persona,
                                age, "nickname", "firstName", "lastName", "updateDate",
                                "homeLocation", "homeRegion", "locPatterns",
                                "associatedURLs", "assosciatedUsernames", details,
                                "ownerOf", "affiliateOf", "socialID", "isBusiness","reviewCount","photoCount"
                            ) VALUES (
                                %(reviewerID)s, %(userName)s,
                                %(bio)s, %(followers)s, %(following)s,
                                %(userProfileLink)s, %(userProfilePicture)s,
                                %(photoUrls)s, %(postID)s, %(email)s,
                                %(occupation)s, %(persona)s, %(age)s, %(nickname)s,
                                %(firstName)s, %(lastName)s, %(updateDate)s,
                                %(homeLocation)s, %(homeRegion)s, %(locPatterns)s,
                                %(associatedURLs)s, %(assosciatedUsernames)s,
                                %(details)s, %(ownerOf)s, %(affiliateOf)s,
                                %(socialID)s, %(isBusiness)s,%(reviewCount)s,%(photoCount)s
                            )
                            ON CONFLICT ("reviewerID") DO UPDATE SET
                                "userName" = EXCLUDED."userName",
                                bio = EXCLUDED.bio,
                                followers = EXCLUDED.followers,
                                following = EXCLUDED.following,
                                "userProfileLink" = EXCLUDED."userProfileLink",
                                "userProfilePicture" = EXCLUDED."userProfilePicture",
                                "photoUrls" = EXCLUDED."photoUrls",
                                "postID" = EXCLUDED."postID",
                                email = EXCLUDED.email,
                                occupation = EXCLUDED.occupation,
                                persona = EXCLUDED.persona,
                                age = EXCLUDED.age,
                                "nickname" = EXCLUDED."nickname",
                                "firstName" = EXCLUDED."firstName",
                                "lastName" = EXCLUDED."lastName",
                                "updateDate" = EXCLUDED."updateDate",
                                "homeLocation" = EXCLUDED."homeLocation",
                                "homeRegion" = EXCLUDED."homeRegion",
                                "locPatterns" = EXCLUDED."locPatterns",
                                "associatedURLs" = EXCLUDED."associatedURLs",
                                "assosciatedUsernames" = EXCLUDED."assosciatedUsernames",
                                details = EXCLUDED.details,
                                "ownerOf" = EXCLUDED."ownerOf",
                                "affiliateOf" = EXCLUDED."affiliateOf",
                                "socialID" = EXCLUDED."socialID",
                                "isBusiness" = EXCLUDED."isBusiness",
                                "reviewCount" = EXCLUDED."reviewCount",
                                "photoCount" = EXCLUDED."photoCount"
                        """,
                            reviewer_data,
                        )

                if data.get("reviews"):

                    for review in data["reviews"]:
                        review_data = vars(review)
                        review_data["derivedSignals"] = (
                            Json(review_data["derivedSignals"])
                            if review_data["derivedSignals"]
                            else None
                        )
                        review_data["otherMentions"] = (
                            Json(review_data["otherMentions"])
                            if review_data["otherMentions"]
                            else None
                        )
                        try:
                            cursor.execute(
                                """
                                INSERT INTO Review (
                                    "reviewID", "businessID", url, platform, "reviewerID", "ratingRaw",
                                    "ratingScaled", "reviewText", "ownerResponse", upvotes,
                                    "reviewSentiment", "reviewQuality", defunct, edited,
                                    length, views, "isLocal", "derivedSignals", parent,
                                    child, "updateDate", "reviewDate", "reviewViews",
                                    "reviewLength", "reviewValidity",
                                    "priorVersions", "otherMentions", "productID"
                                ) VALUES (
                                    %(reviewID)s, %(businessID)s, %(url)s, %(platform)s, %(reviewerID)s,
                                    %(ratingRaw)s, %(ratingScaled)s, %(reviewText)s,
                                    %(ownerResponse)s, %(upvotes)s, %(reviewSentiment)s,
                                    %(reviewQuality)s, %(defunct)s, %(edited)s,
                                    %(length)s, %(views)s, %(isLocal)s,
                                    %(derivedSignals)s, %(parent)s, %(child)s,
                                    %(updateDate)s, %(reviewDate)s, %(reviewViews)s,
                                     %(reviewLength)s,
                                    %(reviewValidity)s, %(priorVersions)s,
                                    %(otherMentions)s, %(productID)s
                                )
                                ON CONFLICT ("reviewID") DO UPDATE SET
                                    "businessID" = EXCLUDED."businessID",
                                    url = EXCLUDED.url,
                                    platform = EXCLUDED.platform,
                                    "reviewerID" = EXCLUDED."reviewerID",
                                    "ratingRaw" = EXCLUDED."ratingRaw",
                                    "ratingScaled" = EXCLUDED."ratingScaled",
                                    "reviewText" = EXCLUDED."reviewText",
                                    "ownerResponse" = EXCLUDED."ownerResponse",
                                    upvotes = EXCLUDED.upvotes,
                                    "reviewSentiment" = EXCLUDED."reviewSentiment",
                                    "reviewQuality" = EXCLUDED."reviewQuality",
                                    defunct = EXCLUDED.defunct,
                                    edited = EXCLUDED.edited,
                                    length = EXCLUDED.length,
                                    views = EXCLUDED.views,
                                    "isLocal" = EXCLUDED."isLocal",
                                    "derivedSignals" = EXCLUDED."derivedSignals",
                                    parent = EXCLUDED.parent,
                                    child = EXCLUDED.child,
                                    "updateDate" = EXCLUDED."updateDate",
                                    "reviewDate" = EXCLUDED."reviewDate",
                                    "reviewViews" = EXCLUDED."reviewViews",
                                    "reviewLength" = EXCLUDED."reviewLength",
                                    "reviewValidity" = EXCLUDED."reviewValidity",
                                    "priorVersions" = EXCLUDED."priorVersions",
                                    "otherMentions" = EXCLUDED."otherMentions",
                                    "productID" = EXCLUDED."productID"

                                """,
                                review_data,
                        )


                        except psycopg2.Error as e:
                            conn.rollback()
                            # print(f"\nDatabase error occurred for business {data.get('business', {}).get('businessID')}:")
                            print(f"Error1: {str(e)}")
                            print("\nFull traceback:")
                            traceback.print_exc()
                            exit()
                        except Exception as e:
                            conn.rollback()
                            # print(f"\nUnexpected error occurred for business {data.get('business', {}).get('businessID')}:")
                            print(f"Error2: {str(e)}")
                            print("\nFull traceback:")
                            traceback.print_exc()
                            exit()

            conn.commit()
        # print("Inserted Data into DB")


def connect_to_db(dbname: str, user: str, password: str, host: str, port: str = "5432"):
    """Create a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )


def main():

    service = get_drive_service()

    # Your folder ID where the ZIP files are stored

    # folder_id = "1A_eF-PToLPjxKTxtrjgVooDSk9tT40jv" #batch.zip, dataset.zip Archive.zip Portugal

    # folder_id = "1iKvODgwo74KXHOlgXB9RKi8ip0ciOPAu"  # cumulative.zip Saltillo

    folder_id = "14QGMsDy1UNBmkbDlH7x7hmOoL42w-a17" #final set, finaltotal.zip

    # Get all ZIP files
    zip_files = get_zip_files(service, folder_id)

    if not zip_files:
        print("No ZIP files found in the specified folder")
        return

    # Process each ZIP file
    with connect_to_db(**db_config) as conn:
        onlyPost = False

        parser = argparse.ArgumentParser(add_help=False)

        parser.add_argument(
            "--path_to_sql_file",
            type=str,
            default=None,
            help="sql schema",
        )

        parser.add_argument(
            "--onlyPostProcess",
            type=bool,
            default=False,
            help="set to True if you only want to execute the post processing steps. default is false",
        )

        parser.add_argument(
            "--postProcessFuncsToExecute",
            nargs='+',
            type=str,  
            default=[],
            help="Arguments to pass to allPostProcessing function",
        )

        parser.add_argument(
            "--onlyInjectFolders",
            nargs='+',
            type=str,
            default=None,
            help="only inject these zip folders in the folder",
        )
        parser.add_argument(
            "--help", "-h",
            action="help",
            default=argparse.SUPPRESS,
            
        )


       

        args = parser.parse_args()
        

        

        if args.onlyPostProcess:
            print("HERE")
            allPostProcessing(conn, conn.cursor(), args.postProcessFuncsToExecute)
           
            exit()
        

        # Check if table reset is requested
        if args.path_to_sql_file:
            print("AHHHH")
            execute_sql_file(conn, args.path_to_sql_file)
        else:
            print("did not clear the database. appending rows if applicable")
        
        toInject = args.onlyInjectFolders if args.onlyInjectFolders else zip_files
        # print(toInject)

        for zip_file in toInject:
            if type(zip_file) == dict:
                name = zip_file['name']
            elif type(zip_file) == str:
                name = zip_file
            else:
                print("WTF how is this possible")
                exit()

            length = 0
            #///////////////////////////////////////////////////////////////////////////////////////
            # if name'] not in toInject:
            #     continue
            #///////////////////////////////////////////////////////////////////////////////////////
            start = time.time()
            print(f"\nProcessing ZIP file: {name}")
            try:
                # Download ZIP
                zip_path = download_zip(service, zip_file["id"],name) #

                for tables in extract_and_process_jsons(zip_path, True): #first run through, only add the shopping centers
                    length += len(tables)
                    insert_business_data(conn, tables, True)
                print("AJJJJJJJJJJJJJJJJJJJJJJ")
                

            except Exception as e:
                print(
                    f"Thereis an Error processing ZIP file {name}: {str(e)}"
                )
                traceback.print_exc()
                continue

            end = time.time()
            print(f"{name} executed in {end-start} seconds. {length} tables inserted\n\n")


        for zip_file in zip_files:

            if type(zip_file) == dict:
                name = zip_file['name']
            elif type(zip_file) == str:
                name = zip_file
            else:
                print("WTF how is this possible")
                exit()
            
            length = 0
            #///////////////////////////////////////////////////////////////////////////////////////
            # if name not in toInject:
            #     print("MMMMMMMMMMMMMMMMMMMM")
            #     continue
            #///////////////////////////////////////////////////////////////////////////////////////
            start = time.time()
            print(f"\nProcessing ZIP file again: {name}")
            try:
                # Download ZIP
                zip_path = download_zip(service, zip_file["id"], name)

                for tables in extract_and_process_jsons(zip_path, False): #first run through, only add the shopping centers
                    length += len(tables)
                    insert_business_data(conn, tables, False)
                

            except Exception as e:
                print(
                    f"Thereis an Error processing ZIP file again {name}: {str(e)}"
                )
                traceback.print_exc()
                continue

            end = time.time()
            print(f"{name} executed again in {end-start} seconds. {length} tables inserted\n\n")

    #POSTPROCESSING!
         
        allPostProcessing(conn, conn.cursor())

# def mainTesting():
#     with connect_to_db(**db_config) as conn:
#         parser = argparse.ArgumentParser(
#             description="Executes the listed SQL file before data is added"
#         )

#         parser.add_argument(
#             "--path_to_sql_file",
#             type=str,
#             default="create-tables.sql",
#             help="sql schema",
#         )

#         args = parser.parse_args()

#         # Check if table reset is requested
#         if args.path_to_sql_file:
#             execute_sql_file(conn, args.path_to_sql_file)

#         print("\nProcessing ZIP file: Home Depot")
#         try:
#             with open("The_Home_Depot_Uruapan.json", "r") as file:
#                 python_dict = json.load(file)

#             # for tables in process_google_json(python_dict, "02/26/2025"):

#             insert_business_data(
#                 conn,
#                 [
#                     process_google_json(
#                         python_dict, datetime.strptime("02/26/2025", "%m/%d/%Y").date(), True #first run through, only add shopping malls
#                     )
#                 ],
#             )

#             insert_business_data(
#                 conn,
#                 [
#                     process_google_json(
#                         python_dict, datetime.strptime("02/26/2025", "%m/%d/%Y").date(), False #add everything else.
#                     )
#                 ],
#             )

#         except Exception as e:
#             print(
#                 f"Thereis an Error processing ZIP file The_Home_Depot_Uruapan.json['name']: {str(e)}"
#             )
#             traceback.print_exc()


if __name__ == "__main__":
    main()

    # os.system(r"pytest .\test\db_auto_validation.py")  # mainTesting()
    test_path = os.path.join("test", "db_auto_validation.py")
    os.system(f"pytest {test_path}")  
