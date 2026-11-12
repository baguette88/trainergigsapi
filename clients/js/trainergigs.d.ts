// Types for the TrainerGigs open data client. A field may be added to a file at any time, so every shape is open.
// Data: TrainerGigs, https://trainergigs.com

export declare const VERSION: string
export declare const BASE: string
export declare const CREDIT: string

/** One open listing in the roles file. */
export interface Role {
  /** The role's key on the site. It stays the same for as long as the role is open. */
  id: string
  /** The role's own page on trainergigs.com, with the tag src=api. Link to it as it is. */
  url: string
  title: string
  platform: string
  /** The board's name for the role's field of work, such as "Law". */
  field: string
  /** "study" is a paid research study. Studies are counted apart and are never called roles. */
  kind: "role" | "study"
  /** The lower end of the listed pay. Null when the listing states no pay, or a top only. */
  pay_min: number | null
  /** The upper end of the listed pay. Null when the listing states no pay, or a bottom only. */
  pay_max: number | null
  pay_unit: "hr" | "task" | "yr" | null
  /** True when the listing gives an hourly figure but says it pays per task. */
  paid_per_task: boolean
  /** The board's short place text, such as "US" or "58 countries". Empty when no country is named. */
  where: string
  /** Two-letter codes of the countries the listing names. Empty when it names none. */
  countries: string[]
  /** The day the platform dated the listing, as YYYY-MM-DD, or null. */
  posted: string | null
  [more: string]: unknown
}

/** The day's numbers, as the site's pages state them. */
export interface Totals {
  open_roles: number
  platforms_with_open_roles: number
  paid_research_studies: number
  roles_that_state_pay: number
  roles_with_hourly_pay: number
  median_listed_hourly_usd: number | null
  q1_listed_hourly_usd: number | null
  q3_listed_hourly_usd: number | null
  [more: string]: unknown
}

export interface RolesFile {
  source: string
  /** The day the roles were counted, as YYYY-MM-DD. */
  counted: string
  license: string
  /** What each role field holds, in plain words. */
  fields: Record<string, string>
  totals: Totals
  roles: Role[]
  [more: string]: unknown
}

/** One row of the daily file: a platform and a field. */
export interface DailyRow {
  platform: string
  field: string
  open_roles: number
  roles_with_hourly_pay: number
  /** Null when fewer than 8 roles state hourly pay. */
  median_listed_hourly_usd: number | null
  posted_last_7_days: number
  countries_named: number
  feed_read: string
  kind: "role" | "study"
  [more: string]: unknown
}

export interface DailyFile {
  name: string
  /** The day of the counts, as YYYY-MM-DD. */
  date: string
  source: string
  method: string[]
  totals: Totals
  fields: string[]
  rows: DailyRow[]
  [more: string]: unknown
}

/** One closed week. The README lists every field. */
export interface Week {
  week: string
  week_start: string
  week_end: string
  last_day: string
  closed_on: string
  roles_sunday: number
  roles_new: number
  roles_gone: number
  median_listed_hourly_usd: number | null
  /** The week's own page on trainergigs.com. */
  url: string
  [more: string]: unknown
}

export interface WeeklyFile {
  name: string
  source: string
  method: string[]
  notes: string[]
  revisions: Array<Record<string, unknown>>
  weeks: Week[]
  [more: string]: unknown
}

export interface Filters {
  /** A two-letter code such as "NG". Anything else throws a RangeError. */
  country?: string | null
  /** With country: also keep the roles whose listing names no country. */
  unnamed?: boolean
  field?: string | null
  platform?: string | null
  /** The least listed hourly pay, a range at its midpoint. */
  minPay?: number | null
  /** A day written as YYYY-MM-DD. Anything else throws a RangeError. */
  since?: string | null
  /** "role" is the default. Null gives roles and studies. */
  kind?: "role" | "study" | null
  /** A roles file you already hold. Without it the live file is fetched. */
  data?: RolesFile
}

export interface PayStats {
  /** How many of the roles state hourly pay with both ends. */
  roles: number
  q1: number | null
  median: number | null
  q3: number | null
}

export declare function rolesFile(base?: string): Promise<RolesFile>
export declare function daily(base?: string): Promise<DailyFile>
export declare function weekly(base?: string): Promise<WeeklyFile>
export declare function roles(filters?: Filters): Promise<Role[]>
export declare function hourlyMidpoint(role: Role): number | null
export declare function byPay(found: Role[]): Role[]
export declare function tally(found: Role[], key: "field" | "platform" | "kind" | "pay_unit" | "countries"): Array<[string, number]>
export declare function payStats(found: Role[]): PayStats
export declare function payText(role: Role): string
export declare function line(role: Role): string
