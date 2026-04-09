import requests
import json
import os

if os.path.exists("dxdata.json"):
    data = open("dxdata.json", "r", encoding="utf-8")
    dx_data = json.load(data)
else:
    response = requests.get("https://raw.githubusercontent.com/gekichumai/dxrating/main/packages/dxdata/dxdata.json")
    dx_data = response.json()
    data = open("dxdata.json", "w", encoding="utf-8")
    json.dump(dx_data, data, ensure_ascii=False, indent=2)

print(f"共 {len(dx_data['songs'])} 首歌")