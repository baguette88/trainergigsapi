# Changes

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
