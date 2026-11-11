"""Print the day's totals from the TrainerGigs daily file.

Data: TrainerGigs, https://trainergigs.com
"""
import json
import urllib.request

URL = "https://trainergigs.com/ai-training-jobs-data.json"

req = urllib.request.Request(URL, headers={"User-Agent": "trainergigs-api-client/1.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)

totals = data["totals"]
print("Counted on", data["date"])
print(totals["open_roles"], "open roles on", totals["platforms_with_open_roles"], "platforms")
print("Median listed hourly pay (USD):", totals.get("median_listed_hourly_usd"))
