// A small client for the TrainerGigs open data. No dependency. Node 18 or newer, and a browser page on any site.
// Data: TrainerGigs, https://trainergigs.com
export const VERSION = "1.5.0"
export const BASE = "https://trainergigs.com"
export const CREDIT = "Data: TrainerGigs, https://trainergigs.com"

async function get(path, base = BASE) {
  const res = await fetch(base + path)
  if (!res.ok) throw new Error("HTTP " + res.status + " for " + path)
  return res
}

// The roles file: source, counted, license, fields, totals and roles.
export async function rolesFile(base = BASE) {
  return (await get("/ai-training-jobs-roles.json", base)).json()
}

// The daily file: open roles by platform and field, the day's totals and how they are counted.
export async function daily(base = BASE) {
  return (await get("/ai-training-jobs-data.json", base)).json()
}

// Every closed week, with a total row and rows by platform and field.
export async function weekly(base = BASE) {
  return (await get("/ai-training-jobs-weekly.json", base)).json()
}

// The listed hourly pay of a role, a range at its midpoint, or null. Only roles whose pay_unit is "hr" count.
// A listing that states one end only ("Up to $90/hr") counts at that end. payText says which end it is.
export function hourlyMidpoint(role) {
  if (role.pay_unit !== "hr") return null
  let low = role.pay_min, high = role.pay_max
  if (low == null && high == null) return null
  if (low == null) low = high
  if (high == null) high = low
  return (low + high) / 2
}

// Open roles, filtered. Every option may be left out.
//   country: a two-letter code such as "NG". Keeps the roles whose listing names that country.
//   unnamed: with country, also keeps the roles whose listing names no country at all.
//   field, platform: names as the file gives them (case does not matter).
//   minPay: the least listed hourly pay, a range at its midpoint.
//   since: a day such as "2026-11-01". Keeps the roles their platform dated on or after it.
//   kind: "role" (the default), "study", or null for both.
//   data: a roles file you already hold. Without it the live file is fetched.
// A country that is not a two-letter code, or a day that is not written YYYY-MM-DD, throws a RangeError. Either
// would match nothing, and an empty answer would look like a day with no such roles.
export async function roles({ country, unnamed = false, field, platform, minPay, since, kind = "role", data } = {}) {
  const code = country ? String(country).trim().toUpperCase() : null
  if (code && !/^[A-Z]{2}$/.test(code)) {
    throw new RangeError('country takes a two-letter code such as "NG" for Nigeria, not "' + country + '"')
  }
  if (since && !/^\d{4}-\d{2}-\d{2}$/.test(String(since))) {
    throw new RangeError('since takes a day written as "2026-11-01", not "' + since + '"')
  }
  const file = data ?? await rolesFile()
  return file.roles.filter(role => {
    if (kind && role.kind !== kind) return false
    if (field && field.toLowerCase() !== role.field.toLowerCase()) return false
    if (platform && platform.toLowerCase() !== role.platform.toLowerCase()) return false
    if (minPay != null) {
      const mid = hourlyMidpoint(role)
      if (mid == null || mid < minPay) return false
    }
    if (code) {
      const named = role.countries ?? []
      if (!named.includes(code) && !(unnamed && named.length === 0)) return false
    }
    if (since && !((role.posted ?? "") >= since)) return false
    return true
  })
}

// The same roles, best paid by the hour first. Roles with no listed hourly pay come last, in the order given.
export function byPay(found) {
  return [...found].sort((a, b) => (hourlyMidpoint(b) ?? 0) - (hourlyMidpoint(a) ?? 0))
}

// How many of the roles fall under each value of one field, most first: [["Law", 91], ...].
//   key: "field", "platform", "kind", "pay_unit" or "countries" (a role counts once under each country it names).
export function tally(found, key) {
  const counts = new Map()
  for (const role of found) {
    const value = role[key]
    for (const one of Array.isArray(value) ? value : [value]) {
      if (one != null) counts.set(one, (counts.get(one) ?? 0) + 1)
    }
  }
  return [...counts].sort((a, b) => b[1] - a[1] || (String(a[0]) < String(b[0]) ? -1 : 1))
}

function share(values, part) {
  const spot = (values.length - 1) * part
  const at = Math.floor(spot)
  const after = Math.min(at + 1, values.length - 1)
  return values[at] + (values[after] - values[at]) * (spot - at)
}

// The listed hourly pay of a set of roles, counted as the site counts it: { roles, q1, median, q3 }.
// A role counts when its unit is "hr", its listing states both ends (one rate is both ends) and it does not say it
// pays per task. A range counts at its midpoint. q1, median and q3 are null when fewer than 8 roles count, as on
// the site. Over every row marked role this gives the numbers in the file's own totals.
export function payStats(found) {
  const mids = found
    .filter(r => r.pay_unit === "hr" && !r.paid_per_task && r.pay_min != null && r.pay_max != null)
    .map(r => (r.pay_min + r.pay_max) / 2)
    .sort((a, b) => a - b)
  if (mids.length < 8) return { roles: mids.length, q1: null, median: null, q3: null }
  return { roles: mids.length, q1: share(mids, 0.25), median: share(mids, 0.5), q3: share(mids, 0.75) }
}

// Dollars as the site writes them: $40, $35.50, $130,000.
function money(x) {
  const words = x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return "$" + (words.endsWith(".00") ? words.slice(0, -3) : words)
}

// The listed pay as the listing states it: "$40 to $60/hr", "Up to $90/hr", "From $25/hr" or "pay not listed".
export function payText(role) {
  const low = role.pay_min, high = role.pay_max, unit = role.pay_unit
  if (!unit || (low == null && high == null)) return "pay not listed"
  let words
  if (low == null) words = "Up to " + money(high)
  else if (high == null) words = "From " + money(low)
  else if (low === high) words = money(low)
  else words = money(low) + " to " + money(high)
  return words + "/" + unit + (role.paid_per_task ? ", paid per task" : "")
}

// One role on one line: its pay, title, platform and page.
export function line(role) {
  return [payText(role), role.title, role.platform, role.url].join(" | ")
}
