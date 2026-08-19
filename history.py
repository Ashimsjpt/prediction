import pandas as pd
import json
import requests

URL = "https://gatrout.com/api/recent?limit=1000"

response = requests.get(URL, timeout=30)
response.raise_for_status()

data = response.json()

with open("data/raw/gatrout_history.json", "w") as file:
    json.dump(data, file, indent=2)

df = pd.DataFrame(data)
df.to_csv ("data/raw/gatrout_history.csv", index=False)

print(f"downloaded {len(df)} records")
print (df.head())