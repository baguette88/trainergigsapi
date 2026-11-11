import csv
import json
import pathlib
import unittest

import trainergigs as tg

SAMPLES = pathlib.Path(__file__).resolve().parents[2] / "tests" / "samples"


def load(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


class SampleTests(unittest.TestCase):
    def test_daily_shape(self):
        d = load("ai-training-jobs-data.json")
        self.assertEqual(d["fields"], list(d["rows"][0].keys()))
        roles = sum(r["open_roles"] for r in d["rows"] if r["kind"] == "role")
        self.assertEqual(roles, d["totals"]["open_roles"])

    def test_weekly_shape(self):
        w = load("ai-training-jobs-weekly.json")
        self.assertTrue(w["weeks"])
        self.assertTrue(w["weeks"][0]["url"].startswith("https://trainergigs.com/"))

    def test_csv_matches_json(self):
        with (SAMPLES / "ai-training-jobs-data.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), len(load("ai-training-jobs-data.json")["rows"]))

    def test_roles_file_shape(self):
        d = load("ai-training-jobs-roles.json")
        self.assertEqual(len(d["roles"]), 20)
        for r in d["roles"]:
            self.assertEqual(list(r), list(d["fields"]))
            self.assertTrue(r["url"].startswith("https://trainergigs.com/job-"))
        self.assertNotIn("bounty", json.dumps(d))

    def test_filters(self):
        d = load("ai-training-jobs-roles.json")
        everything = tg.roles(kind=None, data=d)
        self.assertEqual(len(everything), 20)
        self.assertTrue(all(r["kind"] == "role" for r in tg.roles(data=d)))
        self.assertTrue(any(r["kind"] == "study" for r in everything))
        prov = d["roles"][0]["platform"]
        self.assertTrue(all(r["platform"] == prov for r in tg.roles(platform=prov.upper(), data=d)))
        paid = tg.roles(min_pay=1, data=d)
        self.assertTrue(paid)
        self.assertTrue(all(tg.hourly_midpoint(r) >= 1 for r in paid))
        self.assertEqual(tg.roles(min_pay=100000, data=d), [])
        field = d["roles"][0]["field"]
        self.assertTrue(all(r["field"] == field for r in tg.roles(field=field.lower(), kind=None, data=d)))


if __name__ == "__main__":
    unittest.main()
