#!/usr/bin/env python3
"""Write the day's numbers into README.md, between its two count marks. Standard library only.

    python3 tools/readme_counts.py path/to/ai-training-jobs-data.json

The daily workflow runs it on the file it has just fetched, so the numbers in the README carry the day they were
counted and are never older than a day. With no path it fetches the live file.
"""
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
START, END = "<!-- counts:start -->", "<!-- counts:end -->"


def money(x):
    words = format(x, ",.2f")
    return "$" + (words[:-3] if words.endswith(".00") else words)


def day_words(day):
    d = datetime.date.fromisoformat(day)
    return "%s %d, %d" % (d.strftime("%b"), d.day, d.year)


def counts(daily):
    """The paragraph for one daily file."""
    t = daily["totals"]
    said = ("On %s the daily file stated **{:,} open roles on {:,} platforms**, and {:,} paid research studies, "
            "which it counts apart." % day_words(daily["date"])).format(
                t["open_roles"], t["platforms_with_open_roles"], t["paid_research_studies"])
    if t.get("median_listed_hourly_usd") is not None:
        said += " The median listed pay was %s an hour, across %s roles that state hourly pay. The middle half list %s to %s." % (
            money(t["median_listed_hourly_usd"]), "{:,}".format(t["roles_with_hourly_pay"]),
            money(t["q1_listed_hourly_usd"]), money(t["q3_listed_hourly_usd"]))
    return said


def rewrite(text, daily):
    """The README's text with the paragraph between the marks replaced. The text is unchanged when a mark is missing."""
    head, mark, rest = text.partition(START)
    _, end, tail = rest.partition(END)
    if not mark or not end:
        return text
    return head + START + "\n" + counts(daily) + "\n" + END + tail


def main(argv=None, readme=ROOT / "README.md"):
    args = sys.argv[1:] if argv is None else argv
    if args:
        daily = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
    else:
        sys.path.insert(0, str(ROOT / "clients" / "python"))
        import trainergigs
        daily = trainergigs.daily()
    before = readme.read_text(encoding="utf-8")
    after = rewrite(before, daily)
    if after != before:
        readme.write_text(after, encoding="utf-8")
    print("README counts: %s, %s" % (daily["date"], "written" if after != before else "no change"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
