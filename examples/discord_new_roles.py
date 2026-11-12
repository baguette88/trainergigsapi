#!/usr/bin/env python3
"""Post the roles that are new since the last run into a Discord channel, through a webhook of that channel.

    python3 examples/discord_new_roles.py --webhook https://discord.com/api/webhooks/... --country NG --min-pay 20

Run it once a day (cron, a scheduled workflow). It remembers the roles it has posted in a small file beside it
(--seen), so a role is posted once. The first run posts nothing: it only notes what is open, so a channel is not
flooded. Each line links to the role's own page on trainergigs.com. Standard library only.
Data: TrainerGigs, https://trainergigs.com"""
import argparse
import json
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "clients" / "python"))
import trainergigs as tg  # noqa: E402

MOST = 8  # roles in one message: a Discord message holds 2,000 characters


def message(found):
    lines = ["**New remote AI training roles**"] + ["- %s: %s (%s) <%s>" % (tg.pay_text(r), r["title"], r["platform"], r["url"]) for r in found[:MOST]]
    more = len(found) - MOST
    return "\n".join(lines + (["and %d more on https://trainergigs.com/?src=api" % more] if more > 0 else ["Data: TrainerGigs, https://trainergigs.com"]))


def run(args, fetch=tg.roles_file, send=None):
    seen_path = pathlib.Path(args.seen)
    first = not seen_path.exists()
    seen = set() if first else set(json.loads(seen_path.read_text(encoding="utf-8")))
    data = fetch()
    found = tg.roles(field=args.field, min_pay=args.min_pay, country=args.country, unnamed=args.unnamed, data=data)
    new = tg.by_pay([r for r in found if r["id"] not in seen])
    if new and not first:
        (send or post)(args.webhook, message(new))
    seen_path.write_text(json.dumps(sorted(seen | {r["id"] for r in found})), encoding="utf-8")
    return 0 if first else len(new)


def post(webhook, text):
    req = urllib.request.Request(webhook, data=json.dumps({"content": text}).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": tg.USER_AGENT})
    urllib.request.urlopen(req, timeout=30).read()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--webhook", required=True)
    ap.add_argument("--country")
    ap.add_argument("--unnamed", action="store_true")
    ap.add_argument("--field")
    ap.add_argument("--min-pay", type=float)
    ap.add_argument("--seen", default=str(pathlib.Path(__file__).with_name("seen_roles.json")))
    print("posted %d new roles" % run(ap.parse_args()))
