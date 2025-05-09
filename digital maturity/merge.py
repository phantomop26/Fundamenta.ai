# import json
# import re
# import pandas as pd

# # --- 1. Load results.json ---
# with open('results.json', 'r', encoding='utf-8') as f:
#     results = json.load(f)

# # --- 2. Load scraped_data.json ---
# with open('scraped_data.json', 'r', encoding='utf-8') as f:
#     scraped = json.load(f)
# scraped_map = {e.get('url','').strip(): e for e in scraped}

# # --- 3. Regexes & helpers ---
# email_re = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
# phone_re = re.compile(
#     r'(?:\+?\d{1,3}[ .\-]?)?'        # country code
#     r'(?:\(?\d{2,3}\)?[ .\-]?)?'     # area code
#     r'\d{2,4}'                       # first block
#     r'(?:[ .\-]?\d{2,4}){1,3}'       # more blocks
# )

# def normalize_phone(raw: str) -> str | None:
#     digits = re.sub(r'\D', '', raw)
#     if len(digits) == 10:
#         return digits
#     if len(digits) == 12 and digits.startswith('52'):
#         return digits[2:]
#     if len(digits) == 12 and digits.startswith('01'):
#         return digits[2:]
#     if len(digits) == 13 and digits.startswith(('044','045')):
#         return digits[3:]
#     return None

# def is_valid_mex_phone(num: str) -> bool:
#     # exactly 10 digits, not starting with 0,1,9
#     return len(num) == 10 and num[0] not in ('0','1','9')

# # — Add any known bad numbers here:
# blacklist = {'2850574025', '4433108192'}

# # Social regexes (unchanged)…
# fb_re = re.compile(
#     r'^https?://(?:www\.|m\.)?(?:facebook\.com|fb\.com)/'
#     r'(?:(?:pages/[A-Za-z0-9\.-]+/\d+)|(?:profile\.php\?id=\d+)|[A-Za-z0-9\.]+)'
#     r'/?(?:\?.*)?$', re.IGNORECASE
# )
# ig_re = re.compile(
#     r'^https?://(?:www\.)?(?:instagram\.com|instagr\.am)/'
#     r'(?:(?:p/[A-Za-z0-9_-]+)|[A-Za-z0-9._]+)'  
#     r'/?$', re.IGNORECASE
# )
# tt_re = re.compile(r'^https?://(?:www\.)?tiktok\.com/@?[A-Za-z0-9._-]+/?$', re.IGNORECASE)
# li_re = re.compile(r'^https?://(?:www\.)?linkedin\.com/(?:in|company)/[A-Za-z0-9_-]+/?$', re.IGNORECASE)


# # --- 4. Build merged rows ---
# rows = []
# for rec in results:
#     url = rec.get('url','').strip()
#     success = rec.get('success',False)
#     error   = rec.get('error','') if not success else ''

#     text  = scraped_map.get(url,{}).get('text','')
#     links = rec.get('links',[])

#     combined = " ".join([text, *links])

#     # emails
#     emails = set(email_re.findall(combined))

#     # raw phones → normalize → mx‑valid → not blacklisted
#     raw_phones = [m.group() for m in phone_re.finditer(combined)]
#     phones = {
#         norm
#         for raw in raw_phones
#         if (norm := normalize_phone(raw))
#            and is_valid_mex_phone(norm)
#            and norm not in blacklist
#     }

#     # whatsapp & socials (same as before)…
#     wapps      = {l for l in links if 'wa.me' in l.lower() or 'whatsapp' in l.lower()}
#     ig_links   = {l for l in links if ig_re.match(l)}
#     fb_links   = {l for l in links if fb_re.match(l)}
#     tt_links   = {l for l in links if tt_re.match(l)}
#     li_links   = {l for l in links if li_re.match(l)}

#     rows.append({
#         'url': url,
#         'Error': error,
#         'Morada': ', '.join(rec.get('addresses',[])),
#         'Emails': ';'.join(sorted(emails)),
#         'Phones': ';'.join(sorted(phones)),
#         'Whatsapps': ';'.join(sorted(wapps)),
#         'Links IG': ';'.join(sorted(ig_links)),
#         'Links Facebook': ';'.join(sorted(fb_links)),
#         'Links TikTok': ';'.join(sorted(tt_links)),
#         'Links Linkedin': ';'.join(sorted(li_links)),
#     })

# # --- 5. Save CSV ---
# df = pd.DataFrame(rows, columns=[
#     'url','Error','Morada','Emails','Phones','Whatsapps',
#     'Links IG','Links Facebook','Links TikTok','Links Linkedin'
# ])
# df.to_csv('batch.csv', index=False)
# print("Saved merged output to batch.csv")












import json
import re
import pandas as pd

# --- 1. Load results.json (everything’s in here now) ---
with open('results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# --- 2. Regex helpers for phone normalization/filtering ---
phone_re = re.compile(
    r'(?:\+?\d{1,3}[ .\-]?)?'        # optional country code
    r'(?:\(?\d{2,3}\)?[ .\-]?)?'     # optional area code
    r'\d{2,4}'                       # first block
    r'(?:[ .\-]?\d{2,4}){1,3}'       # 1–3 additional blocks
)

def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 10:
        return digits
    if len(digits) == 12 and digits.startswith('52'):
        return digits[2:]
    if len(digits) == 12 and digits.startswith('01'):
        return digits[2:]
    if len(digits) == 13 and digits.startswith(('044','045')):
        return digits[3:]
    return None

def is_valid_mex_phone(num: str) -> bool:
    # exactly 10 digits, not starting with 0,1,9
    return len(num) == 10 and num[0] not in ('0','1','9')

# any specific bad numbers you want to drop
blacklist = {'2850574025', '4433108192'}

# --- 3. Build rows for DataFrame ---
rows = []
for rec in results:
    url     = rec.get('url', '').strip()
    success = rec.get('success', False)
    error   = '' if success else rec.get('error', '')

    # Addresses (Morada)
    morada = ', '.join(rec.get('addresses', []))

    # Emails: from rec['emails'] + any mailto: links
    emails = set(rec.get('emails', []))
    for link in rec.get('links', []):
        if link.lower().startswith('mailto:'):
            emails.add(link.split(':', 1)[1])

    # Phones: from rec['phones'] + any tel: links
    raw_phones = list(rec.get('phones', []))
    for link in rec.get('links', []):
        if link.lower().startswith('tel:'):
            raw_phones.append(link.split(':', 1)[1])

    # normalize, MX‑filter, blacklist
    phones = {
        norm
        for raw in raw_phones
        if (norm := normalize_phone(raw))
           and is_valid_mex_phone(norm)
           and norm not in blacklist
    }

    # WhatsApp links
    wapps = {
        link for link in rec.get('links', [])
        if 'wa.me' in link.lower() or 'whatsapp' in link.lower()
    }

    # Social links come straight from rec['social']
    social = rec.get('social', {})
    fb_links = set(social.get('facebook', []))
    ig_links = set(social.get('instagram', []))
    tt_links = set(social.get('tiktok', []))
    li_links = set(social.get('linkedin', []))

    rows.append({
        'url': url,
        'Error': error,
        'Morada': morada,
        'Emails': ';'.join(sorted(emails)),
        'Phones': ';'.join(sorted(phones)),
        'Whatsapps': ';'.join(sorted(wapps)),
        'Links IG': ';'.join(sorted(ig_links)),
        'Links Facebook': ';'.join(sorted(fb_links)),
        'Links TikTok': ';'.join(sorted(tt_links)),
        'Links Linkedin': ';'.join(sorted(li_links)),
    })

# --- 4. Save to CSV ---
df = pd.DataFrame(rows, columns=[
    'url','Error','Morada','Emails','Phones','Whatsapps',
    'Links IG','Links Facebook','Links TikTok','Links Linkedin'
])
df.to_csv('bat.csv', index=False)
print("Saved merged output to batch.csv")


