<div align="center">
  <img src="https://raw.githubusercontent.com/GeiserX/awesome-lint-extra/main/docs/images/banner.svg" alt="awesome-lint-extra" width="700">
  <br><br>
  <p>
    <a href="https://pypi.org/project/awesome-lint-extra/"><img src="https://img.shields.io/pypi/v/awesome-lint-extra?style=flat-square" alt="PyPI"></a>
    <a href="https://github.com/GeiserX/awesome-lint-extra/actions/workflows/tests.yml"><img src="https://github.com/GeiserX/awesome-lint-extra/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
    <a href="https://github.com/GeiserX/awesome-lint-extra/blob/main/LICENSE"><img src="https://img.shields.io/github/license/GeiserX/awesome-lint-extra?style=flat-square" alt="License"></a>
    <a href="https://github.com/GeiserX/awesome-lint-extra/releases/latest"><img src="https://img.shields.io/github/v/release/GeiserX/awesome-lint-extra?style=flat-square&label=release" alt="Release"></a>
    <a href="https://codecov.io/gh/GeiserX/awesome-lint-extra"><img src="https://img.shields.io/codecov/c/github/GeiserX/awesome-lint-extra?style=flat-square" alt="Coverage"></a>
  </p>
</div>

---

Command-line linter for [awesome lists](https://github.com/sindresorhus/awesome), also packaged as a GitHub Action. Validates entry format, alphabetical order, badge presence, and URL hosts.

Designed as a complement or replacement for [awesome-lint](https://github.com/sindresorhus/awesome-lint) when your list uses advanced formatting (clickable badges, custom tags, etc.) that the standard linter doesn't support.

## Features

- Entry format: `- [Name](url) ... - Description.`
- Description style: starts with a capital letter, ends with a period, does not repeat the project name.
- Alphabetical order: entries sorted within each section and subsection.
- No duplicate URLs: each project listed once.
- URL host check: only approved git hosting domains (configurable).
- Badge presence: optionally require shields.io badges (stars, last commit, language, license).
- Custom tag badges: require coloured tag badges (for example an EU regulation or a Spanish institution).
- Table of contents: the contents list matches the actual sections.

## Quick start

```bash
pip install awesome-lint-extra
awesome-lint-extra   # run in the folder that holds README.md; exit code 1 on errors
```

As a GitHub Action, after `actions/checkout`:

```yaml
- uses: GeiserX/awesome-lint-extra@v1.1.1
  with:
    require_badges: 'true'
```

The full workflow and running from a checkout without installing are in [Getting started](https://github.com/GeiserX/awesome-lint-extra/blob/main/docs/getting-started.md).

## Documentation

- [Getting started](https://github.com/GeiserX/awesome-lint-extra/blob/main/docs/getting-started.md): pip, the GitHub Action and a checkout.
- [Configuration](https://github.com/GeiserX/awesome-lint-extra/blob/main/docs/configuration.md): `.awesomerc.json` keys and Action inputs.

## License

[GPL-3.0-or-later](https://github.com/GeiserX/awesome-lint-extra/blob/main/LICENSE)
