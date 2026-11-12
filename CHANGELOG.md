# Changes

## 1.3.0, Nov 12, 2026

- A filter that could never match is an error and no longer an empty answer. A country that is not a two-letter code ("Nigeria" for "NG") and a day that is not written `2026-11-01` raise `ValueError` in the Python client and throw a `RangeError` in the JavaScript client. In 1.2.0 both returned no roles.
- The command line names what went wrong and ends with code 2. A field or a platform the file does not have gets the close names and the way to see them all. `--limit` below 0 is refused. A real name with no role that day still answers "0 found".
- New: `--csv` on `roles`, `fields`, `platforms` and `countries`, and `roles_csv` in the Python client, for a table to open in a spreadsheet. A title that begins like a formula is kept as text.

Nothing was taken away, and the files on trainergigs.com did not change. One thing to know: code that passed a country name or a date in another form got an empty list in 1.2.0 and gets an error now.

## 1.2.0, Nov 12, 2026

- Pay in words keeps the listing's own words. A top with no bottom reads "Up to $90/hr", where 1.1.0 wrote "$90/hr". A bottom with no top reads "From $25/hr". Cents are written in full: "$47.50/hr".
- New in both clients: `by_pay` (`byPay`) sorts best paid first, `tally` counts the roles under each field, platform or country, and `pay_stats` (`payStats`) gives the median listed hourly pay as the site counts it. The JavaScript client gains `payText` and `line`.
- The command line gains `fields`, `platforms`, `countries` and `pay`, each with every filter. `totals` prints lines in place of a Python dict. A failed read ends with one line, not a traceback.
- The Python client asks for gzip, so the roles file comes as about 150 KB in place of 1.5 MB.
- It installs from this repository: `pip install git+https://github.com/baguette88/trainergigsapi` and `npm install github:baguette88/trainergigsapi`.
- `openapi.yaml` no longer forbids fields it does not list on a role, since fields may be added. It says when `pay_min` and `pay_max` are null, and it describes the 304 and the 403.
- The README says that the site refuses the default User-Agent of Python's urllib, which a plain `pandas.read_csv` sends, and shows the one line that fixes it.
- `tools/check_live.py` checks the live files against the documents each day, and `tests/test_docs.py` fails when a field is missing from the README or from `openapi.yaml`.
- The daily workflow writes the day's numbers into the README, and it no longer saves a file that does not parse.
- New examples: `examples/pandas_example.py` and `examples/roles_page.html`.

Nothing was taken away, and the files on trainergigs.com did not change.

## 1.1.0, Nov 11, 2026

- The roles file gives each role an `id`, its `countries` as two-letter codes, and its `url` with the tag `src=api`.
- The Python client filters by country and by the day a role was posted, and has a command line.
- A JavaScript client, `clients/js/trainergigs.mjs`, for Node 18 or newer and for a browser page.
- A recipe that posts new roles into a Discord channel, `examples/discord_new_roles.py`.
- The clients are tested on every push.

Nothing was taken away. A program written for 1.0.0 still runs, with one thing to know: `url` now ends in `?src=api`,
so use `id` where you compared addresses.

## 1.0.0, Nov 11, 2026

- The field reference, the OpenAPI description, the Python client, the examples and the daily archive.
