"""The documents against the files they describe. Nothing is fetched.

    python3 -m unittest discover -s tests

A field the samples hold must be named in README.md and in openapi.yaml, the version must read the same in every
file that states it, and every file the README names must be in the repository.
"""
import copy
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "tests" / "samples"
sys.path.insert(0, str(ROOT / "clients" / "python"))
sys.path.insert(0, str(ROOT / "tools"))
import check_live  # noqa: E402
import readme_counts  # noqa: E402
import trainergigs as tg  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")
OPENAPI = (ROOT / "openapi.yaml").read_text(encoding="utf-8")


def sample(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def columns(name):
    with (SAMPLES / name).open(encoding="utf-8") as fh:
        return fh.readline().strip().split(",")


class Fields(unittest.TestCase):
    def named(self, keys, what):
        for key in keys:
            self.assertIn("`%s`" % key, README, "README.md does not name the %s field %s" % (what, key))

    def described(self, keys, what):
        for key in keys:
            self.assertRegex(OPENAPI, r"(?m)^\s+%s:\s*$" % re.escape(key), "openapi.yaml does not describe the %s field %s" % (what, key))

    def test_the_daily_file(self):
        d = sample("ai-training-jobs-data.json")
        for keys, what in ((list(d), "daily file"), (list(d["totals"]), "daily totals"), (list(d["rows"][0]), "daily row")):
            self.named(keys, what)
            self.described(keys, what)
        self.assertEqual(columns("ai-training-jobs-data.csv"), list(d["rows"][0]))

    def test_the_weekly_file(self):
        w = sample("ai-training-jobs-weekly.json")
        for keys, what in ((list(w), "weekly file"), (list(w["weeks"][0]), "week")):
            self.named(keys, what)
            self.described(keys, what)
        self.named(columns("ai-training-jobs-weekly.csv"), "weekly CSV")

    def test_the_roles_file(self):
        r = sample("ai-training-jobs-roles.json")
        for keys, what in ((list(r), "roles file"), (list(r["roles"][0]), "role")):
            self.named(keys, what)
            self.described(keys, what)

    def test_every_field_name_the_readme_lists_for_a_filter_is_in_the_samples_or_stated_live(self):
        fields = re.search(r"<!-- fields:start -->(.*?)<!-- fields:end -->", README, re.S)
        self.assertTrue(fields, "README.md has no list of field names")
        listed = set(re.findall(r"`([^`]+)`", fields.group(1)))
        self.assertTrue({r["field"] for r in sample("ai-training-jobs-roles.json")["roles"]} <= listed)


class Versions(unittest.TestCase):
    def test_one_version_everywhere(self):
        said = {
            "clients/python/trainergigs.py": tg.__version__,
            "clients/js/trainergigs.mjs": re.search(r'export const VERSION = "([^"]+)"', (ROOT / "clients/js/trainergigs.mjs").read_text()).group(1),
            "openapi.yaml": re.search(r'(?m)^  version: "([^"]+)"', OPENAPI).group(1),
            "package.json": json.loads((ROOT / "package.json").read_text())["version"],
            "pyproject.toml": re.search(r'(?m)^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text()).group(1),
            "CITATION.cff": re.search(r'(?m)^version: "([^"]+)"', (ROOT / "CITATION.cff").read_text()).group(1),
            "CHANGELOG.md": re.search(r"(?m)^## (\d+\.\d+\.\d+),", (ROOT / "CHANGELOG.md").read_text()).group(1),
        }
        self.assertEqual(len(set(said.values())), 1, said)
        self.assertEqual(tg.USER_AGENT, "trainergigs-api-client/" + tg.__version__)
        self.assertIn("@v%s/" % tg.__version__, README, "the README's CDN address does not carry the version")


class Readme(unittest.TestCase):
    def test_every_file_it_names_is_here(self):
        paths = set(re.findall(r"`((?:clients|examples|tests|tools|\.github)/[^`\s*<>]+|[A-Z][A-Z-]+\.(?:md|cff)|LICENSE|openapi\.yaml|pyproject\.toml|package\.json)`", README))
        self.assertGreater(len(paths), 10)
        for path in sorted(paths):
            self.assertTrue((ROOT / path).exists(), "README.md names %s, which is not in the repository" % path)

    def test_every_page_link_inside_it_lands(self):
        heads = {re.sub(r"[^a-z0-9 -]", "", h.lower()).replace(" ", "-") for h in re.findall(r"(?m)^#{1,4} (.+)$", README)}
        for anchor in re.findall(r"\]\(#([^)]+)\)", README):
            self.assertIn(anchor, heads, "README.md links to #%s, and no heading makes it" % anchor)

    def test_the_counts_are_written_between_the_marks(self):
        daily = sample("ai-training-jobs-data.json")
        once = readme_counts.rewrite(README, daily)
        self.assertEqual(readme_counts.rewrite(once, daily), once)
        self.assertIn("On Nov 11, 2026 the daily file stated **3,102 open roles on 33 platforms**, and 439 paid research studies", once)
        self.assertIn("The median listed pay was $39 an hour, across 2,120 roles that state hourly pay. The middle half list $35 to $75.", once)
        head, _, rest = README.partition(readme_counts.START)
        tail = rest.partition(readme_counts.END)[2]
        new_head, _, new_rest = once.partition(readme_counts.START)
        self.assertEqual((new_head, new_rest.partition(readme_counts.END)[2]), (head, tail))  # nothing outside the marks moves
        self.assertEqual(readme_counts.rewrite("no marks here", daily), "no marks here")


class Recipes(unittest.TestCase):
    """The recipes a reader copies: the Python under "What you can build" and the workflow in examples/."""

    def test_each_python_recipe_in_the_readme_runs_on_the_saved_roles(self):
        import contextlib
        import io
        part = README.partition("## What you can build")[2].partition("\n## ")[0]
        blocks = re.findall(r"```python\n(.*?)```", part, re.S)
        self.assertEqual(len(blocks), 2)
        live, tg.roles_file = tg.roles_file, lambda base=None: sample("ai-training-jobs-roles.json")
        try:
            for block in blocks:
                said = io.StringIO()
                with contextlib.redirect_stdout(said):
                    exec(compile(block, "README.md", "exec"), {"__name__": "recipe"})
                self.assertIn("2026-11-1", said.getvalue())  # each prints the day the roles were counted
        finally:
            tg.roles_file = live

    def test_the_workflow_to_copy_pins_this_version_and_asks_for_no_secret(self):
        text = (ROOT / "examples" / "daily-roles.yml").read_text(encoding="utf-8")
        self.assertIn('trainergigsapi@v%s"' % tg.__version__, text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("\t", text)
        self.assertRegex(text, r"(?m)^permissions:\n  contents: write$")
        for name in ("COUNTRY", "FIELD", "MIN_PAY"):
            self.assertRegex(text, r'(?m)^  %s: "' % name)

    def test_the_workflow_step_writes_both_files_with_a_field_of_two_words(self):
        import os
        import shutil
        import subprocess
        import tempfile
        if not shutil.which("bash"):
            self.skipTest("no bash here")
        text = (ROOT / "examples" / "daily-roles.yml").read_text(encoding="utf-8")
        step = re.search(r"- name: Write roles\.md and roles\.csv\n        run: \|\n(.*?)\n\n", text, re.S).group(1)
        script = "\n".join(line[10:] for line in step.splitlines())
        found = tg.roles(field="Language & Audio", min_pay=20, data=sample("ai-training-jobs-roles.json"))
        self.assertTrue(found)
        with tempfile.TemporaryDirectory() as tmp:
            # the command, reading the saved roles in place of the live file
            runner = pathlib.Path(tmp) / "bin" / "run.py"
            runner.parent.mkdir()
            runner.write_text(
                "import json, sys\n"
                "sys.path.insert(0, %r)\n"
                "import trainergigs as tg\n"
                "sys.exit(tg.main(sys.argv[1:], fetch=lambda: json.load(open(%r, encoding='utf-8'))))\n"
                % (str(ROOT / "clients" / "python"), str(SAMPLES / "ai-training-jobs-roles.json")), encoding="utf-8")
            stand_in = runner.with_name("trainergigs")
            stand_in.write_text('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, runner), encoding="utf-8")
            stand_in.chmod(0o755)
            env = dict(os.environ, PATH=str(stand_in.parent) + os.pathsep + os.environ["PATH"], COUNTRY="", FIELD="Language & Audio", MIN_PAY="20")
            done = subprocess.run(["bash", "-c", script], cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual((done.returncode, done.stderr), (0, ""))
            table = (pathlib.Path(tmp) / "roles.md").read_text(encoding="utf-8")
            sheet = (pathlib.Path(tmp) / "roles.csv").read_text(encoding="utf-8")
        self.assertEqual(table.count("](https://trainergigs.com/job-"), len(found))
        self.assertEqual(len(sheet.splitlines()), len(found) + 1)
        self.assertIn("Data: [TrainerGigs](https://trainergigs.com/?src=api)", table)


class LiveCheck(unittest.TestCase):
    """tools/check_live.py on the saved files: the daily, weekly and CSV samples are whole, the roles sample is a cut."""

    def files(self):
        import csv
        d, w = sample("ai-training-jobs-data.json"), sample("ai-training-jobs-weekly.json")
        with (SAMPLES / "ai-training-jobs-data.csv").open(encoding="utf-8") as fh:
            dc = list(csv.DictReader(fh))
        with (SAMPLES / "ai-training-jobs-weekly.csv").open(encoding="utf-8") as fh:
            wc = list(csv.DictReader(fh))
        found = sample("ai-training-jobs-roles.json")["roles"]
        stats = tg.pay_stats([r for r in found if r["kind"] == "role"])
        totals = dict(d["totals"], open_roles=sum(r["kind"] == "role" for r in found), paid_research_studies=sum(r["kind"] == "study" for r in found),
                      roles_with_hourly_pay=stats["roles"], q1_listed_hourly_usd=stats["q1"], median_listed_hourly_usd=stats["median"], q3_listed_hourly_usd=stats["q3"])
        roles = dict(sample("ai-training-jobs-roles.json"), totals=totals, counted="another day")
        return d, w, roles, dc, wc

    def test_whole_files_pass(self):
        bad, notes = check_live.check(*self.files())
        self.assertEqual((bad, notes), ([], []))

    def test_a_field_that_is_gone_fails_and_a_new_one_is_only_named(self):
        d, w, roles, dc, wc = copy.deepcopy(self.files())
        for r in roles["roles"]:
            del r["countries"]
            r["remote"] = True
        bad, notes = check_live.check(d, w, roles, dc, wc)
        self.assertEqual(bad, ["role: gone countries"])
        self.assertEqual(notes, ["role: new remote"])

    def test_rows_that_do_not_add_up_fail(self):
        d, w, roles, dc, wc = copy.deepcopy(self.files())
        d["totals"]["open_roles"] += 1
        roles["roles"][0]["url"] = "https://example.com/elsewhere"
        bad, _ = check_live.check(d, w, roles, dc, wc)
        self.assertEqual(len(bad), 2)
        self.assertIn("add up to", bad[0])
        self.assertIn("its url is not its page with the tag", bad[1])

    def test_it_reads_again_before_it_fails(self):
        good, said, waits = self.files(), [], []
        broken = copy.deepcopy(good)
        broken[0]["totals"]["open_roles"] += 1
        answers = [broken, good]
        self.assertEqual(check_live.main([], fetch=lambda: answers.pop(0), wait=waits.append, out=said.append), 0)
        self.assertEqual(waits, [90])
        self.assertTrue(said[-1].startswith("OK "))
        self.assertEqual(check_live.main(["--tries", "1"], fetch=lambda: broken, wait=waits.append, out=said.append), 1)
        self.assertTrue(said[-1].startswith("FAIL "))


if __name__ == "__main__":
    unittest.main()
