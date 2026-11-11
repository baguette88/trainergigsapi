// node --test clients/js/trainergigs.test.mjs
import test from "node:test"
import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { roles, hourlyMidpoint } from "./trainergigs.mjs"

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
