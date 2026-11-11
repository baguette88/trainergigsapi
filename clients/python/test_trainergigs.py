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
        import csv
        with (SAMPLES / "ai-training-jobs-data.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), len(load("ai-training-jobs-data.json")["rows"]))

    def test_board_rows_become_dicts(self):
        b = load("board.json")
        found = tg.role_dicts(b)
        self.assertEqual(len(found), 20)
        self.assertTrue(all(r["url"].startswith("https://trainergigs.com/job-") for r in found))

    def test_filters(self):
        b = load("board.json")
        allr = tg.roles(data=b)
        self.assertEqual(len(allr), 20)
        prov = allr[0]["provider"]
        self.assertTrue(all(r["provider"] == prov for r in tg.roles(platform=prov.upper(), data=b)))
        paid = tg.roles(min_pay=1, data=b)
        self.assertTrue(paid)
        self.assertTrue(all(tg.hourly_midpoint(r) >= 1 for r in paid))
        self.assertEqual(tg.roles(min_pay=100000, data=b), [])
        cat = allr[0]["cat"]
        self.assertTrue(all(r["cat"] == cat for r in tg.roles(field=cat, data=b)))


if __name__ == "__main__":
    unittest.main()
