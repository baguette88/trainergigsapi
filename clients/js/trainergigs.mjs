// A small client for the TrainerGigs open data. No dependency. Node 18 or newer, and a browser page on any site.
// Data: TrainerGigs, https://trainergigs.com
export const BASE = "https://trainergigs.com"

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
export async function roles({ country, unnamed = false, field, platform, minPay, since, kind = "role", data } = {}) {
  const file = data ?? await rolesFile()
  const code = country ? country.toUpperCase() : null
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
