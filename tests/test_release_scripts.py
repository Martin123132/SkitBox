from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


class ReleaseScriptTests(unittest.TestCase):
    def test_verify_release_zip_accepts_valid_zip(self) -> None:
        if sys.platform != "win32":
            self.skipTest("PowerShell release verification is Windows-first.")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "release.zip"
            with zipfile.ZipFile(zip_path, "w") as release:
                release.writestr("START_SkitBox_WINDOWS.bat", "@echo off\n")
                release.writestr("STOP_SkitBox_WINDOWS.bat", "@echo off\n")
                release.writestr("README.md", "# SkitBox\n")
                release.writestr("scripts/stop_dev_processes.ps1", "Write-Host 'stop'\n")
                release.writestr("sitcom_engine_app/app.py", "print('doctor')\n")
                release.writestr("sitcom_engine_app/engine.py", "\n")
                release.writestr("sitcom_engine_app/seeds/default_show.json", "{}\n")
                release.writestr("sitcom_engine_app/seeds/templates.json", "[]\n")
                release.writestr("sitcom_engine_app/templates/index.html", "<!doctype html>\n")
                release.writestr("sitcom_engine_app/static/assets/sitcom-set-bg.png", b"fake")

            result = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "scripts\\verify_release_zip.ps1",
                    "-ZipPath",
                    str(zip_path),
                    "-SkipDoctor",
                    "-WorkRoot",
                    str(root / "work"),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Release ZIP verified", result.stdout)


if __name__ == "__main__":
    unittest.main()
