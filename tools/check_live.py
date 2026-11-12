#!/usr/bin/env python3
"""Check the live files against what this repository documents. Standard library only.

    python3 tools/check_live.py

It fetches the five data files and compares them with the saved copies in tests/samples/. A documented field
that is gone is a failure. A field that is new is only named, since fields may be added at any time. It also
adds the files up: the rows against the totals, and the roles file against the daily file. It ends with 0 when
everything holds and 1 when something does not. The daily workflow runs it after it saves the day's files.
"""
import argparse
import json
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "clients" / "python"))
import trainergigs as tg  # noqa: E402

SAMPLES = ROOT / "tests" / "samples"


def sample(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def sample_columns(name):
    with (SAMPLES / name).open(encoding="utf-8") as fh:
        return fh.readline().strip().split(",")


def missing(documented, live):
    return [k for k in documented if k not in live]


def check(daily, weekly, roles, daily_rows, weekly_rows):
    """(failures, notes) for one reading of the live files."""
    bad, notes = [], []

    def keys(what, documented, live):
        gone = missing(documented, live)
        if gone:
            bad.append("%s: gone %s" % (what, ", ".join(gone)))
        new = [k for k in live if k not in documented]
        if new:
            notes.append("%s: new %s" % (what, ", ".join(new)))

    d, w, r = sample("ai-training-jobs-data.json"), sample("ai-training-jobs-weekly.json"), sample("ai-training-jobs-roles.json")
    keys("daily file", list(d), list(daily))
    keys("daily totals", list(d["totals"]), list(daily.get("totals", {})))
    keys("daily row", list(d["rows"][0]), list(daily["rows"][0]) if daily.get("rows") else [])
    keys("weekly file", list(w), list(weekly))
    keys("week", list(w["weeks"][0]), list(weekly["weeks"][0]) if weekly.get("weeks") else [])
    keys("roles file", list(r), list(roles))
    keys("role", list(r["roles"][0]), list(roles["roles"][0]) if roles.get("roles") else [])
    keys("daily CSV", sample_columns("ai-training-jobs-data.csv"), list(daily_rows[0]) if daily_rows else [])
    keys("weekly CSV", sample_columns("ai-training-jobs-weekly.csv"), list(weekly_rows[0]) if weekly_rows else [])
    if bad:
        return bad, notes

    totals = daily["totals"]
    for kind, key in (("role", "open_roles"), ("study", "paid_research_studies")):
        rows = sum(x["open_roles"] for x in daily["rows"] if x["kind"] == kind)
        if rows != totals[key]:
            bad.append("daily rows marked %s add up to %d, totals.%s says %d" % (kind, rows, key, totals[key]))
    if len(daily_rows) != len(daily["rows"]):
        bad.append("the daily CSV has %d rows, the daily JSON %d" % (len(daily_rows), len(daily["rows"])))
    if daily["fields"] != list(daily["rows"][0]):
        bad.append("the daily file's fields list is not the fields of its rows")

    found = roles["roles"]
    if roles["counted"] == daily["date"] and roles["totals"] != totals:
        bad.append("the roles file and the daily file state different totals for %s" % daily["date"])
    for kind, key in (("role", "open_roles"), ("study", "paid_research_studies")):
        n = sum(1 for x in found if x["kind"] == kind)
        if n != roles["totals"][key]:
            bad.append("%d rows of the roles file are marked %s, its totals.%s says %d" % (n, kind, key, roles["totals"][key]))
    stats = tg.pay_stats(tg.roles(data=roles))
    said = roles["totals"]
    stated = {"roles": said.get("roles_with_hourly_pay", 0), "q1": said.get("q1_listed_hourly_usd"),
              "median": said.get("median_listed_hourly_usd"), "q3": said.get("q3_listed_hourly_usd")}
    near = lambda a, b: a == b or (a is not None and b is not None and abs(a - b) < 0.01)
    if stats["roles"] != stated["roles"] or not all(near(stats[k], stated[k]) for k in ("q1", "median", "q3")):
        bad.append("hourly pay counted from the roles gives %s, the totals say %s" % (stats, stated))
    if len({x["id"] for x in found}) != len(found):
        bad.append("two roles share an id")
    for x in found:
        if x["url"] != "%s/%s?src=api" % (tg.BASE, x["id"]):
            bad.append("role %s: its url is not its page with the tag" % x["id"])
        elif x["kind"] not in ("role", "study") or x["pay_unit"] not in ("hr", "task", "yr", None):
            bad.append("role %s: a kind or a pay unit this repository does not document" % x["id"])
        elif any(not re.fullmatch("[A-Z]{2}", c) for c in x["countries"]):
            bad.append("role %s: a country that is not a two-letter code" % x["id"])
        elif x["posted"] is not None and not re.fullmatch(r"\d{4}-\d\d-\d\d", x["posted"]):
            bad.append("role %s: posted is not a day" % x["id"])
        if len(bad) > 20:
            break
    return bad, notes


def read():
    return tg.daily(), tg.weekly(), tg.roles_file(), tg.daily_csv(), tg.weekly_csv()


def main(argv=None, fetch=read, wait=time.sleep, out=print):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tries", type=int, default=2, help="read again after a pause when a check fails: a build may be writing the files")
    ap.add_argument("--pause", type=int, default=90, help="seconds between two reads")
    a = ap.parse_args(argv)
    bad = notes = []
    for turn in range(max(1, a.tries)):
        if turn:
            wait(a.pause)
        files = fetch()
        bad, notes = check(*files)
        if not bad:
            break
    for note in notes:
        out("NOTE  " + note)
    for line in bad:
        out("FAIL  " + line)
    if bad:
        return 1
    daily, weekly, roles = files[0], files[1], files[2]
    out("OK    %s: %d rows, %d weeks, %d roles and studies, every documented field present, the files add up"
        % (daily["date"], len(daily["rows"]), len(weekly["weeks"]), len(roles["roles"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
