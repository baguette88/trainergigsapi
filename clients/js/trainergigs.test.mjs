// node --test clients/js/trainergigs.test.mjs
import test from "node:test"
import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { roles, hourlyMidpoint, byPay, tally, payStats, payText, line, VERSION } from "./trainergigs.mjs"

const data = JSON.parse(await readFile(new URL("../../tests/samples/ai-training-jobs-roles.json", import.meta.url)))

test("every sample role has an id, a tagged page on the site and a list of countries", () => {
  for (const r of data.roles) {
    assert.equal(r.url, "https://trainergigs.com/" + r.id + "?src=api")
    assert.ok(Array.isArray(r.countries))
  }
})

test("roles are the default kind and studies are counted apart", async () => {
  const found = await roles({ data })
  assert.ok(found.length > 0)
  assert.ok(found.every(r => r.kind === "role"))
  assert.equal((await roles({ data, kind: null })).length, data.roles.length)
})

test("a country keeps the roles that name it, and unnamed adds the roles that name none", async () => {
  const code = data.roles.find(r => r.countries.length > 0).countries[0]
  const named = await roles({ data, country: code.toLowerCase(), kind: null })
  assert.ok(named.length > 0)
  assert.ok(named.every(r => r.countries.includes(code)))
  const wider = await roles({ data, country: code, unnamed: true, kind: null })
  assert.equal(wider.length, named.length + data.roles.filter(r => r.countries.length === 0).length)
})

test("the least pay is read at the midpoint of a listed hourly range", async () => {
  assert.equal(hourlyMidpoint({ pay_unit: "hr", pay_min: 40, pay_max: 60 }), 50)
  assert.equal(hourlyMidpoint({ pay_unit: "yr", pay_min: 90000, pay_max: 120000 }), null)
  assert.equal(hourlyMidpoint({ pay_unit: "hr", pay_min: null, pay_max: null }), null)
  const found = await roles({ data, minPay: 50, kind: null })
  assert.ok(found.every(r => hourlyMidpoint(r) >= 50))
})

test("since keeps the roles dated on or after a day and drops the undated", async () => {
  const days = data.roles.map(r => r.posted).filter(Boolean).sort()
  const day = days[Math.floor(days.length / 2)]
  const found = await roles({ data, since: day, kind: null })
  assert.ok(found.length > 0)
  assert.ok(found.every(r => r.posted >= day))
})

test("a country or a day that could never match throws, and is not answered with nothing", async () => {
  await assert.rejects(roles({ data, country: "Nigeria" }), /two-letter code such as "NG".*not "Nigeria"/)
  await assert.rejects(roles({ data, since: "11/01/2026" }), RangeError)
  assert.deepEqual(await roles({ data, country: " ng " }), await roles({ data, country: "NG" }))
})

test("pay keeps the listing's own words", () => {
  assert.equal(payText({ pay_min: 40, pay_max: 60, pay_unit: "hr" }), "$40 to $60/hr")
  assert.equal(payText({ pay_min: 47.5, pay_max: 47.5, pay_unit: "hr", paid_per_task: true }), "$47.50/hr, paid per task")
  assert.equal(payText({ pay_min: null, pay_max: 90, pay_unit: "hr" }), "Up to $90/hr")
  assert.equal(payText({ pay_min: 25, pay_max: null, pay_unit: "hr" }), "From $25/hr")
  assert.equal(payText({ pay_min: 130000, pay_max: 180000, pay_unit: "yr" }), "$130,000 to $180,000/yr")
  assert.equal(payText({ pay_min: 0.01, pay_max: 0.01, pay_unit: "task" }), "$0.01/task")
  assert.equal(payText({ pay_min: null, pay_max: null, pay_unit: null }), "pay not listed")
  const r = data.roles[0]
  assert.equal(line(r), [payText(r), r.title, r.platform, r.url].join(" | "))
})

test("best paid first, and the rest in their order", () => {
  const a = { id: "a", pay_unit: null }, b = { id: "b", pay_unit: "hr", pay_min: 20, pay_max: 30 }
  const c = { id: "c", pay_unit: "hr", pay_min: 60, pay_max: 60 }, d = { id: "d", pay_unit: "task", pay_min: 500, pay_max: 500 }
  const given = [a, b, c, d]
  assert.deepEqual(byPay(given).map(r => r.id), ["c", "b", "a", "d"])
  assert.deepEqual(given.map(r => r.id), ["a", "b", "c", "d"])
})

test("counts under each name", async () => {
  const everything = await roles({ data, kind: null })
  const fields = tally(everything, "field")
  assert.equal(fields.reduce((sum, [, n]) => sum + n, 0), everything.length)
  assert.deepEqual(fields.map(([, n]) => n), fields.map(([, n]) => n).sort((x, y) => y - x))
  const countries = new Map(tally(everything, "countries"))
  assert.equal(countries.get("NG"), (await roles({ data, country: "NG", kind: null })).length)
})

test("the median is counted as the site counts it", () => {
  const hourly = (low, high, more = {}) => ({ pay_unit: "hr", pay_min: low, pay_max: high, ...more })
  const eight = [10, 20, 30, 40, 50, 60, 70, 80].map(x => hourly(x, x))
  assert.deepEqual(payStats(eight), { roles: 8, q1: 27.5, median: 45, q3: 62.5 })
  assert.deepEqual(payStats(eight.slice(0, 7)), { roles: 7, q1: null, median: null, q3: null })
  const leftOut = [hourly(900, 900, { paid_per_task: true }), hourly(null, 900), { pay_unit: "yr", pay_min: 9e4, pay_max: 9e4 }, { pay_unit: null }]
  assert.deepEqual(payStats([...eight, ...leftOut]), payStats(eight))
  assert.equal(payStats(Array(8).fill(hourly(40, 60))).median, 50)
})

test("the client states its version", () => {
  assert.match(VERSION, /^\d+\.\d+\.\d+$/)
})
