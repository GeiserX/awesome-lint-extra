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

## From a checkout, without installing

```bash
git clone https://github.com/GeiserX/awesome-lint-extra.git
cd path/to/your-list
python3 /path/to/awesome-lint-extra/lint.py
```

`lint.py` has no dependencies outside the Python standard library.
