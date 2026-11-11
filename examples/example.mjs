// Print the day's totals from the TrainerGigs daily file.
// Runs in Node 18 or newer. A browser page on another site cannot fetch the file yet,
// because the site does not send an Access-Control-Allow-Origin header today.
// Data: TrainerGigs, https://trainergigs.com
const res = await fetch("https://trainergigs.com/ai-training-jobs-data.json")
if (!res.ok) throw new Error("HTTP " + res.status)
const data = await res.json()
const t = data.totals
console.log("Counted on", data.date)
console.log(t.open_roles, "open roles on", t.platforms_with_open_roles, "platforms")
console.log("Median listed hourly pay (USD):", t.median_listed_hourly_usd)
