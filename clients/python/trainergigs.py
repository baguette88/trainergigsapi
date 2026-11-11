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


def roles(field=None, platform=None, min_pay=None, kind="role", data=None):
    """Open roles from the roles file, filtered. Each role has a "url", its own page on trainergigs.com.

    field: the field's name as the file gives it, such as "Law" (case does not matter).
    platform: a platform name as the file gives it (case does not matter).
    min_pay: keep roles whose listed hourly pay, at the midpoint of a range, is at least this.
    kind: "role" (the default), "study", or None for both.
    data: a roles file dict you already hold. Without it the live file is fetched."""
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
        out.append(role)
    return out


def main():
    data = roles_file()
    print("Counted on", data.get("counted"))
    for role in roles(data=data)[:5]:
        pay = role["pay_min"], role["pay_max"], role["pay_unit"]
        print("-", role["title"], "|", role["platform"], "|", pay, "|", role["url"])
    print("Data: TrainerGigs, https://trainergigs.com")


if __name__ == "__main__":
    main()
