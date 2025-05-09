from datetime import date
from typing import Dict, Any, List
from uuid import uuid4
from decimal import Decimal
import re
import csv
from dateutil.relativedelta import relativedelta
from functions.classTables import (
    Business,
    Product,
    Reviewer,
    Social,
    Search,
    Contact,
    Metrics,
    PostProducts,
    Region,
    ReviewerAffiliates,
    Address,
    SupplierCustomer,
    Review,
    ShoppingCenterBusinesses,
    Post,
    ReviewerOwns,
    Detail,
    OpenedHoursBusy,
    ReviewerHistory
)
from functions.hashingFunctions import hash_object, hash_to_uuid
from psycopg2.extras import Json
from datetime import datetime


personaDiction = {"Local Guide": 1, "New": 2, "Google": 3, "Owner": 4}
malls = set()
noPlaceDetails = 0

def sanitize(value):
    """Sanitize a string value by replacing non-alphanumeric characters with underscores."""
    if isinstance(value, str):
        return re.sub(r"[^a-zA-Z0-9]", "_", value.strip())

    return value

def check_string_in_csv(csv_file, search_string):
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if any(search_string in cell for cell in row):
                return True
        return False


def parse_coordinates_from_url(url: str) -> tuple[float, float]:
    """Extract latitude and longitude from Google Maps URL."""
    lat_match = re.search(r"!3d(-?\d+\.\d+)", url)
    lng_match = re.search(r"!4d(-?\d+\.\d+)", url)

    if lat_match and lng_match:
        return float(lat_match.group(1)), float(lng_match.group(1))
    return None, None


def parse_rating(rating_str: str) -> float:
    """Convert rating string (e.g., '4,4' or '5 estrelas') to float."""
    if not rating_str:
        return None
    # Handle '4,4' format
    rating_str = rating_str.replace(",", ".")
    # Handle '5 estrelas' format
    rating_str = rating_str.split()[0]
    try:
        return float(rating_str)
    except ValueError:
        return None


def extract_phone_email_website(details):
    if not details:             
        return None, None, None
    """Extract phone number, email, and website from details list."""

    phone = None
    email = None
    website = None

    
    if (
        len(details) == 1
    ):  # phone number is typically in the 1th index, but if there is only 1 item, it may be the only item (idx 0)
        idx = 0
    else:
        idx = 1
    pattern = r"^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+$"  # for finding characters.characters.characters,etc.
    stringToCheck = details[idx].encode("ascii", "ignore").decode("ascii").strip() if isinstance(details[0], str) else details[idx]['text'].encode("ascii", "ignore").decode("ascii").strip()
    # get rid of emojis. sometimes its a list of dictionaries and the string is under ['text']

    if (
        " " not in stringToCheck
        and "." in stringToCheck
        and re.match(pattern, stringToCheck)
    ):
        website = stringToCheck

    for detail in details:
        # if isinstance(detail, dict):
        #     if "Located in" in detail['text']:
        #         with open("output.txt", 'a') as file:
        #             mall = detail['text'].split('Located in: ')[1]
        #             if mall not in malls:
        #                 file.write(f"{mall}\n")
        #                 malls.add(mall)

        detail = detail.replace("\ue0b0", "").replace("\ue14d", "").strip() if isinstance(details[0], str) else detail['text'].replace("\ue0b0", "").replace("\ue14d", "").strip() 
        
        
        if detail.startswith("+"):
            phone = detail
        elif "@" in detail:
            email = detail

    return phone, email, website
    
    
        
'''
[{'text': '\ue0c8C. Prol. Urdiñola 1074, La Madrid, 25050 Saltillo, Coah., Mexico\ue14d', 'href': None}, 
{'text': '\ue0b0+52 18441461414\ue14d\ue0b0', 'href': 'tel:+52%2018441461414'},
 {'text': '\uf186C236+Q2 Saltillo, Coahuila, Mexico\ue14d\ue88e', 'href': None},
   {'text': '\ue8e8Claim this business\ue89e', 'href': 'https://business.google.com/create?fp=17046739287421048058&hl=en&authuser=0&gmbsrc=us-en-et-ip-z-gmb-s-z-l~mrc%7Cclaimbz%7Cu&ppsrc=GMBMI&utm_campaign=us-en-et-ip-z-gmb-s-z-l~mrc%7Cclaimbz%7Cu&utm_source=gmb_mrc81&utm_medium=et&getstarted&lis=0'}]
'''



def parse_review_date(dateString):
    if "anos" in dateString:
        yearsAgo = int(dateString.split(" ")[0])
        return date.today() - relativedelta(years=yearsAgo)

    elif "ano" in dateString:
        return date.today() - relativedelta(years=1)

    elif "mês" in dateString:
        return date.today() - relativedelta(months=1)

    elif "meses" in dateString:
        monthsAgo = int(dateString.split(" ")[0])
        return date.today() - relativedelta(months=monthsAgo)

    elif "semana" in dateString:
        return date.today() - relativedelta(weeks=1)

    elif "semanas" in dateString:
        weeksAgo = int(dateString.split(" ")[0])
        return date.today() - relativedelta(weeks=weeksAgo)

    elif "dia" in dateString:
        return date.today() - relativedelta(days=1)

    elif "dias" in dateString:
        daysAgo = int(dateString.split(" ")[0])
        return date.today() - relativedelta(days=daysAgo)

    else:
        return date.today()


def is_dot_pattern_string(text):
    if not isinstance(text, str):
        return False

    pattern = r"^[^\s\.]+\.[^\s\.]+$"
    return bool(re.match(pattern, text))


def process_address(address):
    if not address:
        return {"country": None, "city": None, "zipCode": None, "addressName": None}

    if (
        is_dot_pattern_string(address) or address[0] == "+"
    ):  # sometimes the address is a website or phone number
        return {"country": None, "city": None, "zipCode": None, "addressName": None}

    # pattern = r'\b\d{4}-\d{3}\b' #Portugal
    pattern = r"\b\d{5}\b"  # Saltillo
    matches = re.findall(
        pattern, address
    )  # not all(x == matches[0] for x in matches[1:])

    if len(matches) >= 1:
        zipCode = matches[
            0
        ]  # PERHAPS check what comes before and after the zipcode. I'm pretty sure that if there is a city, itll come after the zipcode
    else:
        zipCode = None

    address = address.split(", ")
    if any(char.isdigit() for char in address[-1]):
        country = None
    else:
        country = (
            address.pop()
        )  # does not account for the possibility that the address is just the city
    if not address:
        return {"country": country, "city": None, "zipCode": None, "addressName": None}

    city = address.pop()  # could be ####-### city, city, or street number, or ####

    if city.isdigit() and not zipCode:  # accounts for 5240 Portugal
        zipCode = int(city)

    elif zipCode and zipCode in city: #if there is a zipCode, get rid of it, the rest of the string is the city.
        city = city.replace(zipCode, "").strip() 
    
    else: #street information, Portugal
        address.append(city) #just put it back in the string
    
    addressName = ", ".join(address) 
  
 
        

    return {
        "country": country,
        "city": city,
        "zipCode": zipCode,
        "addressName": addressName,
    }


def parse_name(username):
    words = username.split(" ")
    if len(words) == 1:
        return words[0], None

    first_word = words[0]
    rest_of_string = " ".join(words[1:])

    return first_word, rest_of_string


def process_google_json(data: Dict[str, Any], modDate, firstRunThrough, filename = None):
    """Parse Google Maps JSON data into our database classes."""
    
    
    if "placeDetails" not in data: #some files are just a list of the google maps link. skip these
    
        return None
    
    # if data['placeDetails']['category'] == "Shopping mall":
    #     print(data['placeDetails']['name'])
    
    if firstRunThrough and data['placeDetails']['category'] != "Shopping mall": #on the first run through, only add the shopping malls.
        return None

    if not firstRunThrough and data['placeDetails']['category'] == "Shopping mall":
        return None

    if not data["placeDetails"]["name"]:
        return None

    business = None
    address = None
    contact = None
    detail = None
    reviewers = None
    reviews = None
    scb = None

    business = Business()

    business.name = data["placeDetails"]["name"]
    # if check_string_in_csv("missingMalls.csv", data["placeDetails"]["name"]):
    #     print("x")
    #     for item in data["placeDetails"].get("Details", []): #find #LOCATED IN
                
    #         check = "Located in:" in item['text'] if isinstance(item, dict) else "Located in:" in item
    #         if check:
    #             mall = item['text'].split('Located in: ')[1] if isinstance(item, dict) else item.split('Located in: ')[1]
    #             with open("actualMissingMalls.csv", 'a', newline='', encoding='utf-8') as file:
    #                 writer = csv.writer(file)
    #                 writer.writerow(mall)


    business.price = (
        data["placeDetails"]["price"] if data["placeDetails"]["price"] else None
    )

    if "url" in data:
        lat, lng = parse_coordinates_from_url(data["url"])
        business.gmapsURL = data["url"]
        business.latitude = Decimal(str(lat)) if lat else None
        business.longitude = Decimal(str(lng)) if lng else None
    
    business.updateDate = date.today().strftime('%Y-%m-%d')
    business.rating = float(data['placeDetails']['rating'].replace(",",".")) if data['placeDetails']['rating'] else None
    business.totalReviews = int(data['placeDetails']['totalReviews'][1:-1].replace(",","").replace(".","")) if data['placeDetails']['totalReviews'] else 0
    business.permclosed = data['placeDetails']['perclose'] != None if 'perclose' in data['placeDetails'] else False #if its None, then the place is open and this is False
    
    business.locationCount = 1
    business.category = data['placeDetails']['category'] if data['placeDetails']['category'] != "Adicionar hor\u00e1rio" else None

    if not firstRunThrough:
        for item in data["placeDetails"].get("Details", []): #find #LOCATED IN
                
            check = "Located in:" in item['text'] if isinstance(item, dict) else "Located in:" in item
            if check:
                mall = item['text'].split('Located in: ')[1] if isinstance(item, dict) else item.split('Located in: ')[1]
                business.shoppingCenterID = hash_to_uuid(mall)
                    
    


    
    if business.category == "Shopping mall":
        scb = ShoppingCenterBusinesses()
        scb.shoppingCenterID = hash_to_uuid(business.name)

        business.isShoppingCenter = True
        business.shoppingCenterID = scb.shoppingCenterID
    else:
        business.isShoppingCenter = False
        




    # Create Detail instance
    detail = Detail()
    if 'about' in data['aboutDetails']:
        detail.about = data['aboutDetails']['about']
    else:
        print(data['aboutDetails'])
        import os
        file_exists = os.path.isfile("missingAbout.csv")
    
        with open("missingAbout.csv", 'a', newline='') as csvfile:
            fieldnames = ['filename']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write the filename
            writer.writerow({'filename': filename})


    # print(data['aboutDetails']['aboutbadges'])
    if "aboutbadges" in data['aboutDetails']:
        detail.amenities = data['aboutDetails']['aboutbadges'] 
    elif "categories" in data['aboutDetails']:
        detail.amenitites = data['aboutDetails']['categories']
    
    detail.updateDate = date.today().strftime('%Y-%m-%d')

    if not business.name:
        print("business name is empty")
        print(data)

    # Create Address instance
    
    # Create Contact instance
    contact = Contact()
    contact.phone, contact.email, contact.businessURL = extract_phone_email_website(data["placeDetails"].get("Details", []))
  
    contact.updateDate = date.today().strftime("%Y-%m-%d")
    if not contact.phone and not contact.businessURL and not contact.updateDate:
        contact = None

    if data["placeDetails"]["address"]:
        addressDict = process_address(data["placeDetails"]["address"])
        if addressDict:
            address = Address()

            # if data["placeDetails"]["address"].startswith("+"):
            #     contact.phone = data["placeDetails"]["address"]
            #     print(contact.phone)
            # elif " " not in data["placeDetails"]["address"] and "." in data["placeDetails"]["address"] and re.match(r"^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+$", data["placeDetails"]["address"]):
            #     contact.businessURL = data["placeDetails"]["address"]
            # else:
            address.addressFull = data["placeDetails"]["address"]
            address.addressCity = addressDict["city"]
            address.addressCountry = addressDict["country"]
            address.addressPostalCode = addressDict["zipCode"]
            address.addressName = addressDict["addressName"]
            address.updateDate = date.today().strftime("%Y-%m-%d")

            for attr_name in dir(address): #checks all address values for either phone number or businessURL
                if not attr_name.startswith('__'):
                    value = getattr(address, attr_name)
                    if not value or type(value) != str:
                        continue
                    if value.startswith("+"):
                        contact.phone = data["placeDetails"]["address"]
                        setattr(address, attr_name, None)
                    elif  " " not in value and "." in value and re.match(r"^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+$", value):
                        contact.businessURL = data["placeDetails"]["address"]
                        setattr(address, attr_name, None)




    business.businessID = hash_to_uuid(sanitize(business.name) + business.gmapsURL)

    if address:
        address.businessID = business.businessID
    if detail:
        detail.businessID = business.businessID

    if contact:
        contact.businessID = business.businessID

    busyTimes = []
    if data['busyTimes']:
        for hourInfo in data['busyTimes']:

            busyTime = OpenedHoursBusy()
            busyTime.date = datetime.strptime(hourInfo["date"], "%Y-%m-%d").date()
            busyTime.DayOfWeek = hourInfo["day"]
            busyTime.Hour = hour = datetime.strptime(
                hourInfo["time"].replace(".", ""), "%I %p"
            ).hour  # convert to 24h time
            busyTime.Percent = hourInfo["percentage"]
            busyTime.businessID = business.businessID

            busyTimes.append(busyTime)

    # Process reviews
    reviews = []
    reviewers = []
    for review_data in data["reviews"]:
        # Create Reviewer instance
        reviewer = Reviewer()
        reviewer.userName = review_data["user"]
        firstName, lastName = parse_name(review_data["user"])
        reviewer.firstName = firstName
        reviewer.lastName = lastName
        reviewer.userProfilePicture = review_data["userProfilePicture"]

        if "userHistory" in review_data:
            reviewer.userProfileLink = (
                review_data["userHistory"][0] if review_data["userHistory"] else None
            )  # USER HISTORY LINK IS A LINK TO THEIR PROFILE

        # Parse reviewer details from userTagText
        if "userTagText" in review_data:
            if review_data["userTagText"]:
                tag_parts = review_data["userTagText"].split(" · ")
                if "Local Guide" in tag_parts:
                    reviewer.persona = personaDiction["Local Guide"]
                elif "New" in tag_parts:
                    reviewer.persona = personaDiction["New"]
                elif "Google" in tag_parts:
                    reviewer.persona = personaDiction["Google"]
                elif "Owner" in tag_parts:
                    reviewer.persona = personaDiction["Owner"]

                for part in tag_parts:
                    if "reviews" in part:
                        reviewer.reviewCount = int(part.split(" ")[0].replace(".","").replace(",",""))
                    elif "photos" in part:
                        reviewer.photoCount = int(part.split(" ")[0].replace(".","").replace(",",""))



                    
        reviewer.photoUrls = {i+1: item for i, item in enumerate(review_data['photos'])}
        reviewer.updateDate = date.today().strftime('%Y-%m-%d')
        reviewer.reviewerID = hash_to_uuid(reviewer.userName + reviewer.userProfileLink)
        reviewers.append(reviewer)

        # Create Review instance
        if review_data["reviewDate"]:
            review = Review()
            review.reviewerID = reviewer.reviewerID
            review.platform = "Google Maps"
            review.ratingRaw = int(float(parse_rating(review_data["rating"])))
            review.reviewText = review_data["text"]
            review.upvotes = review_data["likecount"]
            review.reviewLength = len(review_data["text"].split())
            if "ownerResponse" in review_data:
                review.ownerResponse = Json(review_data["ownerResponse"])

            review.reviewDate = datetime.strptime(
                review_data["reviewDate"], "%Y-%m-%d"
            ).date()

            # Format the modification date
            review.updateDate = (
                modDate.strftime("%Y-%m-%d") if isinstance(modDate, date) else modDate
            )

            if "photos" in review_data:
                review.derivedSignals = {
                    "has_photos": True,
                    "photo_count": len(review_data["photos"]),
                }

            review.businessID = business.businessID.replace("'", "")
            review.reviewID = hash_object(review)

            reviews.append(review)

    return {
        "business": business,
        "address": address,
        "contact": contact,
        "detail": detail,
        "busyTimes": busyTimes,
        "reviews": reviews,
        "reviewers": reviewers,
        "shoppingCenterBusinesses": scb
    }


    
def process_reviewerHistory(data: Dict[str, Any], modDate: datetime) -> List[ReviewerHistory]:
    """
    Process reviewer data and create ReviewerHistory objects for each review.
    
    Args:
        data: Dictionary containing profile and reviews data
        modDate: The modification date to use for records
        
    Returns:
        List of ReviewerHistory objects
    """
    result = []
    review_counts = {}

    
    # Extract profile information
    profile = data.get("profile", {})
    reviewer_name = profile.get("name")
    profile_pic_url = profile.get("profilePicUrl")
    review_points = int(profile.get("reviewPoints").split(" ")[0].replace(",","").replace(".","")) if profile.get("reviewPoints") else profile.get("reviewPoints")
    user_tag =  profile.get("userTagOrContributions") 

    # user_tag = int(profile.get("userTagOrContributions").split(" ")[0].replace(",","").replace(".","")) if profile.get("userTagOrContributions") else profile.get("userTagOrContributions")
    profile_link = profile.get("link")
    
    # Generate a UUID for the reviewer - in practice this would likely come from your database
    
    # Process each review
    if not data['reviews']:
        history = ReviewerHistory()

        history.reviewerName = reviewer_name
        history.reviewerProfilePictureURL = profile_pic_url
        history.reviewPoints = review_points
        history.userTagOrContributions = user_tag
        history.profileLink = profile_link
        history.reviewerID = hash_to_uuid(reviewer_name + profile_link)
        # print("this user has no reviews")
        result.append(history)

    
    
    for review in data.get("reviews", []):
        # if review['name'] == None:
        #     print("NAME IS NULL")
        #     print(data['profile']['link'])

        # review_tuple = tuple(sorted((k, str(v)) for k, v in review.items() if v is not None))
        
        # Increment the count for this review
        # if review_tuple in review_counts:
        #     # if review_counts[review_tuple] == 1:
                
        #         # print("\n\n\nTHERE IS A DUPLICATE ------------------------------------------------------------------------------")
        #         # print(data['profile']['link'])
        #         # print(review)
        #         # print(data.get("reviews", []))
        #     review_counts[review_tuple] += 1
        # else:
        #     review_counts[review_tuple] = 1

        # duplicates = {review_tuple: count for review_tuple, count in review_counts.items() if count > 1}
    
        # # Convert the tuple keys back to dictionaries for better readability
        # duplicate_reviews = []
        # for review_tuple, count in duplicates.items():
        #     # Convert the tuple of tuples back to a dictionary
        #     review_dict = {k: v for k, v in review_tuple}
        #     duplicate_reviews.append({
        #         "review": review_dict,
        #         "count": count
        #     })
    
        # if duplicate_reviews: print(duplicate_reviews)


        history = ReviewerHistory()
        
        # Set reviewer information
        history.reviewerID = hash_to_uuid(reviewer_name + profile_link)
        
        
        history.reviewerName = reviewer_name
        history.reviewerProfilePictureURL = profile_pic_url
        history.reviewPoints = review_points
        history.userTagOrContributions = user_tag
        history.profileLink = profile_link
        
        # Set business information
        history.businessName = review.get("name")
        history.businessAddress = review.get("address")
        
        
        # Handle rating (convert from "5 stars" format to Decimal)
        rating_str = review.get("rating", "")
        if rating_str and "stars" in rating_str:
            try:
                stars = rating_str.split()[0]
                history.businessRating = Decimal(stars)
            except (ValueError, IndexError):
                history.businessRating = None
        
        # Set rating time as the original string
        history.ratingTime = review.get("time")
        
        # Set update date to the provided modDate
        history.updateDate = modDate
        
        # Set review content
        history.reviewText = review.get("textReview")
        # if reviewer_name == "Anahi Cisneros":
        #     print(profile_link)
        #     print(history.reviewerID)
        #     print(history.reviewText)
        
        # Handle review tags (assuming texttag might be a comma-separated string)
        text_tag = review.get("texttag")
        if text_tag:
            history.reviewTags = [tag.strip() for tag in text_tag.split(",")]
        
        # Set photos
        history.photos = review.get("photos", [])
        
        # Set owner response (convert from None to False if needed)
        history.ownerResponse = bool(review.get("ownerResponse"))
        
        # if history.businessAddress == 'Calz. Juárez S/N, Félix Ireta, 58070 Morelia, Mich., Mexico' and history.businessName == 'Parque Zoológico Benito Juárez' and history.ratingTime == "6 years ago"and history.businessRating == 5:
        #     print(data['profile']['link'])
        result.append(history)
        # print(history.reviewerName)
    
    return result




