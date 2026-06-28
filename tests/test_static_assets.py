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
        self.assertIn("navPageStatus", js)
        self.assertIn("nav-status-dot", css)
        self.assertIn("[hidden]", css)
        self.assertIn("SkitBox", html)
        self.assertIn("<title>SkitBox</title>", html)
        self.assertIn('<span class="brand-mark">SB</span>', html)
        old_brand = "Sitcom" + "Engine"
        self.assertNotIn(old_brand, html)


if __name__ == "__main__":
    unittest.main()
