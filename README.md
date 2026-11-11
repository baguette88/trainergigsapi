# AI training jobs API

Free, read-only data on remote AI training jobs from [TrainerGigs](https://trainergigs.com). No key and no sign-up. Fetch the files, use them, and credit the source.

This repository holds a field reference, an OpenAPI description, a small Python client, runnable examples and a dated archive of the daily and weekly files.

## Endpoints

All addresses are on `https://trainergigs.com`. A CDN caches each file for 5 minutes.

| Address | Format | What it holds | How often it changes |
|---|---|---|---|
| `/ai-training-jobs-data.json` | JSON | Open roles by platform and field, the day's totals, the counting method | Rebuilt daily |
| `/ai-training-jobs-data.csv` | CSV | The same rows as the daily JSON | Rebuilt daily |
| `/ai-training-jobs-weekly.json` | JSON | Every closed week, with a total row and rows by platform and field | A week is added after it closes |
| `/ai-training-jobs-weekly.csv` | CSV | The same weeks as one long table | A week is added after it closes |
| `/board.json` | JSON | The live board, every open role, one row per role | With each site build. The `built` field gives the day |
| `/feed.xml` | RSS | Roles on the board | With the site build |
| `/feed-weekly.xml` | RSS | One item per closed week | A week is added after it closes |
| `/feed-changes.xml` | RSS | Platforms whose open roles grew, week by week | A week is added after it closes |
| `/sitemap.xml` | XML | Every page on the site | With the site build |
| `/llms.txt` | Text | A plain list of every page, with its number of the day | With the site build |

The site does not publish a build time. Read the `date` or `built` field in a file to see its day.

### Browser use

These files send no `Access-Control-Allow-Origin` header today. A web page on another site cannot fetch them with `fetch` yet. Servers, scripts, notebooks and spreadsheets are not affected. The examples here run outside a browser.

## Counts on Nov 11, 2026

The daily file for Nov 11, 2026 states 3,100 open roles on 33 platforms and 437 paid research studies, which it counts apart from the roles. For any other day, fetch the file. The live number is always in `totals` in the daily JSON.

## Field reference

Every field below was read from the live files on Nov 11, 2026.

### Daily file: `ai-training-jobs-data.json`

Top level: `name`, `date`, `source`, `method`, `totals`, `fields`, `rows`.

`totals`:

| Field | Meaning |
|---|---|
| `open_roles` | Sum of `open_roles` over the rows where `kind` is `role` |
| `platforms_with_open_roles` | Platforms with at least one open role |
| `paid_research_studies` | Sum of `open_roles` over the rows where `kind` is `study` |
| `roles_that_state_pay` | Roles that state pay in any unit |
| `roles_with_hourly_pay` | Roles that state hourly pay |
| `median_listed_hourly_usd` | Median listed hourly pay in US dollars |
| `q1_listed_hourly_usd` | First quartile of listed hourly pay |
| `q3_listed_hourly_usd` | Third quartile of listed hourly pay |

`rows`, one per platform and field. The CSV has the same columns.

| Field | Meaning |
|---|---|
| `platform` | The platform's name |
| `field` | The board's name for the field of work |
| `open_roles` | Listings open on the day |
| `roles_with_hourly_pay` | Of those, listings that state hourly pay |
| `median_listed_hourly_usd` | Median listed hourly pay, empty when fewer than 8 roles state hourly pay |
| `posted_last_7_days` | Roles the platform itself dates within the last 7 days |
| `countries_named` | Countries the listings name, or the platform's published list |
| `feed_read` | The day the platform's listings were read |
| `kind` | `role` or `study` |

### Weekly file: `ai-training-jobs-weekly.json`

Top level: `name`, `source`, `method`, `notes`, `revisions`, `weeks`. Each item in `weeks` has these fields:

`week`, `week_start`, `week_end`, `last_day`, `days_counted`, `days_missing`, `closed_on`, `revised`, `open_sunday`, `open_prev_sunday`, `studies_sunday`, `listed_any_day`, `new_roles`, `renewed_new`, `gone_roles`, `renewed_gone`, `newly_tracked`, `old_postings`, `roles_100_plus`, `roles_100_plus_prev`, `roles_with_hourly_pay`, `median_listed_hourly_usd`, `q1_listed_hourly_usd`, `q3_listed_hourly_usd`, `platforms_read`, `feeds_not_read`, `languages_named`, `countries_named`, `days_listed_median`, `days_listed_n`, `roles_sunday`, `roles_prev_sunday`, `roles_new`, `roles_gone`, `platforms_with_roles`, `url`.

How to read them, from the file's own notes and method:

* A week runs Monday to Sunday, UTC. `last_day` is its day of record.
* `open_sunday`, `open_prev_sunday`, `new_roles` and `gone_roles` count every listing, paid research studies among them.
* `roles_sunday`, `roles_prev_sunday`, `roles_new` and `roles_gone` are the same counts with the research studies left out.
* `renewed_new` and `renewed_gone` count ids that are the same role as one gone or new. They are neither new nor gone.
* `roles_100_plus` counts roles whose listed hourly pay reaches $100.
* `url` is the week's own page on trainergigs.com.

The weekly CSV (`ai-training-jobs-weekly.csv`) has one row per week, platform and field. Its columns are `week`, `week_start`, `week_end`, `last_day`, `days_counted`, `closed_on`, `revised`, `platform`, `field`, `open_sunday`, `open_prev_sunday`, `listed_any_day`, `new_roles`, `gone_roles`, `renewed`, `newly_tracked`, `old_postings`, `roles_100_plus`, `roles_with_hourly_pay`, `median_listed_hourly_usd`, `q1_listed_hourly_usd`, `q3_listed_hourly_usd`, `platforms_read`, `feeds_not_read`, `languages_named`, `countries_named`, `days_listed_median`, `days_listed_n`. Platform and field are blank on the week's total row. Field is blank on a platform's row. Platform is blank on a field's row. The week's own numbers, from `platforms_read` to `days_listed_n`, are on its total row only.

### Board file: `board.json`

Top level: `built`, `new_since`, `v`, `fields`, `rows`, `providers`, `cats`, `places`.

* `fields` lists the names of the columns in each row.
* `rows` holds one list per open role, in the order of `fields`.
* `cats` maps a field key to its label.
* `providers` maps a platform name to its apply label.
* `places` is a table of country codes. A row's `places` value is an index into it.

Row values this repository documents:

| Field | Meaning |
|---|---|
| `key` | The role's id |
| `page` | The role's page name. The page is `https://trainergigs.com/<page>` |
| `title` | The listing's title |
| `cat` | The field key, a key of `cats` |
| `provider` | The platform's name |
| `pay` | The upper end of the listed pay as a number, empty when none is listed |
| `paymin` | The lower end of the listed pay as a number, empty when none is listed |
| `unit` | `hr`, `task`, `yr`, `hrtask` (an hourly figure on a role paid per task) or empty |
| `salary` | The yearly figure when `unit` is `yr`, otherwise empty |
| `posted` | The day the platform dated the listing, when it does |
| `seen` | The day the board first saw the listing |
| `paylabel` | The pay as the listing states it, or `Pay not listed` |
| `where` | A short place text |

Link to a role through its page on trainergigs.com. The other row values are there for the site's own pages and are not part of this reference.

## Examples

Curl:

```sh
curl -s https://trainergigs.com/ai-training-jobs-data.json
curl -s https://trainergigs.com/ai-training-jobs-weekly.csv -o weekly.csv
```

Python, standard library only (`examples/example.py`). Send a `User-Agent` header of your own. A request with Python's default one was refused with HTTP 403 when this was written:

```python
import json
import urllib.request

url = "https://trainergigs.com/ai-training-jobs-data.json"
req = urllib.request.Request(url, headers={"User-Agent": "my-script/1.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)
print(data["date"], data["totals"]["open_roles"], "open roles")
```

Node 18 or newer (`examples/example.mjs`):

```js
const res = await fetch("https://trainergigs.com/ai-training-jobs-data.json")
const data = await res.json()
console.log(data.date, data.totals.open_roles, "open roles")
```

This runs in Node. In a browser it fails until the site sends the header described above.

Google Sheets, on the CSV:

```
=IMPORTDATA("https://trainergigs.com/ai-training-jobs-data.csv")
```

A small client with filters is in `clients/python/trainergigs.py`. Run `python3 clients/python/trainergigs.py` to print five open roles. Run `python3 -m unittest` inside `clients/python` to test it against the saved files in `tests/samples/`. The board sample is a cut of 20 rows.

## How the numbers are counted

These lines come from the `method` list inside `ai-training-jobs-data.json` and `ai-training-jobs-weekly.json`. Each semicolon in the original is shown here as a full stop. The files carry the exact text.

Daily file:

* A role is one listing in a platform's own public feed, read that day. Copies with the same title and pay on one platform count once.
* Listed pay is hourly pay that the platform lists, as one rate or a range. A range counts at its midpoint. A median is given only when 8 or more roles state hourly pay. Nothing is estimated or converted.
* posted_last_7_days counts roles the platform itself dates within the last 7 days.
* countries_named counts the countries the roles' own listings name, or their platform's published list.
* kind is role or study. Paid research studies on study panels are counted apart and are never called roles. totals.open_roles is the sum of open_roles over the rows marked role, and totals.paid_research_studies the sum over the rows marked study.
* totals holds the day's numbers as the site's pages state them. roles_that_state_pay counts the roles that state pay in any unit. The median and its quartiles are over every listing that states hourly pay.

Weekly file:

* A week runs Monday to Sunday, UTC. Its numbers are counted on its day of record: its Sunday, or its last day with a build when the Sunday build did not run.
* A role is one listing in a platform's public feed. Copies with the same title and pay on one platform count once.
* A role is new when the ledger first saw it this week on a platform we already tracked, and gone when it was open on the day of record of the week before and not on this one, with its platform's feed read on this one. A role that came back with a new id and the same title and pay is neither.
* A role first seen this week that its platform dated more than 14 days before is an old posting: open, and counted apart, never as new. So is a role first seen on the day the board began to read its platform's feed in full.
* A platform whose feed was not read on the day of record is marked under Platforms. Its roles are not counted as gone, and its count that day is from its last good read.
* Pay is the hourly pay a listing states, a range at its midpoint, a median from 8 roles or more, nothing estimated or converted. $100+ counts the roles whose listed hourly pay reaches $100.
* days_listed_median is explained in the file's own method list.

The site's page on the method is https://trainergigs.com/data-method.

Pay is as each listing states it. Nothing here promises pay, hiring or speed.

## The dated archive

A daily workflow in `.github/workflows/mirror.yml` saves the two daily files and the two weekly files into `data/<YYYY-MM-DD>/`. It saves a file only when it changed since the last saved copy. Each folder is the day the file was fetched, in UTC.

## Terms

The code in this repository is under the MIT license (`LICENSE`). The data is under CC BY 4.0 (`LICENSE-DATA.md`). Credit line:

> Data: TrainerGigs, https://trainergigs.com

Please keep requests modest. The files are cached for 5 minutes, so fetching more often than that returns the same file.

## How to cite

Use `CITATION.cff`, or write:

> TrainerGigs. AI training jobs data. https://trainergigs.com/ai-training-jobs-data.json. Accessed YYYY-MM-DD.

Always give the day. The numbers change every day.

## Contact

hello@trainergigs.com
