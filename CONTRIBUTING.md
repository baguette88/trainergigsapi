# Contributing

Thank you for looking. This project is small on purpose: two clients with no dependency, the documents, and the tests that hold them together.

## A problem with the data

A wrong number, a role in the wrong field or a missing platform is a matter for the site and not for this code. Write to hello@trainergigs.com, or open an issue here with the role's `id` and the day in `counted`.

## A problem with the code or the documents

Open an issue with the command or the lines you ran, what you expected and what you got. A fix is welcome as a pull request. Please keep to these:

- No new dependency. The Python client uses the standard library only, and the JavaScript client uses `fetch` only.
- A change in behavior comes with a test and a line in `CHANGELOG.md`.
- A field named in the README is also in `openapi.yaml`. `tests/test_docs.py` checks it.
- Nothing in the text promises pay or work. Pay is always as the listing states.

## Run the tests

Nothing is fetched. They read the saved files in `tests/samples/`.

```sh
python3 -m unittest discover -s clients/python
python3 -m unittest discover -s tests
node --test clients/js/trainergigs.test.mjs
```

`python3 tools/check_live.py` reads the live files and checks them against the documents.
