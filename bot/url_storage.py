import json
import os

URL_STORAGE = "url_storage.json"

def load_url_storage():
    if os.path.exists(URL_STORAGE):
        with open(URL_STORAGE, "r") as file:
            return json.load(file)
    return {}

def save_url_storage(data):
    with open(URL_STORAGE, "w") as file:
        json.dump(data, file, indent=4)
        
url_storage = load_url_storage()