import json
import re
import tldextract

# Load your JSON file
with open('website_data.json', 'r', encoding='utf-8') as f:
    websites = json.load(f)

# Patterns for identifying signals
social_media_domains = {
    'facebook.com': 'Facebook',
    'instagram.com': 'Instagram',
    'tiktok.com': 'TikTok',
    'linkedin.com': 'LinkedIn',
    'youtube.com': 'YouTube'
}
chat_tools = ['whatsapp.com', 'messenger.com', 'tawk.to', 'livechatinc.com']
video_embeds = ['youtube.com', 'vimeo.com', 'tiktok.com']
review_widgets = ['tripadvisor.com', 'yelp.com', 'google.com/maps']
checkout_services = ['stripe.com', 'paypal.com', 'mercadopago.com', 'squareup.com']
ecommerce_platforms = ['shopify.com', 'woocommerce.com', 'magento.com']
appointment_tools = ['calendly.com', 'acuityscheduling.com', 'booksy.com']
newsletter_tools = ['mailchimp.com', 'hubspot.com', 'sendinblue.com']
keywords_pricing = ['pricing', 'plans', 'quote', 'estimate']

signals = []

# Helper: categorize link
def extract_domain(url):
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

# Iterate through each website
for site in websites:
    url = site.get("url", "")
    links = site.get("links", [])
    text = site.get("text", "")

    for link in links:
        domain = extract_domain(link)

        # Check each signal category
        if any(social in link for social in social_media_domains):
            signals.append({
                "Category": "Social Media Activity",
                "Signal": "Social Media Icons/Links",
                "Description": "Platform presence and outreach",
                "Tags": domain,
                "Source": link
            })

        if any(chat in link for chat in chat_tools):
            signals.append({
                "Category": "Social Media Activity",
                "Signal": "Chat Widgets",
                "Description": "Real-time engagement via chat",
                "Tags": domain,
                "Source": link
            })

        if any(video in link for video in video_embeds):
            signals.append({
                "Category": "Social Media Activity",
                "Signal": "Video Embeds",
                "Description": "Video content marketing",
                "Tags": domain,
                "Source": link
            })

        if any(review in link for review in review_widgets):
            signals.append({
                "Category": "Social Media Activity",
                "Signal": "Embedded Reviews",
                "Description": "Reputation-building via reviews",
                "Tags": domain,
                "Source": link
            })

        if any(service in link for service in checkout_services):
            signals.append({
                "Category": "Online Transactions",
                "Signal": "Payment Integration",
                "Description": "Embedded checkout/payment options",
                "Tags": domain,
                "Source": link
            })

        if any(platform in link for platform in ecommerce_platforms):
            signals.append({
                "Category": "Online Transactions",
                "Signal": "E-commerce Platform",
                "Description": "Hosted on e-commerce system",
                "Tags": domain,
                "Source": link
            })

        if any(app in link for app in appointment_tools):
            signals.append({
                "Category": "Online Transactions",
                "Signal": "Online Booking Tools",
                "Description": "Service-based appointment scheduler",
                "Tags": domain,
                "Source": link
            })

        if any(news in link for news in newsletter_tools):
            signals.append({
                "Category": "Website Presence & Quality",
                "Signal": "Newsletter Tools Used",
                "Description": "CRM readiness",
                "Tags": domain,
                "Source": link
            })

        if "mailto:" in link:
            signals.append({
                "Category": "Website Presence & Quality",
                "Signal": "Presence of Contact Channels",
                "Description": "Email contact available",
                "Tags": "email",
                "Source": link
            })

        if "tel:" in link:
            signals.append({
                "Category": "Website Presence & Quality",
                "Signal": "Presence of Contact Channels",
                "Description": "Phone contact available",
                "Tags": "phone",
                "Source": link
            })

    # Additional text-based signals
    for keyword in keywords_pricing:
        if keyword.lower() in text.lower():
            signals.append({
                "Category": "Online Transactions",
                "Signal": "Pricing Page or Quote Request Options",
                "Description": "Mentions pricing or quotes",
                "Tags": keyword,
                "Source": url
            })

    # WhatsApp detection (text or links)
    if re.search(r'whatsapp\.com', text, re.IGNORECASE):
        signals.append({
            "Category": "Social Media Activity",
            "Signal": "Chat Widgets",
            "Description": "WhatsApp contact option",
            "Tags": "whatsapp.com",
            "Source": url
        })

# Output structured data
with open("structured_signals.json", "w", encoding="utf-8") as f:
    json.dump(signals, f, indent=2, ensure_ascii=False)

print(f"✅ Extracted {len(signals)} signals.")
