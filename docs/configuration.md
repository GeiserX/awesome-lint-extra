# Configuration

Create `.awesomerc.json` next to the `README.md` you lint. See
[`.awesomerc.example.json`](https://github.com/GeiserX/awesome-lint-extra/blob/main/.awesomerc.example.json)
for every option.

| Key | Default | What it does |
|---|---|---|
| `allowed_hosts` | the list below | Hosts an entry URL may point at. Setting it replaces the default list. |
| `require_badges` | `false` | Require shields.io badges on every entry. |
| `badge_types` | `[]` | Which badges `require_badges` asks for: `stars`, `last-commit`, `language`, `license`. |
| `require_custom_tags` | `null` | A hex colour such as `"003399"`: every entry needs a shields.io tag badge of that colour. |
| `check_alphabetical` | `true` | Entries sorted within each section and subsection. |
| `check_description_format` | `true` | Every entry has a description that starts with a capital letter, ends with a period and does not start with the project name. |
| `check_toc` | `true` | Every entry in the contents list has a matching `##` section. (A section missing from the contents list is not reported.) |

The GitHub Action inputs `allowed_hosts`, `require_badges`, `badge_types`, `require_custom_tags` and
`check_alphabetical` override the same keys in `.awesomerc.json`, and `readme` sets the file to lint
(default `README.md`). The Action always passes `require_badges` (default `false`) and
`check_alphabetical` (default `true`), so those two come from the Action inputs, not from the file,
when you run it as an Action.

## Allowed hosts

By default the linter accepts URLs from the major git hosting platforms: github.com, gitlab.com,
codeberg.org, gitea.com, sr.ht, bitbucket.org, framagit.org, salsa.debian.org, sourceforge.net, and
more (`DEFAULT_HOSTS` in `lint.py`).

Override the list with the `allowed_hosts` key or Action input:

```yaml
- uses: GeiserX/awesome-lint-extra@v1.1.1
  with:
    allowed_hosts: '["github.com", "gitlab.com", "my-gitea.example.com"]'
```

## Requiring badges

Set `require_badges` to `true` and name the badge types:

```json
{
  "require_badges": true,
  "badge_types": ["stars", "language", "license"]
}
```

Supported badge types: `stars`, `last-commit`, `language`, `license`.

## Custom tag badges

If your list uses coloured tag badges (for example EU regulation tags), require them with a hex colour:

```yaml
- uses: GeiserX/awesome-lint-extra@v1.1.1
  with:
    require_custom_tags: '003399'
```

Or in `.awesomerc.json`:

```json
{
  "require_custom_tags": "003399"
}
```

Each entry then needs at least one shields.io badge with that colour.
