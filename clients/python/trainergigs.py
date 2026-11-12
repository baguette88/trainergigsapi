"""Read the free TrainerGigs job data with the Python standard library only.

Data: TrainerGigs, https://trainergigs.com

Run "python3 trainergigs.py" to print five open roles, or "python3 trainergigs.py --help".
"""
import csv
import gzip
import io
import json
import re
import urllib.error
import urllib.request

__version__ = "1.5.0"

BASE = "https://trainergigs.com"
DAILY = "/ai-training-jobs-data"
WEEKLY = "/ai-training-jobs-weekly"
ROLES = "/ai-training-jobs-roles.json"
USER_AGENT = "trainergigs-api-client/" + __version__
CREDIT = "Data: TrainerGigs, https://trainergigs.com"
MIN_ROLES = 8  # the site gives a median only when this many roles state hourly pay
CSV_COLUMNS = ("pay", "title", "platform", "field", "kind", "pay_min", "pay_max", "pay_unit", "paid_per_task",
               "countries", "posted", "url")


def _get(path, base=BASE, timeout=30):
    """The text of one file. It names itself in the User-Agent and asks for gzip: the roles file is ten times smaller that way."""
    req = urllib.request.Request(base + path, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    return body.decode("utf-8")


def daily(base=BASE):
    """The daily file: totals, method and one row per platform and field."""
    return json.loads(_get(DAILY + ".json", base))


def weekly(base=BASE):
    """The weekly file: every closed week, with method and notes."""
    return json.loads(_get(WEEKLY + ".json", base))


def daily_csv(base=BASE):
    """The daily CSV as a list of dicts. Every value is text."""
    return list(csv.DictReader(io.StringIO(_get(DAILY + ".csv", base))))


def weekly_csv(base=BASE):
    """The weekly CSV as a list of dicts. Every value is text."""
    return list(csv.DictReader(io.StringIO(_get(WEEKLY + ".csv", base))))


def roles_file(base=BASE):
    """The roles file as a dict: source, counted, license, fields, totals and roles."""
    return json.loads(_get(ROLES, base))


def hourly_midpoint(role):
    """The listed hourly pay of a role, a range at its midpoint, or None. Only roles whose pay_unit is "hr" count.

    A listing that states one end only ("Up to $90/hr") counts at that end. pay_text says which end it is."""
    if role.get("pay_unit") != "hr":
        return None
    high, low = role.get("pay_max"), role.get("pay_min")
    if high is None and low is None:
        return None
    if high is None:
        high = low
    if low is None:
        low = high
    return (high + low) / 2


def _country_code(country):
    if not country:
        return None
    code = str(country).strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", code):
        raise ValueError('country takes a two-letter code such as "NG" for Nigeria, not "%s"' % country)
    return code


def _day(since):
    if not since:
        return None
    day = str(since).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise ValueError('since takes a day written as "2026-11-01", not "%s"' % since)
    return day


def roles(field=None, platform=None, min_pay=None, kind="role", data=None, country=None, unnamed=False, since=None):
    """Open roles from the roles file, filtered. Each role has an "id" and a "url", its own page on trainergigs.com.

    field: the field's name as the file gives it, such as "Law" (case does not matter).
    platform: a platform name as the file gives it (case does not matter).
    min_pay: keep roles whose listed hourly pay, at the midpoint of a range, is at least this.
    kind: "role" (the default), "study", or None for both.
    country: a two-letter country code such as "NG". Keeps the roles whose listing names that country.
    unnamed: with country, also keep the roles whose listing names no country at all.
    since: a day such as "2026-11-01". Keeps the roles their platform dated on or after it.
    data: a roles file dict you already hold. Without it the live file is fetched.

    A country that is not a two-letter code, or a day that is not written YYYY-MM-DD, raises ValueError. Either
    would match nothing, and an empty answer would look like a day with no such roles."""
    code = _country_code(country)
    since = _day(since)
    found = (data if data is not None else roles_file())["roles"]
    out = []
    for role in found:
        if kind and role["kind"] != kind:
            continue
        if field and field.lower() != role["field"].lower():
            continue
        if platform and platform.lower() != role["platform"].lower():
            continue
        if min_pay is not None:
            mid = hourly_midpoint(role)
            if mid is None or mid < min_pay:
                continue
        if code:
            named = role.get("countries") or []
            if code not in named and not (unnamed and not named):
                continue
        if since and not ((role.get("posted") or "") >= since):
            continue
        out.append(role)
    return out


def by_pay(found):
    """The same roles, best paid by the hour first. Roles with no listed hourly pay come last, in the order given."""
    return sorted(found, key=lambda r: -(hourly_midpoint(r) or 0))


def tally(found, key):
    """How many of the roles fall under each value of one field, most first: [("Law", 91), ...].

    key: "field", "platform", "kind", "pay_unit" or "countries" (a role counts once under each country it names)."""
    counts = {}
    for role in found:
        value = role.get(key)
        for one in (value if isinstance(value, list) else [value]):
            if one is not None:
                counts[one] = counts.get(one, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))


def _share(values, share):
    spot = (len(values) - 1) * share
    at = int(spot)
    after = min(at + 1, len(values) - 1)
    return values[at] + (values[after] - values[at]) * (spot - at)


def pay_stats(found):
    """The listed hourly pay of a set of roles, counted as the site counts it: {"roles", "q1", "median", "q3"}.

    A role counts when its unit is "hr", its listing states both ends (one rate is both ends) and it does not say it
    pays per task. A range counts at its midpoint. "q1", "median" and "q3" are None when fewer than 8 roles count,
    as on the site. Over every row marked role this gives the numbers in the file's own totals."""
    mids = sorted((r["pay_min"] + r["pay_max"]) / 2 for r in found
                  if r.get("pay_unit") == "hr" and not r.get("paid_per_task")
                  and r.get("pay_min") is not None and r.get("pay_max") is not None)
    if len(mids) < MIN_ROLES:
        return {"roles": len(mids), "q1": None, "median": None, "q3": None}
    return {"roles": len(mids), "q1": _share(mids, 0.25), "median": _share(mids, 0.5), "q3": _share(mids, 0.75)}


def _money(x):
    """Dollars as the site writes them: $40, $35.50, $130,000."""
    words = format(x, ",.2f")
    return "$" + (words[:-3] if words.endswith(".00") else words)


def pay_text(role):
    """The listed pay as the listing states it: "$40 to $60/hr", "Up to $90/hr", "From $25/hr" or "pay not listed"."""
    low, high, unit = role.get("pay_min"), role.get("pay_max"), role.get("pay_unit")
    if not unit or (low is None and high is None):
        return "pay not listed"
    if low is None:
        words = "Up to " + _money(high)
    elif high is None:
        words = "From " + _money(low)
    elif low == high:
        words = _money(low)
    else:
        words = _money(low) + " to " + _money(high)
    return words + "/" + unit + (", paid per task" if role.get("paid_per_task") else "")


def line(role):
    """One role on one line: its pay, title, platform and page."""
    return "%s | %s | %s | %s" % (pay_text(role), role["title"], role["platform"], role["url"])


def _cell(text):
    """Text for a spreadsheet cell. A title comes from a listing, so one that begins like a formula is kept as text."""
    text = "" if text is None else str(text)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def roles_csv(found):
    """The roles as CSV text for a spreadsheet, one row each, with a header row. The columns are CSV_COLUMNS.

    "pay" is the pay in words, as pay_text writes it. "countries" holds the codes with a space between them.
    "url" is the role's own page on trainergigs.com."""
    held = io.StringIO()
    rows = csv.writer(held, lineterminator="\n")
    rows.writerow(CSV_COLUMNS)
    for r in found:
        rows.writerow([pay_text(r), _cell(r.get("title")), _cell(r.get("platform")), _cell(r.get("field")), r.get("kind") or "",
                       "" if r.get("pay_min") is None else r["pay_min"], "" if r.get("pay_max") is None else r["pay_max"],
                       r.get("pay_unit") or "", "true" if r.get("paid_per_task") else "false",
                       " ".join(r.get("countries") or []), r.get("posted") or "", r.get("url") or ""])
    return held.getvalue()


def _md(text):
    """Text for a cell of a Markdown table. A title comes from a listing, so its marks are kept as plain text."""
    text = " ".join(("" if text is None else str(text)).split())
    return re.sub(r"([\\|\[\]<>*_`$])", r"\\\1", text)


def _md_credit(counted=None):
    credit = "Data: [TrainerGigs](%s/?src=api)" % BASE
    return "Counted on %s. %s" % (counted, credit) if counted else credit


def roles_markdown(found, counted=None):
    """The roles as a Markdown table, one row each, for a README, an issue or a wiki page.

    The columns are the pay in words, the title as a link to the role's own page on trainergigs.com, the platform,
    the field and the day the platform dated the listing. The last line gives the credit, and the day the roles
    were counted when you pass it. With no roles the table is one line that says so."""
    lines = ["| Pay | Role | Platform | Field | Posted |", "|---|---|---|---|---|"]
    for r in found:
        lines.append("| %s | [%s](%s) | %s | %s | %s |" % (
            _md(pay_text(r)), _md(r.get("title")), r.get("url") or "", _md(r.get("platform")), _md(r.get("field")), r.get("posted") or ""))
    if not found:
        lines = ["No open roles matched."]
    return "\n".join(lines + ["", _md_credit(counted)]) + "\n"


def _unknown_name(data, key, name):
    """None when the file has a field or platform of that name. Otherwise the lines that say so and what it does have."""
    names = [n for n, _ in tally(data.get("roles", []), key)]
    if not name or name.lower() in (n.lower() for n in names):
        return None
    import difflib
    lower = {n.lower(): n for n in names}
    near = [lower[n] for n in difflib.get_close_matches(name.lower(), list(lower), n=3, cutoff=0.5)]
    near += [n for n in names if name.lower() in n.lower() and n not in near]
    said = ['No %s is named "%s" in the file of %s.' % (key, name, data.get("counted"))]
    if near:
        said.append("Close to it: " + ", ".join(near[:5]))
    if key == "field":
        said.append("The fields: " + ", ".join(sorted(names)))
    else:
        said.append('Run "trainergigs %ss" to see every name.' % key)
    return said


def _totals_lines(data):
    t = data.get("totals") or {}
    said = ["Counted on %s" % data.get("counted", data.get("date")),
            "{:,} open roles on {:,} platforms".format(t.get("open_roles", 0), t.get("platforms_with_open_roles", 0)),
            "{:,} paid research studies, counted apart".format(t.get("paid_research_studies", 0)),
            "{:,} roles state pay, {:,} of them by the hour".format(t.get("roles_that_state_pay", 0), t.get("roles_with_hourly_pay", 0))]
    if t.get("median_listed_hourly_usd") is not None:
        said.append("Median listed hourly pay %s, the middle half %s to %s" % (
            _money(t["median_listed_hourly_usd"]), _money(t["q1_listed_hourly_usd"]), _money(t["q3_listed_hourly_usd"])))
    return said


def main(argv=None, out=print, fetch=roles_file):
    """python3 trainergigs.py [roles|totals|fields|platforms|countries|pay] [--country NG] [--field Law]
    [--platform micro1] [--min-pay 40] [--since 2026-11-01] [--unnamed] [--studies] [--limit 10] [--json] [--csv] [--md]"""
    import argparse
    import sys
    ap = argparse.ArgumentParser(
        description="Open remote AI training roles from TrainerGigs, https://trainergigs.com",
        epilog="roles lists them, best paid first. totals prints the day's numbers. fields, platforms and countries "
               "count the roles under each name, which is also how to see the names a filter takes. pay gives the "
               "median listed hourly pay. Every filter works with every one of them but totals.")
    ap.add_argument("what", nargs="?", default="roles", choices=("roles", "totals", "fields", "platforms", "countries", "pay"))
    ap.add_argument("--country", help="a two-letter code, such as NG, KE, IN, PH or US")
    ap.add_argument("--unnamed", action="store_true", help="with --country: also roles whose listing names no country")
    ap.add_argument("--field", help='a field as the file names it, such as Law or "Language & Audio"')
    ap.add_argument("--platform", help="a platform as the file names it")
    ap.add_argument("--min-pay", type=float, help="listed hourly pay, a range at its midpoint")
    ap.add_argument("--since", help="a day, such as 2026-11-01")
    ap.add_argument("--studies", action="store_true", help="paid research studies in place of roles")
    ap.add_argument("--limit", type=int, default=5, help="how many roles to show: 5 unless you say, 0 for all")
    ap.add_argument("--json", action="store_true", help="print data in place of lines")
    ap.add_argument("--csv", action="store_true", help="print CSV for a spreadsheet, with roles and with the counts")
    ap.add_argument("--md", action="store_true", help="print a Markdown table, with roles and with the counts")
    ap.add_argument("--version", action="version", version="trainergigs " + __version__)
    a = ap.parse_args(argv)

    def stop(*said):
        print("\n".join(said), file=sys.stderr)
        return 2

    # A filter that could never match is said before anything is fetched. An empty answer would read as "no such roles".
    try:
        _country_code(a.country)
    except ValueError as err:
        return stop(str(err), 'Run "trainergigs countries" to see the codes in the file.')
    try:
        _day(a.since)
    except ValueError as err:
        return stop(str(err))
    if a.limit < 0:
        return stop("--limit takes 0 for every role, or a number above 0")
    if a.csv + a.json + a.md > 1:
        return stop("--csv, --json and --md do not go together")
    if (a.csv or a.md) and a.what in ("totals", "pay"):
        return stop("--csv and --md go with roles, fields, platforms and countries")
    try:
        data = fetch()
    except (urllib.error.URLError, OSError, ValueError) as err:
        print("Could not read %s%s: %s" % (BASE, ROLES, err), file=sys.stderr)
        return 1
    counted = data.get("counted")
    if a.what == "totals":
        out(json.dumps(data.get("totals"), indent=1) if a.json else "\n".join(_totals_lines(data)))
        return 0
    kind = "study" if a.studies else "role"
    for key, name in (("field", a.field), ("platform", a.platform)):
        unknown = _unknown_name(data, key, name)
        if unknown:
            return stop(*unknown)
    found = roles(field=a.field, platform=a.platform, min_pay=a.min_pay, kind=kind, data=data,
                  country=a.country, unnamed=a.unnamed, since=a.since)
    if a.what in ("fields", "platforms", "countries"):
        rows = tally(found, {"fields": "field", "platforms": "platform", "countries": "countries"}[a.what])
        if a.json:
            out(json.dumps(dict(rows), indent=1))
            return 0
        if a.csv:
            out("\n".join(["name,roles"] + ["%s,%d" % ('"%s"' % _cell(name).replace('"', '""'), n) for name, n in rows]))
            return 0
        if a.md:
            out("\n".join(["| %s | Roles |" % a.what[:-1].capitalize().replace("Countrie", "Country"), "|---|---|"]
                          + ["| %s | %d |" % (_md(name), n) for name, n in rows] + ["", _md_credit(counted)]))
            return 0
        out("Counted on %s: %d found under %d %s" % (counted, len(found), len(rows), a.what))
        for name, n in rows:
            out("%6d  %s" % (n, name))
        out(CREDIT)
        return 0
    if a.what == "pay":
        stats = pay_stats(found)
        if a.json:
            out(json.dumps(dict(stats, counted=counted, found=len(found)), indent=1))
            return 0
        out("Counted on %s: %d found, %d state hourly pay" % (counted, len(found), stats["roles"]))
        if stats["median"] is None:
            out("No median: fewer than %d roles state hourly pay" % MIN_ROLES)
        else:
            out("Median listed hourly pay %s, the middle half %s to %s" % tuple(_money(stats[k]) for k in ("median", "q1", "q3")))
        out(CREDIT)
        return 0
    found = by_pay(found)
    shown = found[:a.limit] if a.limit else found
    if a.json:
        out(json.dumps(shown, indent=1))
        return 0
    if a.csv:
        out(roles_csv(shown).rstrip("\n"))
        return 0
    if a.md:
        out(roles_markdown(shown, counted=counted).rstrip("\n"))
        return 0
    out("Counted on %s: %d found, %d shown" % (counted, len(found), len(shown)))
    for role in shown:
        out("- " + line(role))
    out(CREDIT)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
