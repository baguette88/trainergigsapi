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
BOARD = "/board.json"
USER_AGENT = "trainergigs-python-client/1.0 (hello@trainergigs.com)"

ROW_FIELDS_FALLBACK = ("key", "page", "title", "cat", "provider", "pay", "paymin", "unit",
                       "salary", "posted", "seen", "rank", "regions", "skills", "flags",
                       "apply", "paylabel", "where", "more", "places", "bounty_usd")


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


def board(base=BASE):
    """board.json as a dict. The rows are lists, in the order of the "fields" list."""
    return json.loads(_get(BOARD, base))


def role_dicts(data):
    """Turn the rows of a board.json dict into dicts keyed by field name.

    Adds "url", the role's own page on trainergigs.com, and "field_label",
    the readable name of the role's field."""
    names = data.get("fields") or list(ROW_FIELDS_FALLBACK)
    cats = data.get("cats", {})
    out = []
    for row in data["rows"]:
        role = dict(zip(names, row))
        role["url"] = BASE + "/" + role["page"]
        role["field_label"] = cats.get(role["cat"], role["cat"])
        out.append(role)
    return out


def hourly_midpoint(role):
    """The listed hourly pay of a role, a range at its midpoint, or None.

    Only roles whose unit is "hr" count. The site counts a range at its midpoint."""
    if role.get("unit") != "hr":
        return None
    high, low = role.get("pay"), role.get("paymin")
    if not isinstance(high, (int, float)):
        return None
    if not isinstance(low, (int, float)):
        low = high
    return (high + low) / 2


def roles(field=None, platform=None, min_pay=None, data=None):
    """Open roles from the board, filtered.

    field: a field key such as "law" or its label such as "Finance" (case does not matter).
    platform: a platform name as the data gives it (case does not matter).
    min_pay: keep roles whose listed hourly pay, at the midpoint of a range, is at least this.
    data: a board.json dict you already hold. Without it the live board is fetched."""
    found = role_dicts(data if data is not None else board())
    out = []
    for role in found:
        if field and field.lower() not in (role["cat"].lower(), role["field_label"].lower()):
            continue
        if platform and platform.lower() != role["provider"].lower():
            continue
        if min_pay is not None:
            mid = hourly_midpoint(role)
            if mid is None or mid < min_pay:
                continue
        out.append(role)
    return out


def main():
    data = board()
    print("Board built", data.get("built"))
    for role in roles(data=data)[:5]:
        print("-", role["title"], "|", role["provider"], "|", role["paylabel"], "|", role["url"])
    print("Data: TrainerGigs, https://trainergigs.com")


if __name__ == "__main__":
    main()
