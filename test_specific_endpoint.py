#!/usr/bin/env python3

import requests
import json

BASE_URL = "https://22ab362b-ef92-48cd-892f-fb174db57b96.preview.emergentagent.com/api"

# Login first
login_data = {
    "email": "admin@company.com",
    "password": "Admin123!"
}

print("Logging in...")
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if response.status_code != 200:
    print(f"Login failed: {response.status_code} - {response.text}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Testing pending approval endpoint...")
response = requests.get(f"{BASE_URL}/admin/time-entries/pending-approval", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Also test just the list endpoint
print("\nTesting list endpoint...")
response = requests.get(f"{BASE_URL}/admin/time-entries/list", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")