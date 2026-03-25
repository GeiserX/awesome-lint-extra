<div align="center">
  <h1>awesome-lint-extra</h1>
  <p><strong>A strict, configurable linter for awesome lists with badge validation</strong></p>
  <p>
    <a href="https://github.com/GeiserX/awesome-lint-extra/actions"><img src="https://img.shields.io/github/actions/workflow/status/GeiserX/awesome-lint-extra/ci.yml?style=flat-square&label=CI" alt="CI"></a>
    <a href="https://github.com/GeiserX/awesome-lint-extra/blob/main/LICENSE"><img src="https://img.shields.io/github/license/GeiserX/awesome-lint-extra?style=flat-square" alt="License"></a>
    <a href="https://github.com/GeiserX/awesome-lint-extra/releases"><img src="https://img.shields.io/github/v/release/GeiserX/awesome-lint-extra?style=flat-square" alt="Release"></a>
  </p>
</div>

---

Custom linter for [awesome lists](https://github.com/sindresorhus/awesome). Validates entry format, alphabetical order, badge presence, and URL hosts.

Designed as a complement or replacement for [awesome-lint](https://github.com/sindresorhus/awesome-lint) when your list uses advanced formatting (clickable badges, custom tags, etc.) that the standard linter doesn't support.

## Checks

- **Entry format** — `- [Name](url) ... - Description.`
- **Description style** — starts with capital letter, ends with period, doesn't repeat the project name
- **Alphabetical order** — entries sorted within each section/subsection
- **No duplicate URLs** — each project listed only once
- **URL host validation** — only approved git hosting domains (configurable)
- **Badge presence** — optionally require shields.io badges (stars, language, license, etc.)
- **Custom tag badges** — require colored tag badges (e.g. EU regulation, Spanish institution)
- **ToC consistency** — table of contents matches actual sections

## Usage as GitHub Action

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
      - uses: actions/checkout@v4
      - uses: GeiserX/awesome-lint-extra@main
        with:
          require_badges: 'true'
          badge_types: '["stars", "last-commit", "language", "license"]'
          check_alphabetical: 'true'
```

## Usage locally

```bash
python3 lint.py
```

## Configuration

Create `.awesomerc.json` in your repo root to configure checks. See [`.awesomerc.example.json`](.awesomerc.example.json) for all options.

### Allowed hosts

By default, the linter accepts URLs from major git hosting platforms:

- github.com, gitlab.com, codeberg.org, gitea.com, sr.ht, bitbucket.org, framagit.org, salsa.debian.org, sourceforge.net, and more

Override with the `allowed_hosts` config option or action input:

```yaml
- uses: GeiserX/awesome-lint-extra@main
  with:
    allowed_hosts: '["github.com", "gitlab.com", "my-gitea.example.com"]'
```

### Requiring badges

Set `require_badges: true` and specify which badge types are required:

```json
{
  "require_badges": true,
  "badge_types": ["stars", "language", "license"]
}
```

Supported badge types: `stars`, `last-commit`, `language`, `license`.

### Custom tag badges

If your list uses colored tag badges (e.g., EU regulation tags), you can require them by specifying a hex color:

```yaml
- uses: GeiserX/awesome-lint-extra@main
  with:
    require_custom_tags: '003399'
```

Or in `.awesomerc.json`:

```json
{
  "require_custom_tags": "003399"
}
```

This checks that each entry has at least one shields.io badge with the specified color.

## License

[GPL-3.0](LICENSE)
