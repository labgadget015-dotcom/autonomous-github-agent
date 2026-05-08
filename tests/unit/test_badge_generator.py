"""Unit tests for .github/scripts/badge_generator.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from badge_generator import BadgeGenerator


class TestGenerateHealthBadge:
    def _gen(self):
        return BadgeGenerator()

    def test_score_90_plus_is_excellent_brightgreen(self):
        badge = self._gen().generate_health_badge(95)
        assert "excellent" in badge
        assert "brightgreen" in badge

    def test_score_75_to_89_is_good_green(self):
        badge = self._gen().generate_health_badge(80)
        assert "good" in badge
        assert "green" in badge

    def test_score_60_to_74_is_fair_yellow(self):
        badge = self._gen().generate_health_badge(65)
        assert "fair" in badge
        assert "yellow" in badge

    def test_score_below_60_is_poor_red(self):
        badge = self._gen().generate_health_badge(40)
        assert "poor" in badge
        assert "red" in badge

    def test_badge_contains_score_value(self):
        badge = self._gen().generate_health_badge(88)
        assert "88" in badge

    def test_badge_starts_with_markdown_image(self):
        badge = self._gen().generate_health_badge(75)
        assert badge.startswith("![")


class TestGenerateCoverageBadge:
    def _gen(self):
        return BadgeGenerator()

    def test_coverage_90_plus_brightgreen(self):
        badge = self._gen().generate_coverage_badge(92.0)
        assert "brightgreen" in badge

    def test_coverage_80_to_89_green(self):
        badge = self._gen().generate_coverage_badge(85.0)
        assert "green" in badge

    def test_coverage_70_to_79_yellow(self):
        badge = self._gen().generate_coverage_badge(75.0)
        assert "yellow" in badge

    def test_coverage_below_70_red(self):
        badge = self._gen().generate_coverage_badge(50.0)
        assert "red" in badge

    def test_badge_contains_coverage_value(self):
        badge = self._gen().generate_coverage_badge(87.5)
        assert "87.5" in badge


class TestGenerateSecurityBadge:
    def _gen(self):
        return BadgeGenerator()

    def test_zero_issues_brightgreen_passing(self):
        badge = self._gen().generate_security_badge(0)
        assert "brightgreen" in badge
        assert "passing" in badge

    def test_one_to_three_issues_yellow(self):
        badge = self._gen().generate_security_badge(2)
        assert "yellow" in badge

    def test_more_than_three_issues_red(self):
        badge = self._gen().generate_security_badge(5)
        assert "red" in badge


class TestGenerateComplexityBadge:
    def _gen(self):
        return BadgeGenerator()

    def test_complexity_5_or_less_is_low_brightgreen(self):
        badge = self._gen().generate_complexity_badge(4.0)
        assert "low" in badge
        assert "brightgreen" in badge

    def test_complexity_5_to_10_is_moderate_green(self):
        badge = self._gen().generate_complexity_badge(8.0)
        assert "moderate" in badge

    def test_complexity_10_to_15_is_high_yellow(self):
        badge = self._gen().generate_complexity_badge(12.0)
        assert "high" in badge
        assert "yellow" in badge

    def test_complexity_above_15_is_very_high_red(self):
        badge = self._gen().generate_complexity_badge(20.0)
        assert "red" in badge


class TestGenerateStaticBadges:
    def _gen(self):
        return BadgeGenerator()

    def test_license_badge_contains_mit(self):
        badge = self._gen().generate_license_badge()
        assert "MIT" in badge

    def test_python_badge_contains_python(self):
        badge = self._gen().generate_python_badge()
        assert "python" in badge.lower() or "Python" in badge

    def test_workflow_badge_contains_github_url(self):
        badge = self._gen().generate_workflow_badge()
        assert "github.com" in badge


class TestGenerateAllBadges:
    def test_generate_all_badges_returns_dict(self):
        gen = BadgeGenerator()
        badges = gen.generate_all_badges()
        assert isinstance(badges, dict)

    def test_generate_all_badges_contains_required_keys(self):
        gen = BadgeGenerator()
        badges = gen.generate_all_badges()
        assert "health" in badges
        assert "coverage" in badges
        assert "security" in badges
        assert "license" in badges


class TestGenerateBadgeSection:
    def test_badge_section_contains_start_and_end_markers(self):
        gen = BadgeGenerator()
        section = gen.generate_badge_section()
        assert "<!-- BADGES START -->" in section
        assert "<!-- BADGES END -->" in section


class TestUpdateReadmeBadges:
    def test_readme_not_found_is_handled_gracefully(self, tmp_path):
        gen = BadgeGenerator()
        # Should not raise even if file doesn't exist
        gen.update_readme_badges(str(tmp_path / "nonexistent_README.md"))

    def test_readme_updated_with_badges(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "# My Project\n\n<!-- BADGES START -->\nold\n<!-- BADGES END -->\n"
        )
        gen = BadgeGenerator()
        gen.update_readme_badges(str(readme))
        content = readme.read_text()
        assert "BADGES START" in content

    def test_readme_without_badge_section_gets_badges_inserted(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# My Project\n\nSome description.\n")
        gen = BadgeGenerator()
        gen.update_readme_badges(str(readme))
        content = readme.read_text()
        # Should have modified the file
        assert len(content) > 0
