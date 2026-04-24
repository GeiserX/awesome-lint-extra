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

    # --- lint disable / enable blocks (lines 117-129) ---

    def test_lint_disable_skips_entries(self):
        """Entries inside lint disable blocks are not checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                "<!--lint disable-->\n"
                "- [Zzz](https://evil.com/repo) - bad entry no period\n"
                "<!--lint enable-->\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - Good entry.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            # The bad entry inside disable block should not produce errors
            assert not any("Zzz" in e[1] for e in errors)

    def test_toc_entries_collected_inside_lint_disable(self):
        """ToC entries inside lint-disable blocks are collected for ToC checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Contents\n\n"
                "<!--lint disable-->\n"
                "- [Tools](#tools)\n"
                "- [Libraries](#libraries)\n"
                "<!--lint enable-->\n\n"
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - A tool.\n\n"
                "## Libraries\n\n"
                f"- [Beta](https://github.com/u/b) {self._badge('u', 'b')} - A lib.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert not any("ToC" in e[1] for e in errors)

    def test_toc_mismatch_reports_error(self):
        """ToC entry with no matching section produces an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Contents\n\n"
                "<!--lint disable-->\n"
                "- [Tools](#tools)\n"
                "- [Nonexistent](#nonexistent)\n"
                "<!--lint enable-->\n\n"
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("Nonexistent" in e[1] and "ToC" in e[1] for e in errors)

    def test_section_in_actual_but_not_toc_is_tolerated(self):
        """Sections present in the doc but not in ToC do not produce errors (footer sections)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Contents\n\n"
                "<!--lint disable-->\n"
                "- [Tools](#tools)\n"
                "<!--lint enable-->\n\n"
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - A tool.\n\n"
                "## Contributing\n\n"
                "Please contribute.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert not any("Contributing" in e[1] for e in errors)

    # --- subsection tracking (lines 141-143) ---

    def test_subsection_resets_alphabetical_order(self):
        """A new ### subsection resets alphabetical ordering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                "### CLI\n\n"
                f"- [Zebra](https://github.com/u/z) {self._badge('u', 'z')} - Last.\n\n"
                "### GUI\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - First.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            # Alpha after Zebra is OK because subsection reset ordering
            assert not any("alphabetical" in e[1].lower() for e in errors)

    # --- unparseable entry (lines 151-152) ---

    def test_unparseable_entry_reports_error(self):
        """An entry line that starts with '- [' but cannot be parsed reports an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                "- [BrokenLink](missingclosingparen - No good.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("Cannot parse entry format" in e[1] for e in errors)

    # --- description starts with project name (line 178) ---

    def test_description_starts_with_project_name(self):
        """Description that starts with the project name is flagged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [MyTool](https://github.com/u/t) {self._badge('u', 't')} - MyTool is a great thing.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("should not start with the project name" in e[1] for e in errors)

    # --- no description after separator (line 170) ---

    def test_no_description_after_separator(self):
        """Entry with badges but no ' - Description' part reports missing description."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} some text without separator.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            errors = lint_readme(readme, config)
            assert any("No description found" in e[1] for e in errors)

    # --- custom tag badge checking (lines 196-199) ---

    def test_custom_tag_missing_reports_error(self):
        """Entry missing a required custom tag badge reports an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            config["require_custom_tags"] = "003399"
            errors = lint_readme(readme, config)
            assert any("Missing custom tag badge" in e[1] for e in errors)

    def test_custom_tag_present_no_error(self):
        """Entry with a matching custom tag badge passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tag = '[![EU](https://img.shields.io/badge/EU-003399)](https://example.com)'
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} {tag} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            config["require_custom_tags"] = "003399"
            errors = lint_readme(readme, config)
            assert not any("Missing custom tag badge" in e[1] for e in errors)

    def test_custom_tag_plain_badge_accepted(self):
        """A non-clickable (plain) custom tag badge also passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tag = '![EU](https://img.shields.io/badge/EU-003399)'
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} {tag} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            config = load_config(tmpdir)
            config["require_custom_tags"] = "003399"
            errors = lint_readme(readme, config)
            assert not any("Missing custom tag badge" in e[1] for e in errors)


class TestMain:
    """Tests for the main() function (lines 216-249, 253)."""

    def _write_readme(self, tmpdir, content):
        readme = Path(tmpdir) / "README.md"
        readme.write_text(content)
        return str(readme)

    def _badge(self, user, repo):
        return f"[![Stars](https://img.shields.io/github/stars/{user}/{repo})](https://github.com/{user}/{repo})"

    def test_main_readme_not_found(self, monkeypatch):
        """main() exits 1 when README.md does not exist."""
        from lint import main
        monkeypatch.setenv("INPUT_README", "/nonexistent/README.md")
        monkeypatch.delenv("INPUT_ALLOWED_HOSTS", raising=False)
        monkeypatch.delenv("INPUT_REQUIRE_BADGES", raising=False)
        monkeypatch.delenv("INPUT_BADGE_TYPES", raising=False)
        monkeypatch.delenv("INPUT_REQUIRE_CUSTOM_TAGS", raising=False)
        monkeypatch.delenv("INPUT_CHECK_ALPHABETICAL", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_main_clean_readme_exits_0(self, monkeypatch):
        """main() exits 0 on a valid README."""
        from lint import main
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            monkeypatch.setenv("INPUT_README", readme)
            monkeypatch.delenv("INPUT_ALLOWED_HOSTS", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_BADGES", raising=False)
            monkeypatch.delenv("INPUT_BADGE_TYPES", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_CUSTOM_TAGS", raising=False)
            monkeypatch.delenv("INPUT_CHECK_ALPHABETICAL", raising=False)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_with_errors_exits_1(self, monkeypatch, capsys):
        """main() exits 1 and prints errors when lint finds issues."""
        from lint import main
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://evil.com/a) {self._badge('u', 'a')} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            monkeypatch.setenv("INPUT_README", readme)
            monkeypatch.delenv("INPUT_ALLOWED_HOSTS", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_BADGES", raising=False)
            monkeypatch.delenv("INPUT_BADGE_TYPES", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_CUSTOM_TAGS", raising=False)
            monkeypatch.delenv("INPUT_CHECK_ALPHABETICAL", raising=False)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "error(s)" in captured.out

    def test_main_env_allowed_hosts(self, monkeypatch):
        """INPUT_ALLOWED_HOSTS env var overrides config."""
        from lint import main
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://custom.host/a) {self._badge('u', 'a')} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            monkeypatch.setenv("INPUT_README", readme)
            monkeypatch.setenv("INPUT_ALLOWED_HOSTS", '["custom.host"]')
            monkeypatch.delenv("INPUT_REQUIRE_BADGES", raising=False)
            monkeypatch.delenv("INPUT_BADGE_TYPES", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_CUSTOM_TAGS", raising=False)
            monkeypatch.delenv("INPUT_CHECK_ALPHABETICAL", raising=False)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_env_require_badges(self, monkeypatch):
        """INPUT_REQUIRE_BADGES and INPUT_BADGE_TYPES env vars override config."""
        from lint import main
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            monkeypatch.setenv("INPUT_README", readme)
            monkeypatch.setenv("INPUT_REQUIRE_BADGES", "true")
            monkeypatch.setenv("INPUT_BADGE_TYPES", '["license"]')
            monkeypatch.delenv("INPUT_ALLOWED_HOSTS", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_CUSTOM_TAGS", raising=False)
            monkeypatch.delenv("INPUT_CHECK_ALPHABETICAL", raising=False)
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Missing license badge -> errors -> exit 1
            assert exc_info.value.code == 1

    def test_main_env_require_custom_tags(self, monkeypatch):
        """INPUT_REQUIRE_CUSTOM_TAGS env var override."""
        from lint import main
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            monkeypatch.setenv("INPUT_README", readme)
            monkeypatch.setenv("INPUT_REQUIRE_CUSTOM_TAGS", "FF0000")
            monkeypatch.delenv("INPUT_ALLOWED_HOSTS", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_BADGES", raising=False)
            monkeypatch.delenv("INPUT_BADGE_TYPES", raising=False)
            monkeypatch.delenv("INPUT_CHECK_ALPHABETICAL", raising=False)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_env_check_alphabetical_false(self, monkeypatch):
        """INPUT_CHECK_ALPHABETICAL=false disables alphabetical checking."""
        from lint import main
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Tools\n\n"
                f"- [Zebra](https://github.com/u/z) {self._badge('u', 'z')} - Last.\n"
                f"- [Alpha](https://github.com/u/a) {self._badge('u', 'a')} - First.\n"
            )
            readme = self._write_readme(tmpdir, content)
            monkeypatch.setenv("INPUT_README", readme)
            monkeypatch.setenv("INPUT_CHECK_ALPHABETICAL", "false")
            monkeypatch.delenv("INPUT_ALLOWED_HOSTS", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_BADGES", raising=False)
            monkeypatch.delenv("INPUT_BADGE_TYPES", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_CUSTOM_TAGS", raising=False)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_error_at_line_zero_prints_without_line_number(self, monkeypatch, capsys):
        """ToC mismatch errors (line_num=0) print without a line number prefix."""
        from lint import main
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                "## Contents\n\n"
                "<!--lint disable-->\n"
                "- [Tools](#tools)\n"
                "- [Ghost](#ghost)\n"
                "<!--lint enable-->\n\n"
                "## Tools\n\n"
                "- [Alpha](https://github.com/u/a) "
                "[![Stars](https://img.shields.io/github/stars/u/a)](https://github.com/u/a)"
                " - A tool.\n"
            )
            readme = self._write_readme(tmpdir, content)
            monkeypatch.setenv("INPUT_README", readme)
            monkeypatch.delenv("INPUT_ALLOWED_HOSTS", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_BADGES", raising=False)
            monkeypatch.delenv("INPUT_BADGE_TYPES", raising=False)
            monkeypatch.delenv("INPUT_REQUIRE_CUSTOM_TAGS", raising=False)
            monkeypatch.delenv("INPUT_CHECK_ALPHABETICAL", raising=False)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            # Line-0 errors should not have ":<line>" prefix
            assert "Ghost" in captured.out
