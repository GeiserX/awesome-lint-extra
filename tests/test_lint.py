"""Tests for awesome-lint-extra lint.py"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lint import (
    is_entry_line,
    parse_entry,
    check_url_host,
    custom_tag_pattern,
    load_config,
    lint_readme,
    DEFAULT_HOSTS,
)


class TestIsEntryLine:
    def test_valid_entry(self):
        assert is_entry_line("- [Project](https://github.com/user/repo) - Description.")

    def test_toc_entry_excluded(self):
        assert not is_entry_line("- [Section](#section)")

    def test_plain_text(self):
        assert not is_entry_line("Some random text")

    def test_header(self):
        assert not is_entry_line("## Section Header")

    def test_empty_line(self):
        assert not is_entry_line("")

    def test_bullet_without_link(self):
        assert not is_entry_line("- Just a bullet point")


class TestParseEntry:
    def test_entry_with_badge_and_description(self):
        """The linter expects badges between URL and description separator."""
        line = "- [MyProject](https://github.com/user/repo) [![Stars](https://img.shields.io/github/stars/user/repo)](https://github.com/user/repo) - A great project."
        result = parse_entry(line)
        assert result is not None
        assert result["name"] == "MyProject"
        assert result["url"] == "https://github.com/user/repo"
        assert result["description"] == "A great project."

    def test_simple_entry_no_badges(self):
        """Simple entries without badges: rest starts with '- ...' so desc regex won't match."""
        line = "- [MyProject](https://github.com/user/repo) - A great project."
        result = parse_entry(line)
        assert result is not None
        assert result["name"] == "MyProject"
        assert result["url"] == "https://github.com/user/repo"
        # Description is None because rest='- A great project.' has no ' - ' with preceding content
        assert result["description"] is None

    def test_entry_with_multiple_badges(self):
        line = "- [Tool](https://github.com/u/t) [![Stars](https://img.shields.io/github/stars/u/t)](https://github.com/u/t) [![License](https://img.shields.io/github/license/u/t)](https://github.com/u/t) - Does things."
        result = parse_entry(line)
        assert result is not None
        assert result["name"] == "Tool"
        assert result["url"] == "https://github.com/u/t"
        assert result["description"] == "Does things."

    def test_malformed_entry(self):
        result = parse_entry("- [Broken")
        assert result is None

    def test_entry_no_description_separator(self):
        line = "- [Name](https://github.com/x/y) [![B](https://img.shields.io/badge/x)](link) no separator here"
        result = parse_entry(line)
        assert result is not None
        assert result["description"] is None


class TestCheckUrlHost:
    def test_github_allowed(self):
        ok, msg = check_url_host("https://github.com/user/repo", DEFAULT_HOSTS)
        assert ok is True
        assert msg is None

    def test_gitlab_allowed(self):
        ok, msg = check_url_host("https://gitlab.com/user/repo", DEFAULT_HOSTS)
        assert ok is True

    def test_unknown_host_rejected(self):
        ok, msg = check_url_host("https://unknown-host.example.com/repo", DEFAULT_HOSTS)
        assert ok is False
        assert "unknown-host.example.com" in msg

    def test_subdomain_allowed(self):
        ok, msg = check_url_host("https://sub.github.com/user/repo", DEFAULT_HOSTS)
        assert ok is True

    def test_invalid_url(self):
        ok, msg = check_url_host("not-a-url", DEFAULT_HOSTS)
        assert ok is False
        assert "Invalid URL format" in msg

    def test_custom_host_list(self):
        ok, msg = check_url_host("https://my-git.internal.com/repo", ["my-git.internal.com"])
        assert ok is True


class TestCustomTagPattern:
    def test_clickable_pattern_matches(self):
        clickable, plain = custom_tag_pattern("003399")
        import re
        badge = '[![EU](https://img.shields.io/badge/EU-003399)](https://example.com)'
        assert re.search(clickable, badge)

    def test_plain_pattern_matches(self):
        clickable, plain = custom_tag_pattern("FF0000")
        import re
        badge = '![Tag](https://img.shields.io/badge/Tag-FF0000)'
        assert re.search(plain, badge)

    def test_wrong_color_no_match(self):
        clickable, plain = custom_tag_pattern("003399")
        import re
        badge = '![Tag](https://img.shields.io/badge/Tag-FF0000)'
        assert not re.search(plain, badge)


class TestLoadConfig:
    def test_default_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(tmpdir)
            assert config["allowed_hosts"] == DEFAULT_HOSTS
            assert config["require_badges"] is False
            assert config["check_alphabetical"] is True

    def test_custom_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".awesomerc.json"
            config_path.write_text('{"require_badges": true, "badge_types": ["stars"]}')
            config = load_config(tmpdir)
            assert config["require_badges"] is True
            assert config["badge_types"] == ["stars"]


class TestLintReadme:
    def _write_readme(self, tmpdir, content):
        readme = Path(tmpdir) / "README.md"
        readme.write_text(content)
        return str(readme)

    def _badge(self, user, repo):
        """Helper to create a standard badge string."""
        return f"[![Stars](https://img.shields.io/github/stars/{user}/{repo})](https://github.com/{user}/{repo})"

    def test_valid_readme_no_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - First tool.\n"
                f"- [Beta](https://github.com/u/b) {self._badge('u', 'b')} - Second tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert errors == []

    def test_alphabetical_order_violation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Zebra](https://github.com/u/z) {self._badge('u', 'z')} - Last tool.\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - First tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("alphabetical" in e[1].lower() for e in errors)

    def test_duplicate_url_detected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - First.\n"
                f"- [AlphaDupe](https://github.com/u/a) {self._badge('u', 'a')} - Duplicate.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("Duplicate URL" in e[1] for e in errors)

    def test_description_missing_period(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - Missing period\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("period" in e[1].lower() for e in errors)

    def test_description_lowercase_start(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - lowercase start.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("capital" in e[1].lower() for e in errors)

    def test_unknown_host_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://evil.com/repo) {self._badge('u', 'a')} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("not in allowed list" in e[1] for e in errors)

    def test_badge_requirement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                "- [Alpha](https://github.com/u/a) [![License](https://img.shields.io/github/license/u/a)](https://github.com/u/a) - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            config["require_badges"] = True
            config["badge_types"] = ["stars"]
            errors = lint_readme(readme, config)
            assert any("Missing required badge: stars" in e[1] for e in errors)
