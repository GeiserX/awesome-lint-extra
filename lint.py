#!/usr/bin/env python3
"""Awesome list linter with badge validation, format checks, and configurable URL approval."""

import json
import os
import re
import sys
from pathlib import Path

# Default approved git hosting domains
DEFAULT_HOSTS = [
    "github.com",
    "gitlab.com",
    "codeberg.org",
    "gitea.com",
    "sr.ht",
    "bitbucket.org",
    "framagit.org",
    "salsa.debian.org",
    "git.savannah.gnu.org",
    "sourceforge.net",
    "gitee.com",
    "git.sr.ht",
    "git.zx2c4.com",
    "invent.kde.org",
    "gitlab.gnome.org",
    "gitlab.freedesktop.org",
]

# Default badge patterns (shields.io)
BADGE_PATTERNS = {
    "stars": r'\[!\[Stars\]\(https://img\.shields\.io/github/stars/',
    "last-commit": r'\[!\[Last Commit\]\(https://img\.shields\.io/github/last-commit/',
    "language": r'\[!\[Language\]\(https://img\.shields\.io/github/languages/top/',
    "license": r'\[!\[License\]\(https://img\.shields\.io/github/license/',
}

def custom_tag_pattern(color):
    """Build regex for custom tag badges with a specific color."""
    clickable = rf'\[!\[[^\]]+\]\(https://img\.shields\.io/badge/[^)]*{color}[^)]*\)\]\([^)]+\)'
    plain = rf'!\[[^\]]+\]\(https://img\.shields\.io/badge/[^)]*{color}[^)]*\)'
    return clickable, plain


def load_config(readme_dir):
    """Load .awesomerc.json config from the repo root."""
    config_path = Path(readme_dir) / ".awesomerc.json"
    config = {
        "allowed_hosts": DEFAULT_HOSTS,
        "require_badges": False,
        "badge_types": [],
        "require_custom_tags": None,  # hex color string like "003399" to require custom tag badges
        "check_alphabetical": True,
        "check_description_format": True,
        "check_toc": True,
    }
    if config_path.exists():
        with open(config_path) as f:
            user_config = json.load(f)
        config.update(user_config)
    return config


def is_entry_line(line):
    """Check if a line is an awesome list entry (- [Name](url) ...)."""
    return line.startswith("- [") and "](#" not in line and "](" in line


def parse_entry(line):
    """Parse an entry line into components."""
    # Match: - [Name](url) ... - Description.
    m = re.match(r'^- \[([^\]]+)\]\(([^)]+)\)\s+(.+)$', line)
    if not m:
        return None
    name = m.group(1)
    url = m.group(2)
    rest = m.group(3)

    # Find description: everything after the last ` - ` separator
    desc_match = re.search(r' - ([A-Za-z].+)$', rest)
    description = desc_match.group(1) if desc_match else None

    return {"name": name, "url": url, "rest": rest, "description": description}


def check_url_host(url, allowed_hosts):
    """Check if the URL's host is in the allowed list."""
    m = re.match(r'https?://([^/]+)', url)
    if not m:
        return False, f"Invalid URL format: {url}"
    host = m.group(1).lower()
    for allowed in allowed_hosts:
        if host == allowed or host.endswith("." + allowed):
            return True, None
    return False, f"Host '{host}' not in allowed list"


def lint_readme(readme_path, config):
    """Lint the README.md file. Returns list of (line_num, message) errors."""
    errors = []
    with open(readme_path) as f:
        lines = f.readlines()

    current_section = None
    current_subsection = None
    prev_entry_name = None
    seen_urls = {}
    toc_sections = []
    actual_sections = []
    in_toc = False
    in_lint_disable = False

    for i, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")

        # Track lint disable/enable comments
        if "<!--lint disable" in line:
            in_lint_disable = True
        if "<!--lint enable" in line:
            in_lint_disable = False
            continue

        # Track ToC entries
        if in_lint_disable and line.startswith("- [") and "](#" in line:
            m = re.match(r'^- \[([^\]]+)\]\(#', line)
            if m:
                toc_sections.append(m.group(1))
            continue

        # Track sections
        section_match = re.match(r'^## (.+)$', line)
        if section_match:
            current_section = section_match.group(1)
            actual_sections.append(current_section)
            prev_entry_name = None
            continue

        subsection_match = re.match(r'^### (.+)$', line)
        if subsection_match:
            current_subsection = subsection_match.group(1)
            prev_entry_name = None
            continue

        # Check entry lines
        if not is_entry_line(line):
            continue

        entry = parse_entry(line)
        if not entry:
            errors.append((i, "Cannot parse entry format. Expected: - [Name](url) ... - Description."))
            continue

        # Check URL host
        ok, msg = check_url_host(entry["url"], config["allowed_hosts"])
        if not ok:
            errors.append((i, f"[{entry['name']}] {msg}"))

        # Check duplicate URLs
        base_url = entry["url"].rstrip("/")
        if base_url in seen_urls:
            errors.append((i, f"[{entry['name']}] Duplicate URL (first seen at line {seen_urls[base_url]})"))
        else:
            seen_urls[base_url] = i

        # Check description format
        if config["check_description_format"]:
            desc = entry["description"]
            if not desc:
                errors.append((i, f"[{entry['name']}] No description found after ' - '"))
            else:
                if not desc[0].isupper():
                    errors.append((i, f"[{entry['name']}] Description must start with a capital letter"))
                if not desc.endswith("."):
                    errors.append((i, f"[{entry['name']}] Description must end with a period"))
                # Check description doesn't start with project name
                if desc.lower().startswith(entry["name"].lower()):
                    errors.append((i, f"[{entry['name']}] Description should not start with the project name"))

        # Check alphabetical order
        if config["check_alphabetical"] and prev_entry_name:
            if entry["name"].lower() < prev_entry_name.lower():
                errors.append((i, f"[{entry['name']}] Not in alphabetical order (should come before '{prev_entry_name}')"))
        prev_entry_name = entry["name"]

        # Check required badges
        if config["require_badges"]:
            for badge_type in config.get("badge_types", []):
                if badge_type in BADGE_PATTERNS:
                    if not re.search(BADGE_PATTERNS[badge_type], line):
                        errors.append((i, f"[{entry['name']}] Missing required badge: {badge_type}"))

        # Check custom tag badges (e.g., EU regulation tags with color "003399")
        tag_color = config.get("require_custom_tags")
        if tag_color:
            clickable_pat, plain_pat = custom_tag_pattern(tag_color)
            has_tag = re.search(clickable_pat, line) or re.search(plain_pat, line)
            if not has_tag:
                errors.append((i, f"[{entry['name']}] Missing custom tag badge (color: {tag_color})"))

    # Check ToC matches sections
    if config["check_toc"] and toc_sections and actual_sections:
        # Filter out non-content sections (Contributing is typically not in ToC)
        for toc_entry in toc_sections:
            if toc_entry not in actual_sections:
                errors.append((0, f"ToC entry '{toc_entry}' has no matching ## section"))
        for section in actual_sections:
            if section not in toc_sections and section != "Contents":
                # Only warn for content sections, not footer sections
                pass  # Many lists have footer sections not in ToC

    return errors


def main():
    readme_path = os.environ.get("INPUT_README", "README.md")
    if not Path(readme_path).exists():
        print(f"ERROR: {readme_path} not found")
        sys.exit(1)

    readme_dir = str(Path(readme_path).parent)
    config = load_config(readme_dir)

    # Override config with environment variables (for GitHub Action inputs)
    if os.environ.get("INPUT_ALLOWED_HOSTS"):
        config["allowed_hosts"] = json.loads(os.environ["INPUT_ALLOWED_HOSTS"])
    if os.environ.get("INPUT_REQUIRE_BADGES"):
        config["require_badges"] = os.environ["INPUT_REQUIRE_BADGES"].lower() == "true"
    if os.environ.get("INPUT_BADGE_TYPES"):
        config["badge_types"] = json.loads(os.environ["INPUT_BADGE_TYPES"])
    if os.environ.get("INPUT_REQUIRE_CUSTOM_TAGS"):
        config["require_custom_tags"] = os.environ["INPUT_REQUIRE_CUSTOM_TAGS"]
    if os.environ.get("INPUT_CHECK_ALPHABETICAL"):
        config["check_alphabetical"] = os.environ["INPUT_CHECK_ALPHABETICAL"].lower() == "true"

    errors = lint_readme(readme_path, config)

    if errors:
        print(f"Found {len(errors)} error(s):\n")
        for line_num, msg in errors:
            if line_num > 0:
                print(f"  {readme_path}:{line_num}  {msg}")
            else:
                print(f"  {msg}")
        print()
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
