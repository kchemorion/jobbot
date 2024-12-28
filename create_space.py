import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Get the token from .env
token = os.getenv('DO_ACCESS_TOKEN')

if not token:
    print("Error: DO_ACCESS_TOKEN must be set in .env")
    exit(1)

# API endpoint for creating a Space
url = 'https://api.digitalocean.com/v2/spaces'

# Headers with authentication
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Space configuration
data = {
    'name': 'jobbot-storage',
    'region': 'fra1'
}

try:
    # Create the Space
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print("Space created successfully!")
        print(response.json())
    else:
        print(f"Error creating space: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")
