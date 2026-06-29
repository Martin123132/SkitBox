from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StaticAssetTests(unittest.TestCase):
    def test_css_static_asset_references_exist(self) -> None:
        css_path = ROOT / "sitcom_engine_app" / "static" / "app.css"
        css = css_path.read_text(encoding="utf-8")
        urls = sorted(set(re.findall(r'url\("/static/assets/([^"]+)"\)', css)))

        self.assertIn("skitbox-guide-bg-v1.png", urls)
        self.assertIn("skitbox-sparks-bg-v1.png", urls)
        self.assertIn("skitbox-studio-bg-v2.png", urls)
        self.assertIn("skitbox-library-bg-v1.png", urls)
        self.assertIn("skitbox-wallpaper-v1.png", urls)

        for asset_name in urls:
            asset_path = ROOT / "sitcom_engine_app" / "static" / "assets" / asset_name
            self.assertTrue(asset_path.exists(), f"Missing CSS asset: {asset_name}")
            self.assertGreater(asset_path.stat().st_size, 1000, f"Empty or placeholder CSS asset: {asset_name}")

    def test_guided_navigation_assets_are_wired(self) -> None:
        js = (ROOT / "sitcom_engine_app" / "static" / "app.js").read_text(encoding="utf-8")
        css = (ROOT / "sitcom_engine_app" / "static" / "app.css").read_text(encoding="utf-8")
        html = (ROOT / "sitcom_engine_app" / "templates" / "index.html").read_text(encoding="utf-8")

        self.assertIn("renderNavigationStatus", js)
        self.assertIn("renderMobileNavigation", js)
        self.assertIn("navPageStatus", js)
        self.assertIn("renderFirstRunCard", js)
        self.assertIn("renderRooms", js)
        self.assertIn("Generate Scene In This Room", js)
        self.assertIn("next_optional", js)
        self.assertIn("room-save-reminder", js)
        self.assertIn("renderRoomFocusCard", js)
        self.assertIn("renderMemory", js)
        self.assertIn("renderTester", js)
        self.assertIn("testerFeedbackSummary", js)
        self.assertIn("firstRunTesterButton", js)
        self.assertIn("guideTesterButton", js)
        self.assertIn("Save This As Canon", js)
        self.assertIn("Copy Share Text", js)
        self.assertIn("Export Share Card", js)
        self.assertIn("testerOpenExportsButton", js)
        self.assertIn("Share card saved in exports", js)
        self.assertIn("Copy was blocked, so the feedback summary is selected", js)
        self.assertIn("/api/canon", js)
        self.assertIn("/api/memory/reset", js)
        self.assertIn("/api/world-pack/export", js)
        self.assertIn("/api/world-pack/import", js)
        self.assertIn("STOP_SkitBox_WINDOWS.bat", js)
        self.assertIn("nav-status-dot", css)
        self.assertIn("mobile-nav-panel", css)
        self.assertIn("mobile-page-menu", css)
        self.assertIn("first-run-card", css)
        self.assertIn("stop-note", css)
        self.assertIn("room-card-grid", css)
        self.assertIn("room-chip", css)
        self.assertIn("room-focus-card", css)
        self.assertIn("room-save-reminder.dirty", css)
        self.assertIn("memory-grid", css)
        self.assertIn("canon-summary", css)
        self.assertIn("tester-step", css)
        self.assertIn("feedback-summary", css)
        self.assertIn("world-pack-panel", css)
        self.assertIn("mini-card-copy", css)
        self.assertIn("[hidden]", css)
        self.assertIn("mobileNavPanel", html)
        self.assertIn('href="/rooms"', html)
        self.assertIn('href="/memory"', html)
        self.assertIn('href="/tester"', html)
        self.assertIn("SkitBox", html)
        self.assertIn("<title>SkitBox</title>", html)

    def test_github_issue_templates_are_present(self) -> None:
        template_dir = ROOT / ".github" / "ISSUE_TEMPLATE"
        expected = [
            "bug_report.yml",
            "config.yml",
            "first-run-feedback.yml",
            "funny_output.yml",
        ]
        for name in expected:
            path = template_dir / name
            self.assertTrue(path.exists(), f"Missing issue template: {name}")
            self.assertIn("name:", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
