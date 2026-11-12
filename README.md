# AI training jobs API

[![Tests](https://github.com/baguette88/trainergigsapi/actions/workflows/tests.yml/badge.svg)](https://github.com/baguette88/trainergigsapi/actions/workflows/tests.yml)
[![Open roles today](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Ftrainergigs.com%2Fai-training-jobs-data.json&query=%24.totals.open_roles&label=open%20roles%20today&color=1f6feb)](https://trainergigs.com/?src=github)
[![Counted](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Ftrainergigs.com%2Fai-training-jobs-data.json&query=%24.date&label=counted&color=555)](https://trainergigs.com/ai-training-jobs-data.json)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-2ea44f)](LICENSE-DATA.md)
[![Code: MIT](https://img.shields.io/badge/code-MIT-2ea44f)](LICENSE)

Free, read-only data on remote AI training jobs from [TrainerGigs](https://trainergigs.com/?src=github): every open role with its listed pay, field and countries, and the counts by platform for each day and each closed week. No key and no sign-up. Fetch the files, use them, and credit the source.

Looking for the jobs themselves? Search every open role by field, country and listed pay on the board: **[trainergigs.com](https://trainergigs.com/?src=github)**.

<!-- counts:start -->
On Nov 12, 2026 the daily file stated **2,979 open roles on 33 platforms**, and 443 paid research studies, which it counts apart. The median listed pay was $40 an hour, across 2,087 roles that state hourly pay. The middle half list $35.50 to $75.
<!-- counts:end -->

**On this page:** [Quick start](#quick-start) · [Install](#install) · [What you can build](#what-you-can-build) · [The files](#the-files) · [A role](#a-role) · [Filters and commands](#filters-and-commands) · [Recipes](#recipes) · [How the files are served](#how-the-files-are-served) · [Field reference](#field-reference) · [How the numbers are counted](#how-the-numbers-are-counted) · [The dated archive](#the-dated-archive) · [Versions](#versions) · [Terms](#terms)

## Quick start

With nothing to install, the roles whose listings name Nigeria:

```sh
curl -s https://trainergigs.com/ai-training-jobs-roles.json \
  | jq -r '.roles[] | select(.kind == "role" and (.countries | index("NG"))) | [.title, .platform, .url] | @tsv'
```

With the Python client, the same roles that list $20 an hour or more, best paid first:

```sh
git clone https://github.com/baguette88/trainergigsapi && cd trainergigsapi
python3 clients/python/trainergigs.py roles --country NG --min-pay 20 --limit 10
```

It prints the day the roles were counted, how many it found, and one line for each role: the listed pay, the title, the platform and the role's own page.

The same in Python, with the standard library only:

```python
import sys
sys.path.insert(0, "clients/python")
import trainergigs as tg

found = tg.by_pay(tg.roles(country="NG", min_pay=20))
for role in found[:10]:
    print(tg.line(role))
```

And in JavaScript, in Node 18 or newer or in a browser page on any site:

```js
import { roles, byPay, line } from "./clients/js/trainergigs.mjs"

const found = byPay(await roles({ country: "NG", minPay: 20 }))
for (const role of found.slice(0, 10)) console.log(line(role))
```

Every role links to its own page on trainergigs.com. The full listing and the way to apply are there.

## Install

Each client is one file with no dependency, so you can copy it into your project. You can also install from this repository.

Python 3.9 or newer. This adds the module and a `trainergigs` command:

```sh
pip install git+https://github.com/baguette88/trainergigsapi
trainergigs roles --country NG --min-pay 20
```

Node 18 or newer:

```sh
npm install github:baguette88/trainergigsapi
```

```js
import { roles } from "trainergigs"
```

TypeScript and editors read the types in `clients/js/trainergigs.d.ts`, so a role's fields complete as you type.

A browser page, with nothing to install:

```html
<script type="module">
import { roles } from "https://cdn.jsdelivr.net/gh/baguette88/trainergigsapi@v1.5.0/clients/js/trainergigs.mjs"
console.log(await roles({ country: "NG" }))
</script>
```

## What you can build

Three short things, each run against the live file on Nov 12, 2026. The lines under each are what it printed that day. Your numbers will be those of your day. The Python ones need the `pip install` above.

**The roles that name your country.** Kenya here, best paid first:

```sh
trainergigs roles --country KE --limit 3
```

```
Counted on 2026-11-12: 414 found, 3 shown
- $140 to $400/hr | Civil Rights Attorney | micro1 | https://trainergigs.com/job-micro1-2116b175-8be3-49bd-8636-dd3ecef38d70?src=api
- $140 to $400/hr | Consumer Product Safety Attorney | micro1 | https://trainergigs.com/job-micro1-5888d8c4-69df-47b6-8d73-fac94ab909c0?src=api
- $140 to $400/hr | Corporate Attorney (BigLaw Firms) | micro1 | https://trainergigs.com/job-micro1-2f7c4611-a5b1-4e6a-be39-d11c167573a0?src=api
Data: TrainerGigs, https://trainergigs.com
```

**The fields with the highest listed pay today.** The median listed hourly pay of each field, counted as the site counts it:

```python
import trainergigs as tg

data = tg.roles_file()
rows = []
for field, count in tg.tally(tg.roles(data=data), "field"):
    stats = tg.pay_stats(tg.roles(field=field, data=data))
    if stats["median"] is not None:
        rows.append((stats["median"], field, stats["roles"]))
print("Counted on", data["counted"])
for median, field, stated in sorted(rows, reverse=True)[:5]:
    print("$%.2f an hour in %s, across %d roles that state hourly pay" % (median, field, stated))
```

```
Counted on 2026-11-12
$117.50 an hour in Law, across 67 roles that state hourly pay
$84.00 an hour in Applied Engineering, across 63 roles that state hourly pay
$75.00 an hour in Finance, across 102 roles that state hourly pay
$70.00 an hour in Data Analysis, across 21 roles that state hourly pay
$62.50 an hour in Software Engineering, across 277 roles that state hourly pay
```

A field with fewer than 8 roles that state hourly pay has no median and is left out. These are medians of what listings state, not of what anyone was paid.

**The new roles since yesterday, as a Markdown table.** For a README, an issue or a newsletter:

```python
import datetime
import trainergigs as tg

yesterday = (datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)).isoformat()
data = tg.roles_file()
new = tg.by_pay(tg.roles(since=yesterday, data=data))
print(tg.roles_markdown(new, counted=data["counted"]))
```

On Nov 12, 2026 it printed 73 roles their platforms dated Nov 11 or Nov 12. The head of the table, its first two roles and its last line:

```
| Pay | Role | Platform | Field | Posted |
|---|---|---|---|---|
| \$130 to \$140/hr | [Certified Financial Planner (CFP® / CFA)](https://trainergigs.com/job-mercor-list-aaabocs4xiyqlblbntrkf6mm?src=api) | Mercor | Finance | 2026-11-11 |
| \$100 to \$150/hr | [Senior AI Consultant \| Braintrust AI Experts Network (Remote)](https://trainergigs.com/job-braintrust-18128?src=api) | Braintrust | Business & Operations | 2026-11-11 |

Counted on 2026-11-12. Data: [TrainerGigs](https://trainergigs.com/?src=api)
```

A role whose platform gives no date is not in a search by day. The marks in a title are kept as plain text, so a title cannot break the table.

Want the table to write itself each day? See [a daily file in your own repository](#a-daily-file-in-your-own-repository).

## The files

All addresses are on `https://trainergigs.com`. Each is a plain GET.

| Address | Format | What it holds | How often it changes |
|---|---|---|---|
| `/ai-training-jobs-roles.json` | JSON | Every open role, one line each, with its own page on trainergigs.com | With the site build |
| `/ai-training-jobs-data.json` | JSON | Open roles by platform and field, the day's totals, the counting method | With the site build |
| `/ai-training-jobs-data.csv` | CSV | The same rows as the daily JSON | With the site build |
| `/ai-training-jobs-weekly.json` | JSON | Every closed week, with its totals and the counting method | A week is added after it closes |
| `/ai-training-jobs-weekly.csv` | CSV | Every closed week as one long table, with rows by platform and field | A week is added after it closes |
| `/feed.xml` | RSS | The newest roles on the board | With the site build |
| `/feed-weekly.xml` | RSS | One item per closed week | A week is added after it closes |
| `/feed-changes.xml` | RSS | Platforms whose open roles grew, week by week | A week is added after it closes |
| `/sitemap.xml` | XML | Every page on the site | With the site build |
| `/llms.txt` | Text | A plain list of every page, with its number of the day | With the site build |

The site builds about once an hour. To see a file's day, read `date` in the daily file, `counted` in the roles file and `closed_on` on a week.

`openapi.yaml` describes every address and every field for tools that read OpenAPI 3.1.

## A role

One item of `roles` in the roles file, from the saved copy in `tests/samples/`:

```json
{
  "id": "job-lionbridge-27259005-4bd4-4767-b4e3-bff478b57cab",
  "url": "https://trainergigs.com/job-lionbridge-27259005-4bd4-4767-b4e3-bff478b57cab?src=api",
  "title": "US English Transcriber",
  "platform": "Lionbridge",
  "field": "Language & Audio",
  "kind": "role",
  "pay_min": 25,
  "pay_max": 34,
  "pay_unit": "hr",
  "paid_per_task": false,
  "where": "US",
  "countries": ["US"],
  "posted": "2026-04-13"
}
```

Link each role to its `url` as it is. The tag on it tells the site that the visit came through this data, which is how the data stays free.

## Filters and commands

Both clients take the same filters. Every one may be left out.

| Filter | Command line | Python | JavaScript | What it keeps |
|---|---|---|---|---|
| Country | `--country NG` | `country="NG"` | `country: "NG"` | Roles whose listing names that country, by its two-letter code |
| No country named | `--unnamed` | `unnamed=True` | `unnamed: true` | With a country: also the roles whose listing names no country |
| Field | `--field Law` | `field="Law"` | `field: "Law"` | Roles in that field of work |
| Platform | `--platform Appen` | `platform="Appen"` | `platform: "Appen"` | Roles that platform lists |
| Least pay | `--min-pay 40` | `min_pay=40` | `minPay: 40` | Roles whose listed hourly pay, a range at its midpoint, is at least that |
| Day | `--since 2026-11-01` | `since="2026-11-01"` | `since: "2026-11-01"` | Roles their platform dated on or after that day |
| Studies | `--studies` | `kind="study"` | `kind: "study"` | Paid research studies in place of roles |

A role whose listing names no country is left out of a country search unless you ask for it. Case does not matter in a field or a platform name.

A filter that could never match is an error and not an empty answer. A country must be a two-letter code and a day must be written `2026-11-01`: anything else raises `ValueError` in Python and throws a `RangeError` in JavaScript. The command line also checks the names:

```
$ trainergigs roles --field Legal
No field is named "Legal" in the file of 2026-11-12.
Close to it: Law
The fields: AI & Machine Learning, Applied Engineering, Arts & Design, ...
```

A real name with no role that day still answers "0 found".

The field names in the file on Nov 12, 2026:

<!-- fields:start -->
`AI & Machine Learning`, `Applied Engineering`, `Arts & Design`, `Business & Operations`, `Cybersecurity`, `Data Analysis`, `Education`, `Finance`, `Generalist`, `Humanities`, `Language & Audio`, `Law`, `Medicine`, `Other`, `Research Studies`, `Retail & Hospitality`, `Robotics`, `Science & Research`, `Software Engineering`
<!-- fields:end -->

The command line prints the names of the day, with the count under each. Every filter works with every command but `totals`.

| Command | What it prints |
|---|---|
| `trainergigs.py roles` | The roles, best paid first. `--limit 0` shows all of them |
| `trainergigs.py totals` | The day's numbers as the file states them |
| `trainergigs.py fields` | Each field of work and how many roles are in it |
| `trainergigs.py platforms` | Each platform and how many roles it lists |
| `trainergigs.py countries` | Each country code and how many listings name it |
| `trainergigs.py pay` | The median listed hourly pay and its middle half, counted as the site counts them |

So `python3 clients/python/trainergigs.py pay --country KE --field Law` gives the median listed hourly pay of the law roles whose listings name Kenya, or says that fewer than 8 of them state hourly pay. Add `--json` to any command to get data in place of lines. Add `--csv` to `roles`, `fields`, `platforms` or `countries` to get a table for a spreadsheet, or `--md` to get a Markdown table with each role linked to its page.

In code the same counts are `tally` and `pay_stats` in Python, and `tally` and `payStats` in JavaScript. `roles_csv` and `roles_markdown` in Python write the two tables.

## Recipes

### A daily file in your own repository

This repository is also a GitHub Action. One step writes `roles.md`, a table of the open roles for your country or field that GitHub shows as a page, and `roles.csv`, the same roles for a spreadsheet:

```yaml
- uses: baguette88/trainergigsapi@v1.5.0
  with:
    country: "NG"
    min-pay: "20"
```

To see what it writes, open [examples/roles-100.md](examples/roles-100.md): the open roles whose listed hourly pay, a range at its midpoint, is $100 or more, best paid first. This step writes it again each day.

`examples/daily-roles.yml` is the whole workflow around that step. It runs each day and commits the two files only when they changed, so their history is a record of what opened and closed.

1. Copy `examples/daily-roles.yml` into the folder `.github/workflows/` of your repository.
2. Set `country`, `field` and `min-pay` in the file. Leave one empty to leave that filter out. Set at least one: the table of every role was about 530 KB on Nov 12, 2026, which is long for one page.
3. Push. To try it at once, open the Actions tab, pick "Daily AI training roles" and press "Run workflow".

It needs no key and no secret, and it installs nothing. The client names itself in its `User-Agent`, so the site answers it. It needs `bash` and `python3`, which the Linux and macOS runners have. It is tested on the Linux runner with each push.

| Input | What it takes | Without it |
|---|---|---|
| `country` | A two-letter code such as `NG` | Every country |
| `field` | A field as the file names it, such as `Law` | Every field |
| `min-pay` | The least listed hourly pay in US dollars, a range at its midpoint | Every role |
| `since` | A day such as `2026-11-01` | Every day |
| `markdown` | Where to write the table | `roles.md` |
| `csv` | Where to write the CSV | `roles.csv` |

The step's output `found` is the number of roles in the table. A filter that could never match stops the step, and the files of the day before stay as they were.

### pandas

```python
import pandas as pd

who = {"User-Agent": "my-project/1.0"}
rows = pd.read_csv("https://trainergigs.com/ai-training-jobs-data.csv", storage_options=who)
```

Keep the `storage_options` line. pandas reads through Python's urllib, and the site refuses urllib's default User-Agent with a 403. `examples/pandas_example.py` goes on to the median listed pay of each field.

### Google Sheets

```
=IMPORTDATA("https://trainergigs.com/ai-training-jobs-data.csv")
```

The roles themselves, as a table to open in Sheets or Excel:

```sh
trainergigs roles --country NG --limit 0 --csv > roles.csv
```

Each row has the pay in the listing's words, the title, the platform, the field, the countries and the role's own page on trainergigs.com in `url`. A title that begins like a formula is kept as text.

### A web page

`examples/roles_page.html` is one file that lists the roles for a country on your own page, best paid first. It reads the roles file with `fetch`, and it needs no key and no build step.

No code at all? The site makes a ready widget for the whole board, a field or a country: [trainergigs.com/jobs-widget](https://trainergigs.com/jobs-widget?src=github).

### A Discord channel

`examples/discord_new_roles.py` posts the roles that are new since its last run through a webhook, and remembers what it posted. Run it once a day.

### Curl

```sh
curl -s https://trainergigs.com/ai-training-jobs-data.json | jq .totals
curl -s https://trainergigs.com/ai-training-jobs-weekly.csv -o weekly.csv
```

`examples/example.py` and `examples/example.mjs` print the day's totals in Python and in Node. `examples/example.sh` saves the daily and weekly files with curl.

## How the files are served

* **No key.** Nothing to sign up for, and nothing to send but a GET.
* **Name your program.** Send a `User-Agent` header that says what is asking. On Nov 12, 2026 the site refused the default one of Python's urllib (`Python-urllib`) with a 403, which is also what a plain `pandas.read_csv` sends. Curl, Node, browsers, `requests` and the clients here all get the file as they are.
* **Five minutes.** A CDN caches each file for 5 minutes, so fetching more often than that returns the same file.
* **Gzip.** Ask with `Accept-Encoding: gzip` and the roles file is about 150 KB in place of 1.5 MB. Curl does this with `--compressed`. Browsers, Node and the Python client here do it by themselves.
* **Not changed.** A request with `If-Modified-Since` gets a 304 and no body when the file is the same.
* **Any site.** The files send `Access-Control-Allow-Origin: *`, so a web page on any site can read them with `fetch`.

Please keep requests modest. Once an hour is as fresh as the data gets.

## Field reference

Every field below was read from the live files on Nov 12, 2026. `tests/test_docs.py` fails when a field in the saved files is missing from this page or from `openapi.yaml`.

### Roles file: `ai-training-jobs-roles.json`

Top level: `source`, `counted`, `license`, `fields`, `totals`, `roles`.

* `counted` is the day the roles were counted.
* `fields` says in plain words what each role field holds.
* `totals` holds the same numbers as `totals` in the daily file.
* `roles` is sorted by platform, then title, then address.

Each item in `roles`:

| Field | Meaning |
|---|---|
| `id` | The role's key on the site, the last part of its address. It stays the same for as long as the role is open |
| `url` | The role's own page on trainergigs.com, with the tag `src=api`. Link to it as it is |
| `title` | The listing's title |
| `platform` | The platform that lists the role |
| `field` | The board's name for the role's field of work |
| `kind` | `role`, or `study` for a paid research study. Studies are counted apart and are never called roles |
| `pay_min` | The lower end of the listed pay as a number. Null when the listing states no pay, and when it states a top only ("Up to $90/hr") |
| `pay_max` | The upper end of the listed pay as a number. Null when the listing states no pay, and when it states a bottom only. One rate is both ends |
| `pay_unit` | `hr`, `task` or `yr`, or null when the listing states no pay |
| `paid_per_task` | True when the listing gives an hourly figure but says it pays per task, otherwise false |
| `where` | The board's short place text, such as "US" or "58 countries". Empty when no country is named |
| `countries` | The two-letter codes of the countries the listing names for applicants, in its order. Empty when it names none |
| `posted` | The day the platform itself dated the listing, or null when it gives none |

The rows marked `role` add up to `totals.open_roles`. The rows marked `study` add up to `totals.paid_research_studies`. The file holds no apply address and no description. Link to a role through its `url`.

Pay in words: `pay_text` in Python and `payText` in JavaScript write a role's pay as its listing states it, so a top with no bottom reads "Up to $90/hr" and never "$90/hr".

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

Top level: `name`, `source`, `method`, `notes`, `revisions`, `weeks`.

How to read a week, from the file's own notes and method:

* A week runs Monday to Sunday, UTC. `last_day` is its day of record.
* `open_sunday`, `open_prev_sunday`, `new_roles` and `gone_roles` count every listing, paid research studies among them.
* `roles_sunday`, `roles_prev_sunday`, `roles_new` and `roles_gone` are the same counts with the research studies left out.
* `renewed_new` and `renewed_gone` count ids that are the same role as one gone or new. They are neither new nor gone.
* `roles_100_plus` counts roles whose listed hourly pay reaches $100.
* `url` is the week's own page on trainergigs.com.

<details>
<summary>Every field of a week, and every column of the weekly CSV</summary>

Each item in `weeks` has these fields:

`week`, `week_start`, `week_end`, `last_day`, `days_counted`, `days_missing`, `closed_on`, `revised`, `open_sunday`, `open_prev_sunday`, `studies_sunday`, `listed_any_day`, `new_roles`, `renewed_new`, `gone_roles`, `renewed_gone`, `newly_tracked`, `old_postings`, `roles_100_plus`, `roles_100_plus_prev`, `roles_with_hourly_pay`, `median_listed_hourly_usd`, `q1_listed_hourly_usd`, `q3_listed_hourly_usd`, `platforms_read`, `feeds_not_read`, `languages_named`, `countries_named`, `days_listed_median`, `days_listed_n`, `roles_sunday`, `roles_prev_sunday`, `roles_new`, `roles_gone`, `platforms_with_roles`, `url`.

The weekly CSV (`ai-training-jobs-weekly.csv`) has one row per week, platform and field. Its columns are:

`week`, `week_start`, `week_end`, `last_day`, `days_counted`, `closed_on`, `revised`, `platform`, `field`, `open_sunday`, `open_prev_sunday`, `listed_any_day`, `new_roles`, `gone_roles`, `renewed`, `newly_tracked`, `old_postings`, `roles_100_plus`, `roles_with_hourly_pay`, `median_listed_hourly_usd`, `q1_listed_hourly_usd`, `q3_listed_hourly_usd`, `platforms_read`, `feeds_not_read`, `languages_named`, `countries_named`, `days_listed_median`, `days_listed_n`.

Platform and field are blank on the week's total row. Field is blank on a platform's row. Platform is blank on a field's row. The week's own numbers, from `platforms_read` to `days_listed_n`, are on its total row only.

</details>

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

You can count the day's median again from the roles file. Take the rows marked `role` whose `pay_unit` is `hr`, whose `paid_per_task` is false and whose listing states both ends, and count each at its midpoint. That gives `roles_with_hourly_pay` and the median and quartiles in `totals`. `pay_stats` in the Python client does it, and `tools/check_live.py` checks it against the live files each day.

The site's page on the method is https://trainergigs.com/data-method.

Pay is as each listing states it. Nothing here promises pay, hiring or speed.

## The dated archive

A daily workflow in `.github/workflows/mirror.yml` saves the two daily files and the two weekly files into `data/<YYYY-MM-DD>/`. It saves a file only when it changed since the last saved copy. Each folder is the day the file was fetched, in UTC. The first folder is `data/2026-11-12`.

The same workflow writes the day's numbers into the paragraph near the top of this page and the table in `examples/roles-100.md`, and then runs `tools/check_live.py`, which fails when a documented field is gone from a live file or the files stop adding up.

## Versions

`CHANGELOG.md` lists every change. `CONTRIBUTING.md` says how to report a problem or send a fix. A field may be added to a file at any time. A field is never taken away without a new major version, so read the fields you know and pass over the rest.

To test the clients against the saved files in `tests/samples/`, with nothing fetched:

```sh
python3 -m unittest discover -s clients/python
python3 -m unittest discover -s tests
node --test clients/js/trainergigs.test.mjs
```

The roles sample is a cut of 24 rows. The other samples are whole files.

## Terms

The code in this repository is under the MIT license (`LICENSE`). The data is under CC BY 4.0 (`LICENSE-DATA.md`). Credit line:

> Data: TrainerGigs, https://trainergigs.com

## How to cite

Use `CITATION.cff`, or write:

> TrainerGigs. AI training jobs data. https://trainergigs.com/ai-training-jobs-data.json. Accessed YYYY-MM-DD.

Always give the day. The numbers change every day.

## Contact

hello@trainergigs.com
