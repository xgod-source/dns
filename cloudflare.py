import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLOUDFLARE_TOKEN = os.getenv("CLOUDFLARE_TOKEN")
ZONE_ID = os.getenv("ZONE_ID")
DOMAIN = os.getenv("DOMAIN")

headers = {
    "Authorization": f"Bearer {CLOUDFLARE_TOKEN}",
    "Content-Type": "application/json"
}

def update_dns(subdomain, ip):
    record_name = f"{subdomain}.{DOMAIN}"
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    
    # Checking are A record exist
    response = requests.get(url, headers=headers, params={"type": "A", "name": record_name})
    data = response.json()

    if not data["success"]:
        return False, "Fail to access Cloudflare"

    records = data["result"]
    
    if records:
        # If record exist → update
        record_id = records[0]["id"]
        update_url = f"{url}/{record_id}"
        payload = {
            "type": "A",
            "name": record_name,
            "content": ip,
            "ttl": 120,
            "proxied": False
        }
        r = requests.put(update_url, headers=headers, json=payload)
    else:
        # If not exist → create new
        payload = {
            "type": "A",
            "name": record_name,
            "content": ip,
            "ttl": 120,
            "proxied": False
        }
        r = requests.post(url, headers=headers, json=payload)

    result = r.json()
    if result["success"]:
        return True, f"Update Success {record_name} → {ip}"
    else:
        return False, f"Update Fail: {result.get('errors', [])}"
