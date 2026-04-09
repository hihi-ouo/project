import requests
import json
import os


response = requests.get("https://raw.githubusercontent.com/gekichumai/dxrating/main/packages/dxdata/dxdata.json")
data = response.json()
print(data.keys())
print(data["songs"][0]) 

