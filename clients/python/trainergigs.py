"""Read the free TrainerGigs job data with the Python standard library only.

Data: TrainerGigs, https://trainergigs.com

Run "python3 trainergigs.py" to print five open roles.
"""
import csv
import io
import json
import urllib.request

BASE = "https://trainergigs.com"
DAILY = "/ai-training-jobs-data"
WEEKLY = "/ai-training-jobs-weekly"
ROLES = "/ai-training-jobs-roles.json"
USER_AGENT = "trainergigs-api-client/1.0"


def _get(path, base=BASE, timeout=30):
    req = urllib.request.Request(base + path, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


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
    """The listed hourly pay of a role, a range at its midpoint, or None.

    Only roles whose pay_unit is "hr" count. The site counts a range at its midpoint."""
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


def roles(field=None, platform=None, min_pay=None, kind="role", data=None, country=None, unnamed=False, since=None):
    """Open roles from the roles file, filtered. Each role has an "id" and a "url", its own page on trainergigs.com.

    field: the field's name as the file gives it, such as "Law" (case does not matter).
    platform: a platform name as the file gives it (case does not matter).
    min_pay: keep roles whose listed hourly pay, at the midpoint of a range, is at least this.
    kind: "role" (the default), "study", or None for both.
    country: a two-letter country code such as "NG". Keeps the roles whose listing names that country.
    unnamed: with country, also keep the roles whose listing names no country at all.
    since: a day such as "2026-11-01". Keeps the roles their platform dated on or after it.
    data: a roles file dict you already hold. Without it the live file is fetched."""
    found = (data if data is not None else roles_file())["roles"]
    code = country.upper() if country else None
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


def pay_text(role):
    """The listed pay as words, such as "$40 to $60/hr", or "pay not listed"."""
    low, high, unit = role.get("pay_min"), role.get("pay_max"), role.get("pay_unit")
    if not unit or (low is None and high is None):
        return "pay not listed"
    money = lambda x: "$" + format(x, ",.2f").rstrip("0").rstrip(".")
    low, high = (low if low is not None else high), (high if high is not None else low)
    words = money(low) if low == high else money(low) + " to " + money(high)
    return words + "/" + unit + (", paid per task" if role.get("paid_per_task") else "")


def line(role):
    """One role on one line: its pay, title, platform and page."""
    return "%s | %s | %s | %s" % (pay_text(role), role["title"], role["platform"], role["url"])


def main(argv=None, out=print, fetch=roles_file):
    """python3 trainergigs.py [roles] [--country NG] [--field Law] [--platform micro1] [--min-pay 40]
    [--since 2026-11-01] [--unnamed] [--studies] [--limit 10] [--json], or: python3 trainergigs.py totals"""
    import argparse
    ap = argparse.ArgumentParser(description="Open remote AI training roles from TrainerGigs, https://trainergigs.com")
    ap.add_argument("what", nargs="?", default="roles", choices=("roles", "totals"))
    ap.add_argument("--country", help="a two-letter code, such as NG, KE, IN, PH or US")
    ap.add_argument("--unnamed", action="store_true", help="with --country: also roles whose listing names no country")
    ap.add_argument("--field")
    ap.add_argument("--platform")
    ap.add_argument("--min-pay", type=float, help="listed hourly pay, a range at its midpoint")
    ap.add_argument("--since", help="a day, such as 2026-11-01")
    ap.add_argument("--studies", action="store_true", help="paid research studies in place of roles")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    data = fetch()
    if a.what == "totals":
        out(json.dumps(data.get("totals"), indent=1) if a.json else "Counted on %s: %s" % (data.get("counted"), data.get("totals")))
        return 0
    found = roles(field=a.field, platform=a.platform, min_pay=a.min_pay, kind="study" if a.studies else "role", data=data,
                  country=a.country, unnamed=a.unnamed, since=a.since)
    found.sort(key=lambda r: -(hourly_midpoint(r) or 0))
    shown = found[:a.limit] if a.limit else found
    if a.json:
        out(json.dumps(shown, indent=1))
        return 0
    out("Counted on %s: %d found, %d shown" % (data.get("counted"), len(found), len(shown)))
    for role in shown:
        out("- " + line(role))
    out("Data: TrainerGigs, https://trainergigs.com")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
