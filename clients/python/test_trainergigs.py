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
        self.assertEqual(tg.pay_text({"pay_min": 47.5, "pay_max": 47.5, "pay_unit": "hr", "paid_per_task": True}), "$47.50/hr, paid per task")
        self.assertEqual(tg.pay_text({"pay_min": None, "pay_max": None, "pay_unit": None}), "pay not listed")
        self.assertEqual(tg.pay_text({"pay_min": 130000, "pay_max": 180000, "pay_unit": "yr"}), "$130,000 to $180,000/yr")
        self.assertEqual(tg.pay_text({"pay_min": 0.01, "pay_max": 0.01, "pay_unit": "task"}), "$0.01/task")

    def test_a_listing_with_one_end_keeps_its_own_words(self):
        top = {"pay_min": None, "pay_max": 90, "pay_unit": "hr"}
        self.assertEqual(tg.pay_text(top), "Up to $90/hr")  # never "$90/hr": the listing states no lower end
        self.assertEqual(tg.pay_text({"pay_min": 25, "pay_max": None, "pay_unit": "hr"}), "From $25/hr")
        self.assertEqual(tg.hourly_midpoint(top), 90)
        self.assertEqual(tg.pay_stats([top] * 8)["roles"], 0)  # the site's medians leave such a listing out

    def test_best_paid_first_and_the_rest_in_their_order(self):
        a, b, c, d = ({"id": "a", "pay_unit": None}, {"id": "b", "pay_unit": "hr", "pay_min": 20, "pay_max": 30},
                      {"id": "c", "pay_unit": "hr", "pay_min": 60, "pay_max": 60}, {"id": "d", "pay_unit": "task", "pay_min": 500, "pay_max": 500})
        self.assertEqual([r["id"] for r in tg.by_pay([a, b, c, d])], ["c", "b", "a", "d"])

    def test_counts_under_each_name(self):
        everything = tg.roles(kind=None, data=self.data)
        fields = tg.tally(everything, "field")
        self.assertEqual(sum(n for _, n in fields), len(everything))
        self.assertEqual([n for _, n in fields], sorted((n for _, n in fields), reverse=True))
        countries = dict(tg.tally(everything, "countries"))
        self.assertEqual(countries["NG"], len(tg.roles(country="NG", kind=None, data=self.data)))
        self.assertEqual(dict(tg.tally(everything, "kind")), {"role": len(tg.roles(data=self.data)), "study": len(tg.roles(kind="study", data=self.data))})

    def test_the_median_is_counted_as_the_site_counts_it(self):
        hourly = lambda low, high, **more: dict({"pay_unit": "hr", "pay_min": low, "pay_max": high}, **more)
        eight = [hourly(x, x) for x in (10, 20, 30, 40, 50, 60, 70, 80)]
        self.assertEqual(tg.pay_stats(eight), {"roles": 8, "q1": 27.5, "median": 45.0, "q3": 62.5})
        self.assertEqual(tg.pay_stats(eight[:7]), {"roles": 7, "q1": None, "median": None, "q3": None})
        left_out = [hourly(900, 900, paid_per_task=True), hourly(None, 900), {"pay_unit": "yr", "pay_min": 9e4, "pay_max": 9e4}, {"pay_unit": None}]
        self.assertEqual(tg.pay_stats(eight + left_out), tg.pay_stats(eight))
        self.assertEqual(tg.pay_stats([hourly(40, 60)] * 8)["median"], 50)  # a range at its midpoint

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
        self.assertIn("{:,} open roles on".format(self.data["totals"]["open_roles"]), said[0])
        self.assertIn("Counted on " + self.data["counted"], said[0])
        said.clear()
        tg.main(["totals", "--json"], out=said.append, fetch=lambda: self.data)
        self.assertEqual(json.loads(said[0]), self.data["totals"])

    def test_the_commands_that_count(self):
        said = []
        self.assertEqual(tg.main(["fields"], out=said.append, fetch=lambda: self.data), 0)
        self.assertIn("Counted on", said[0])
        self.assertEqual(said[-1], "Data: TrainerGigs, https://trainergigs.com")
        names = [l.split(None, 1)[1] for l in said[1:-1]]
        self.assertEqual(sorted(names), sorted({r["field"] for r in self.data["roles"] if r["kind"] == "role"}))
        for what, key in (("platforms", "platform"), ("countries", "countries"), ("fields", "field")):
            said.clear()
            tg.main([what, "--country", "NG", "--json"], out=said.append, fetch=lambda: self.data)
            self.assertEqual(json.loads(said[0]), dict(tg.tally(tg.roles(country="NG", data=self.data), key)))
        said.clear()
        tg.main(["pay", "--json"], out=said.append, fetch=lambda: self.data)
        got = json.loads(said[0])
        self.assertEqual(got["roles"], tg.pay_stats(tg.roles(data=self.data))["roles"])
        self.assertEqual(got["counted"], self.data["counted"])
        said.clear()
        tg.main(["pay", "--min-pay", "100000"], out=said.append, fetch=lambda: self.data)
        self.assertIn("No median", said[1])

    def run_line(self, *argv):
        """(exit code, lines printed, text on stderr) of one command on the sample."""
        import contextlib
        import io
        said, err, fetched = [], io.StringIO(), []

        def fetch():
            fetched.append(1)
            return self.data
        with contextlib.redirect_stderr(err):
            code = tg.main(list(argv), out=said.append, fetch=fetch)
        return code, said, err.getvalue(), len(fetched)

    def test_a_filter_that_could_never_match_is_said_and_not_answered_with_nothing(self):
        code, said, err, fetched = self.run_line("roles", "--country", "Nigeria")
        self.assertEqual((code, said, fetched), (2, [], 0))  # said before anything is fetched
        self.assertIn('two-letter code such as "NG"', err)
        self.assertIn('not "Nigeria"', err)
        code, said, err, fetched = self.run_line("roles", "--since", "yesterday")
        self.assertEqual((code, said, fetched), (2, [], 0))
        self.assertIn('"2026-11-01"', err)
        self.assertEqual(self.run_line("roles", "--limit", "-1")[0], 2)
        with self.assertRaises(ValueError):
            tg.roles(country="Nigeria", data=self.data)
        with self.assertRaises(ValueError):
            tg.roles(since="11/01/2026", data=self.data)
        self.assertEqual(tg.roles(country=" ng ", data=self.data), tg.roles(country="NG", data=self.data))

    def test_a_field_or_platform_the_file_does_not_have_gets_the_names_it_does_have(self):
        fields = sorted({r["field"] for r in self.data["roles"] if r["kind"] == "role"})
        one = fields[0]
        code, said, err, _ = self.run_line("roles", "--field", one[:-1] + "x")
        self.assertEqual((code, said), (2, []))
        self.assertIn("No field is named", err)
        self.assertIn("Close to it: " + one, err)
        for name in fields:
            self.assertIn(name, err)
        code, said, err, _ = self.run_line("pay", "--platform", "nobody at all")
        self.assertEqual((code, said), (2, []))
        self.assertIn('Run "trainergigs platforms"', err)
        self.assertEqual(self.run_line("roles", "--field", one.upper())[0], 0)  # case does not matter
        code, said, err, _ = self.run_line("roles", "--field", one, "--min-pay", "100000")
        self.assertEqual((code, err), (0, ""))  # a real name with no role today is an honest nothing
        self.assertIn("0 found", said[0])
        code, said, err, _ = self.run_line("roles", "--studies", "--field", one, "--platform", self.data["roles"][0]["platform"])
        self.assertEqual((code, err), (0, ""))  # a name is known when any row has it, role or study

    def test_roles_and_counts_as_csv(self):
        code, said, err, _ = self.run_line("roles", "--limit", "0", "--csv")
        self.assertEqual((code, err), (0, ""))
        rows = list(csv.DictReader(said[0].splitlines()))
        found = tg.by_pay(tg.roles(data=self.data))
        self.assertEqual(tuple(rows[0]), tg.CSV_COLUMNS)
        self.assertEqual([r["url"] for r in rows], [r["url"] for r in found])
        self.assertEqual([r["pay"] for r in rows], [tg.pay_text(r) for r in found])
        self.assertEqual([r["countries"].split() for r in rows], [r["countries"] for r in found])
        self.assertNotIn("None", said[0])
        code, said, _, _ = self.run_line("fields", "--csv")
        counts = list(csv.reader(said[0].splitlines()))
        self.assertEqual(counts[0], ["name", "roles"])
        self.assertEqual([(n, int(c)) for n, c in counts[1:]], tg.tally(tg.roles(data=self.data), "field"))
        self.assertEqual(self.run_line("totals", "--csv")[0], 2)
        self.assertEqual(self.run_line("roles", "--csv", "--json")[0], 2)

    def test_roles_and_counts_as_a_markdown_table(self):
        code, said, err, _ = self.run_line("roles", "--limit", "0", "--md")
        self.assertEqual((code, err), (0, ""))
        lines = said[0].splitlines()
        found = tg.by_pay(tg.roles(data=self.data))
        self.assertEqual(lines[:2], ["| Pay | Role | Platform | Field | Posted |", "|---|---|---|---|---|"])
        self.assertEqual(len(lines), len(found) + 4)
        for row, role in zip(lines[2:], found):
            self.assertIn("](%s) |" % role["url"], row)
            self.assertEqual(row.replace("\\|", "").count("|"), 6, row)
        self.assertEqual(lines[-2:], ["", "Counted on %s. Data: [TrainerGigs](https://trainergigs.com/?src=api)" % self.data["counted"]])
        code, said, _, _ = self.run_line("fields", "--md")
        self.assertEqual(said[0].splitlines()[:2], ["| Field | Roles |", "|---|---|"])
        self.assertEqual(said[0].count("\n| "), len(tg.tally(tg.roles(data=self.data), "field")))
        self.assertEqual(self.run_line("countries", "--md")[1][0].splitlines()[0], "| Country | Roles |")
        self.assertEqual(self.run_line("totals", "--md")[0], 2)
        self.assertEqual(self.run_line("roles", "--md", "--csv")[0], 2)

    def test_a_markdown_table_keeps_a_title_as_plain_text_and_says_when_it_is_empty(self):
        role = dict(self.data["roles"][0], title="Law | Reviewer [US] <b>*now*</b>\nline two", pay_min=40, pay_max=60, pay_unit="hr", paid_per_task=False)
        row = tg.roles_markdown([role]).splitlines()[2]
        self.assertIn("[Law \\| Reviewer \\[US\\] \\<b\\>\\*now\\*\\</b\\> line two](%s)" % role["url"], row)
        self.assertTrue(row.startswith("| \\$40 to \\$60/hr | "), row)  # two dollar signs on one line are not read as a formula
        self.assertEqual(tg.roles_markdown([]), "No open roles matched.\n\nData: [TrainerGigs](https://trainergigs.com/?src=api)\n")

    def test_a_title_that_begins_like_a_formula_stays_text_in_a_spreadsheet(self):
        role = dict(self.data["roles"][0], title='=HYPERLINK("https://example.com")', platform="+1 Labs")
        row = next(csv.DictReader(tg.roles_csv([role]).splitlines()))
        self.assertEqual(row["title"], "'" + role["title"])
        self.assertEqual(row["platform"], "'+1 Labs")
        self.assertEqual(row["url"], role["url"])

    def test_a_failed_read_ends_with_one_line_and_no_traceback(self):
        import contextlib
        import io
        import urllib.error

        def down():
            raise urllib.error.URLError("no route")
        said, err = [], io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(tg.main(["roles"], out=said.append, fetch=down), 1)
        self.assertEqual(said, [])
        self.assertIn("Could not read https://trainergigs.com/ai-training-jobs-roles.json", err.getvalue())


class Fetching(unittest.TestCase):
    """How a file is asked for, with the network replaced: nothing is fetched."""

    def read(self, body, encoding=None):
        import urllib.request
        asked = []

        class Answer:
            headers = {"Content-Encoding": encoding} if encoding else {}

            def read(self):
                return body

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def urlopen(req, timeout=None):
            asked.append(req)
            return Answer()
        real, urllib.request.urlopen = urllib.request.urlopen, urlopen
        try:
            return tg._get("/x.json"), asked[0]
        finally:
            urllib.request.urlopen = real

    def test_it_names_itself_and_asks_for_gzip(self):
        text, req = self.read(b'{"a": 1}')
        self.assertEqual(text, '{"a": 1}')
        self.assertEqual(req.full_url, "https://trainergigs.com/x.json")
        self.assertEqual(req.get_header("User-agent"), "trainergigs-api-client/" + tg.__version__)
        self.assertEqual(req.get_header("Accept-encoding"), "gzip")

    def test_a_gzipped_answer_is_opened(self):
        import gzip
        text, _ = self.read(gzip.compress("é".encode("utf-8")), encoding="gzip")
        self.assertEqual(text, "é")


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
