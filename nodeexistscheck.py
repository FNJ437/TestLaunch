import os
import sys
import requests
import yaml

import argparse

# Create the parser
parser = argparse.ArgumentParser(description="Process user input.")

# Add arguments
parser.add_argument("--inv", type=str, help="inventory name")
parser.add_argument("--nodename", type=str, help="node alias name")

# Parse the arguments
args = parser.parse_args()

# Use the arguments
print(f"Hello, {args.inv}! You are {args.nodename} years old.")

if not args.nodename:
        sys.exit(0)
# === CONFIGURATION FROM ENVIRONMENT ===
AAP_URL = os.getenv("TOWER_HOST", "https://controller.example.org")
USERNAME = os.getenv("TOWER_USERNAME", "admin")
PASSWORD = os.getenv("TOWER_PASSWORD", "redhat")
VERIFY_SSL = os.getenv("TOWER_VERIFY_SSL", "true").lower() != "false"
#INVENTORY_NAME = "Testextrastat"
INVENTORY_NAME = args.inv
# === AUTHENTICATE AND GET TOKEN ===
auth_url = f"{AAP_URL}/api/v2/tokens/"
auth_response = requests.post(auth_url, auth=(USERNAME, PASSWORD), verify=VERIFY_SSL)
auth_response.raise_for_status()
token = auth_response.json()["token"]

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# === STEP 1: Lookup Inventory ID by Name ===
lookup_url = f"{AAP_URL}/api/v2/inventories/?name={INVENTORY_NAME}"
lookup_response = requests.get(lookup_url, headers=headers, verify=VERIFY_SSL)
lookup_response.raise_for_status()

results = lookup_response.json().get("results", [])
if not results:
    raise Exception(f"❌ Inventory '{INVENTORY_NAME}' not found.")

inventory_id = results[0]["id"]
inventory_url = f"{AAP_URL}/api/v2/inventories/{inventory_id}/"

print (inventory_url)

# === STEP 2: Get existing inventory variables ===
response = requests.get(inventory_url, headers=headers, verify=VERIFY_SSL)
response.raise_for_status()
inventory_data = response.json()

existing_vars = inventory_data.get("variables", "")
vars_dict = yaml.safe_load(existing_vars) if existing_vars else {}

# === STEP 3: Append 'task3' to stats array ===
stats = vars_dict.get("stats", [])
if not isinstance(stats, list):
    stats = []

print (stats)
nodename=args.nodename
if nodename not in stats:
    print (f"{nodename} not exists")
    sys.exit(0)
else:
    print (f"{nodename} exists")
    sys.exit(1)
