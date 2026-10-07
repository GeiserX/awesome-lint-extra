# Getting started

awesome-lint-extra needs Python 3.8 or newer and reads one Markdown file, `README.md` by default. It
prints every error with its line number and exits with 1, or prints `All checks passed.` and exits
with 0.

## From PyPI

```bash
pip install awesome-lint-extra
awesome-lint-extra
```

Run it in the folder that holds the list's `README.md`. To lint another file, set `INPUT_README`:

```bash
INPUT_README=docs/list.md awesome-lint-extra
```

## As a GitHub Action

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: GeiserX/awesome-lint-extra@v1.1.1
        with:
          require_badges: 'true'
          badge_types: '["stars", "last-commit", "language", "license"]'
          check_alphabetical: 'true'
```

Pin a release tag rather than `@main`, so a new check never turns your list red without a change on
your side. The inputs are in [Configuration](configuration.md).

## The PR link check the lists share

`links-changed` is a second action in this repo. On a pull request it runs
[lychee](https://github.com/lycheeverse/lychee) over only the README lines the PR adds or changes, so a
site that is down elsewhere in the list never blocks an unrelated PR. 403 and 429 pass (bot blocks and
rate limits); any other error or timeout fails if it repeats on a second pass a minute later. Hosts that
always block the checker go in the list's own `.lycheeignore`. It needs the full history for the diff:

```yaml
name: links-changed
on:
  pull_request:
    branches: [main]
permissions:
  contents: read
jobs:
  links-changed:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: GeiserX/awesome-lint-extra/links-changed@main
```

The GeiserX lists reference `@main` here on purpose: they belong to the same owner, and a change to the
check should land once, not in twenty pull requests. A list owned by someone else should pin a tag.

## From a checkout, without installing

```bash
git clone https://github.com/GeiserX/awesome-lint-extra.git
cd path/to/your-list
python3 /path/to/awesome-lint-extra/lint.py
```

`lint.py` has no dependencies outside the Python standard library.
