"""Open roles by field, and the median listed hourly pay of each, with pandas.

    pip install pandas
    python3 examples/pandas_example.py

Data: TrainerGigs, https://trainergigs.com
"""
import pandas as pd

# Name your program here. pandas reads through urllib, and the site refuses urllib's default User-Agent with a 403.
WHO = {"User-Agent": "my-project/1.0"}

rows = pd.read_csv("https://trainergigs.com/ai-training-jobs-data.csv", storage_options=WHO)
roles = rows[rows["kind"] == "role"]
print(roles.groupby("platform")["open_roles"].sum().sort_values(ascending=False).head(10))

file = pd.read_json("https://trainergigs.com/ai-training-jobs-roles.json", typ="series", storage_options=WHO)
one_by_one = pd.DataFrame(file["roles"])
hourly = one_by_one[(one_by_one["kind"] == "role") & (one_by_one["pay_unit"] == "hr") & ~one_by_one["paid_per_task"]].dropna(subset=["pay_min", "pay_max"])
hourly = hourly.assign(midpoint=(hourly["pay_min"] + hourly["pay_max"]) / 2)
by_field = hourly.groupby("field")["midpoint"].agg(["count", "median"])
print(by_field[by_field["count"] >= 8].sort_values("median", ascending=False))
print("Counted on", file["counted"])
print("Data: TrainerGigs, https://trainergigs.com")
