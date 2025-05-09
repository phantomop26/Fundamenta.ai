
import json
import re
from datetime import datetime
from dateutil.parser import parse as date_parse
from dateutil.relativedelta import relativedelta

# --- Load Data ---
try:
    with open('website_data.json', 'r', encoding='utf-8') as f:
        url_data_list = json.load(f)
except FileNotFoundError:
    print("Error: 'data.json' not found.")
    url_data_list = []
except json.JSONDecodeError:
    print("Error: Could not decode JSON from 'data.json'.")
    url_data_list = []

try:
    with open('domain_data.json', 'r', encoding='utf-8') as f:
        domain_data = json.load(f)
except FileNotFoundError:
    print("Warning: 'domain_data.json' not found. Domain age and SSL info will not be fully available.")
    domain_data = {}
except json.JSONDecodeError:
    print("Error: Could not decode JSON from 'domain_data.json'. Domain age and SSL info might be incomplete.")
    domain_data = {}

# --- Signal Definitions (as before) ---
signals_list = [
    {"Category": "Social Media Activity", "Signal": "Social Media Icons/Links"},
    {"Category": "Social Media Activity", "Signal": "Chat Widgets"},
    {"Category": "Social Media Activity", "Signal": "Embedded Reviews"},
    {"Category": "Social Media Activity", "Signal": "Video Embeds"},
    {"Category": "Social Media Activity", "Signal": "Instagram Feeds"},
    {"Category": "Online Transactions", "Signal": "Checkout Buttons / “Buy” CTAs"},
    {"Category": "Online Transactions", "Signal": "Online Transactions"},
    {"Category": "Online Transactions", "Signal": "Shopping Cart / E-commerce System"},
    {"Category": "Online Transactions", "Signal": "Online Booking / Appointment Tools"},
    {"Category": "Online Transactions", "Signal": "Pricing Pages"},
    {"Category": "Online Transactions", "Signal": "E-commerce Features (Add to Cart, Buy Now)"},
    {"Category": "Online Transactions", "Signal": "Pricing Page or Quote Request Options"},
    {"Category": "Online Transactions", "Signal": "Return Policy or Shipping Information"},
    {"Category": "Website Presence & Quality", "Signal": "Presence of Contact Channels"},
    {"Category": "Website Presence & Quality", "Signal": "Site Structure & Pages"},
    {"Category": "Website Presence & Quality", "Signal": "Load Speed & Mobile Optimization"},
    {"Category": "Website Presence & Quality", "Signal": "Language(s) Supported"},
    {"Category": "Website Presence & Quality", "Signal": "Structured Data (Schema.org, JSON-LD)"},
    {"Category": "Website Presence & Quality", "Signal": "Blog or News Section"},
    {"Category": "Website Presence & Quality", "Signal": "Accessibility Tags (e.g., alt text)"},
    {"Category": "Website Presence & Quality", "Signal": "Email Capture Forms"},
    {"Category": "Website Presence & Quality", "Signal": "Newsletter Tools Used"},
    {"Category": "Website Presence & Quality", "Signal": "Return Policies / FAQs"},
    {"Category": "Website Presence & Quality", "Signal": "Website Availability"},
    {"Category": "Website Presence & Quality", "Signal": "Domain Age and SSL Certificate"},
    {"Category": "Website Presence & Quality", "Signal": "Mobile-Friendliness and Speed"},
    {"Category": "Website Presence & Quality", "Signal": "Phone Responsiveness"},
    {"Category": "Website Presence & Quality", "Signal": "Business Transparency & Credibility"},
    {"Category": "Website Presence & Quality", "Signal": "Website Updated 6 Months Ago?"},
    {"Category": "Website Presence & Quality", "Signal": "Social Updated Less Than 1 Month Ago"},
    {"Category": "Website Presence & Quality", "Signal": "Replies to Reviews"},
    {"Category": "User Engagement Features", "Signal": "Social Media Links (Facebook, Instagram, etc.)"},
    {"Category": "Reputation & Outreach", "Signal": "Google Maps Embeds / GMB Links"},
    {"Category": "Reputation & Outreach", "Signal": "Embedded Reviews (Google, Yelp, TripAdvisor)"},
    {"Category": "Reputation & Outreach", "Signal": "SEO Tags and Page Metadata"},
    {"Category": "Reputation & Outreach", "Signal": "Testimonials or Ratings"},
    {"Category": "Technology Stack", "Signal": "CMS (WordPress, Shopify, Wix, etc.)"},
    {"Category": "Technology Stack", "Signal": "CRM / Marketing Tools (HubSpot, Mailchimp, etc.)"},
    {"Category": "Technology Stack", "Signal": "Analytics (Google Analytics, Facebook Pixel)"},
    {"Category": "Technology Stack", "Signal": "Tag Managers or Script-Based Integrations"},
    {"Category": "User Engagement Features", "Signal": "Affiliate program"},
    {"Category": "User Engagement Features", "Signal": "Presence Destribution Platform"}
]

# --- Social Media Platforms (as before) ---
social_media_platforms = {
    "facebook": r"facebook\.com",
    "instagram": r"instagram\.com",
    "tiktok": r"tiktok\.com",
    "whatsapp": r"whatsapp\.com",
    "twitter": r"twitter\.com",
    "linkedin": r"linkedin\.com",
    "youtube": r"youtube\.com",
    "pinterest": r"pinterest\.com"
}

def extract_domain_info(raw_whois):
    """Extracts domain age and SSL presence from raw WHOIS data."""
    creation_date = None
    ssl_present = False

    if raw_whois:
        creation_date_match = re.search(r"Creation Date:\s*([A-Za-z0-9\-\:T\.]+Z?[-\+]\d{4})", raw_whois)
        if creation_date_match:
            try:
                creation_date = date_parse(creation_date_match.group(1))
            except ValueError:
                creation_date = None

        # Basic check for SSL keywords in WHOIS (might not be definitive)
        if "SSL" in raw_whois or "TLS" in raw_whois or "certificate" in raw_whois.lower():
            ssl_present = True

    return creation_date, ssl_present

def analyze_url_data(url_data, domain_info):
    """
    Analyzes the data for a single URL, incorporating domain information.

    Args:
        url_data (dict): A dictionary containing 'url', 'text', and 'links'.
        domain_info (dict): Domain-specific information from domain_data.json.

    Returns:
        dict: A dictionary containing the URL, found social media links, and detected signals.
    """
    url = url_data.get("url", "N/A")
    text = url_data.get("text", "").lower()
    links = url_data.get("links", [])
    domain = re.search(r"^(?:https?:\/\/)?(?:www\.)?([^\/]+)", url)
    domain_name = domain.group(1) if domain else None

    results = {
        "url": url,
        "social_media_links": {},
        "signals": {}
    }

    # --- Extract Social Media Links (as before) ---
    for platform, regex in social_media_platforms.items():
        results["social_media_links"][platform] = [link for link in links if re.search(regex, link)]

    emails_in_text = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    emails_in_links = re.findall(r"mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", " ".join(links))
    results["social_media_links"]["email"] = list(set(emails_in_text + emails_in_links))

    phone_numbers = re.findall(r"(?:\+\d{1,3}[-\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    results["social_media_links"]["phone"] = list(set(phone_numbers))

    # --- Detect Signals based on Text and Links (mostly as before) ---
    detected_signals = {}

    # Social Media Activity
    detected_signals["Social Media Icons/Links"] = any(results["social_media_links"].values()) and any(len(v) > 0 for v in results["social_media_links"].values() if v)
    detected_signals["Chat Widgets"] = "live chat" in text or "support" in text and "online" in text
    detected_signals["Embedded Reviews"] = "reviews" in text and ("google" in text or "yelp" in text or "tripadvisor" in text)
    detected_signals["Video Embeds"] = "youtube.com/embed" in " ".join(links) or "<iframe" in text and "video" in text
    detected_signals["Instagram Feeds"] = "instagram.com/embed" in " ".join(links) or "instagram feed" in text

    # Online Transactions
    detected_signals["Checkout Buttons / “Buy” CTAs"] = "checkout" in text or "buy now" in text or "purchase" in text
    detected_signals["Online Transactions"] = "order" in text or "transaction" in text or "payment" in text
    detected_signals["Shopping Cart / E-commerce System"] = "cart" in text or "add to cart" in text
    detected_signals["Online Booking / Appointment Tools"] = "book now" in text or "appointment" in text or "schedule" in text
    detected_signals["Pricing Pages"] = "pricing" in links or "price" in text or "plans" in text
    detected_signals["E-commerce Features (Add to Cart, Buy Now)"] = "add to cart" in text or "buy now" in text
    detected_signals["Pricing Page or Quote Request Options"] = "quote" in text or "request a quote" in text or detected_signals["Pricing Pages"]
    detected_signals["Return Policy or Shipping Information"] = "return policy" in text or "shipping" in text

    # Website Presence & Quality
    detected_signals["Presence of Contact Channels"] = "contact us" in text or "contact" in links or results["social_media_links"].get("email") or results["social_media_links"].get("phone")
    detected_signals["Site Structure & Pages"] = len(links) > 5
    detected_signals["Load Speed & Mobile Optimization"] = False
    detected_signals["Language(s) Supported"] = len(re.findall(r'lang="[a-z]{2}"', text)) > 0
    detected_signals["Structured Data (Schema.org, JSON-LD)"] = "schema.org" in text or "application/ld+json" in text
    detected_signals["Blog or News Section"] = "blog" in links or "news" in links or "articles" in links
    detected_signals["Accessibility Tags (e.g., alt text)"] = "alt=" in text
    detected_signals["Email Capture Forms"] = "subscribe" in text and "email" in text and "form" in text
    detected_signals["Newsletter Tools Used"] = "mailchimp" in text or "constant contact" in text or "newsletter" in text
    detected_signals["Return Policies / FAQs"] = "return policy" in text or "faq" in links or "frequently asked questions" in text
    detected_signals["Website Availability"] = True

    # Domain Age and SSL Certificate
    domain_raw_data = domain_info.get(domain_name)
    creation_date, ssl_present = extract_domain_info(domain_raw_data.get("raw_whois_data", "") if domain_raw_data else "")
    detected_signals["Domain Age and SSL Certificate"] = creation_date is not None and ssl_present

    detected_signals["Mobile-Friendliness and Speed"] = False
    detected_signals["Phone Responsiveness"] = results["social_media_links"].get("phone")
    detected_signals["Business Transparency & Credibility"] = "about us" in links or "our team" in links or "mission" in text or "vision" in text
    detected_signals["Website Updated 6 Months Ago?"] = False # Cannot determine from provided data
    detected_signals["Social Updated Less Than 1 Month Ago"] = False # Cannot determine from provided data
    detected_signals["Replies to Reviews"] = "replied to a review" in text or "response from" in text

    # User Engagement Features
    detected_signals["Social Media Links (Facebook, Instagram, etc.)"] = detected_signals["Social Media Icons/Links"]
    detected_signals["Affiliate program"] = "affiliate" in text or "referral program" in text
    detected_signals["Presence Destribution Platform"] = False # Cannot determine from provided data

    # Reputation & Outreach
    detected_signals["Google Maps Embeds / GMB Links"] = "google.com/maps/embed" in " ".join(links) or "google business profile" in text
    detected_signals["Embedded Reviews (Google, Yelp, TripAdvisor)"] = detected_signals["Embedded Reviews"]
    detected_signals["SEO Tags and Page Metadata"] = "<title>" in text or "<meta name=\"description\"" in text or "<meta name=\"keywords\"" in text
    detected_signals["Testimonials or Ratings"] = "testimonial" in text or "rating" in text or "customer reviews" in text

    # Technology Stack
    detected_signals["CMS (WordPress, Shopify, Wix, etc.)"] = "wordpress" in text or "shopify" in text or "wix" in text or "squarespace" in text
    detected_signals["CRM / Marketing Tools (HubSpot, Mailchimp, etc.)"] = "hubspot" in text or "mailchimp" in text or "salesforce" in text
    detected_signals["Analytics (Google Analytics, Facebook Pixel)"] = "google analytics" in text or "googletagmanager" in text or "facebook pixel" in text
    detected_signals["Tag Managers or Script-Based Integrations"] = "googletagmanager" in text or "script" in text and "src=" in text

    results["signals"] = {signal_item["Signal"]: detected_signals.get(signal_item["Signal"], False) for signal_item in signals_list}

    return results

# Process each URL in the data
analysis_results = [analyze_url_data(item, domain_data) for item in url_data_list]

# --- Save the analysis results to a JSON file ---
output_filename = "analyzed_data_with_domain.json"
try:
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        json.dump(analysis_results, outfile, indent=4)
    print(f"\nAnalysis results (including domain info) saved to '{output_filename}'")
except IOError as e:
    print(f"Error saving to '{output_filename}': {e}")