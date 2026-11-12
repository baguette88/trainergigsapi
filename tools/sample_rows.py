#!/usr/bin/env python3
"""Trim the sample table in examples/ to what a reader can use, and say where to send a correction.

  python3 tools/sample_rows.py examples/roles-100.md [--today 2026-11-12]

Keeps a row when its listing is dated within the last 30 days. Leaves out the platforms in LEFT_OUT, whose
names this project's own pages do not print. The table's other rows and its credit line stay as they were
written. One line is added at the end: where to write with a correction or a role to add."""
import datetime
import re
import sys

DAYS = 30
LEFT_OUT = ("mercor",)
CONTACT = "A correction, or a role or platform to add: hello@trainergigs.com"
ROW = re.compile(r"^\|.*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*(\d{4}-\d{2}-\d{2})?\s*\|$")


def trim(text, today):
    """The table with old rows and left-out platforms gone, and the contact line last. Returns (text, kept, dropped)."""
    out, kept, dropped = [], 0, 0
    for line in text.splitlines():
        if line.strip() == CONTACT:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(cells) == 5 and cells[0] not in ("Pay", "---"):
            platform, posted = cells[2].lower(), cells[4]
            old = True
            try:
                old = (today - datetime.date.fromisoformat(posted)).days > DAYS
            except ValueError:
                pass  # no date on the listing: it cannot be shown as fresh
            if platform in LEFT_OUT or old:
                dropped += 1
                continue
            kept += 1
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out + ["", CONTACT]) + "\n", kept, dropped


def main(argv):
    if not argv:
        sys.exit(__doc__.split("\n\n")[1])
    today = datetime.date.fromisoformat(argv[argv.index("--today") + 1]) if "--today" in argv else datetime.datetime.now(datetime.timezone.utc).date()
    with open(argv[0], encoding="utf-8") as f:
        text, kept, dropped = trim(f.read(), today)
    with open(argv[0], "w", encoding="utf-8") as f:
        f.write(text)
    print("%s: %d rows kept, %d left out" % (argv[0], kept, dropped))


if __name__ == "__main__":
    main(sys.argv[1:])
