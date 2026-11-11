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
        self.assertGreaterEqual(len(d["roles"]), 20)
        for r in d["roles"]:
            self.assertEqual(list(r), list(d["fields"]))
            self.assertTrue(r["url"].startswith("https://trainergigs.com/job-"))
        self.assertNotIn("bounty", json.dumps(d))

    def test_filters(self):
        d = load("ai-training-jobs-roles.json")
        everything = tg.roles(kind=None, data=d)
        self.assertEqual(len(everything), len(load("ai-training-jobs-roles.json")["roles"]))
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


class FilterTests(unittest.TestCase):
    """The filters and the command line, on the sample roles file: nothing is fetched."""

    def setUp(self):
        self.data = load("ai-training-jobs-roles.json")

    def test_every_role_has_an_id_a_tagged_page_and_countries(self):
        for r in self.data["roles"]:
            self.assertEqual(r["url"], "https://trainergigs.com/%s?src=api" % r["id"])
            self.assertIsInstance(r["countries"], list)

    def test_a_country_keeps_the_roles_that_name_it(self):
        found = tg.roles(country="ng", kind=None, data=self.data)
        self.assertTrue(found)
        self.assertTrue(all("NG" in r["countries"] for r in found))
        wider = tg.roles(country="NG", unnamed=True, kind=None, data=self.data)
        self.assertEqual(len(wider), len(found) + sum(not r["countries"] for r in self.data["roles"]))

    def test_since_keeps_the_dated_roles_from_that_day_on(self):
        days = sorted(r["posted"] for r in self.data["roles"] if r["posted"])
        day = days[len(days) // 2]
        found = tg.roles(since=day, kind=None, data=self.data)
        self.assertTrue(found)
        self.assertTrue(all(r["posted"] >= day for r in found))

    def test_an_older_file_without_the_new_fields_still_reads(self):
        old = {"roles": [{k: v for k, v in r.items() if k not in ("id", "countries")} for r in self.data["roles"]]}
        self.assertEqual(len(tg.roles(kind=None, data=old)), len(old["roles"]))
        self.assertEqual(tg.roles(country="NG", kind=None, data=old), [])

    def test_pay_as_words(self):
        self.assertEqual(tg.pay_text({"pay_min": 40, "pay_max": 60, "pay_unit": "hr"}), "$40 to $60/hr")
        self.assertEqual(tg.pay_text({"pay_min": 47.5, "pay_max": 47.5, "pay_unit": "hr", "paid_per_task": True}), "$47.5/hr, paid per task")
        self.assertEqual(tg.pay_text({"pay_min": None, "pay_max": None, "pay_unit": None}), "pay not listed")
        self.assertEqual(tg.pay_text({"pay_min": 130000, "pay_max": 180000, "pay_unit": "yr"}), "$130,000 to $180,000/yr")

    def test_the_command_line(self):
        said = []
        self.assertEqual(tg.main(["roles", "--country", "NG", "--limit", "2"], out=said.append, fetch=lambda: self.data), 0)
        self.assertIn("Counted on", said[0])
        self.assertEqual(len([l for l in said if l.startswith("- ")]), 2)
        self.assertTrue(all("?src=api" in l for l in said if l.startswith("- ")))
        self.assertEqual(said[-1], "Data: TrainerGigs, https://trainergigs.com")
        said.clear()
        tg.main(["roles", "--min-pay", "1", "--limit", "0", "--json"], out=said.append, fetch=lambda: self.data)
        got = json.loads(said[0])
        mids = [tg.hourly_midpoint(r) for r in got]
        self.assertEqual(mids, sorted(mids, reverse=True))  # best paid first
        said.clear()
        tg.main(["totals"], out=said.append, fetch=lambda: self.data)
        self.assertIn(str(self.data["totals"]["open_roles"]), said[0])


class DiscordRecipe(unittest.TestCase):
    def test_the_first_run_posts_nothing_and_a_role_is_posted_once(self):
        import argparse
        import sys
        import tempfile
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "examples"))
        import discord_new_roles as recipe
        data = load("ai-training-jobs-roles.json")
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(webhook="https://discord.example/hook", country=None, unnamed=False, field=None, min_pay=None,
                                      seen=str(pathlib.Path(tmp) / "seen.json"))
            sent = []
            send = lambda hook, text: sent.append(text)
            fewer = dict(data, roles=data["roles"][3:])
            self.assertEqual(recipe.run(args, fetch=lambda: fewer, send=send), 0)
            self.assertEqual(sent, [])  # the first run only notes what is open
            self.assertEqual(recipe.run(args, fetch=lambda: data, send=send), len([r for r in data["roles"][:3] if r["kind"] == "role"]))
            self.assertEqual(recipe.run(args, fetch=lambda: data, send=send), 0)
            self.assertLessEqual(len(sent), 1)
            for text in sent:
                self.assertLess(len(text), 2000)
                self.assertIn("?src=api", text)


if __name__ == "__main__":
    unittest.main()
