import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

APP_ID  = os.environ.get("ADZUNA_APP_ID")
APP_KEY = os.environ.get("ADZUNA_APP_KEY")

url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

params = {
    "app_id":           APP_ID,
    "app_key":          APP_KEY,
    "results_per_page": 1,
    "what":             "python developer",
    "content-type":     "application/json"
}

response = requests.get(url, params=params)
data     = response.json()

# Print full structure of first job
job = data["results"][0]
print(json.dumps(dict(job), indent=2))