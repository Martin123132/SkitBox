# Python Friction Decision

For the next public patch, keep SkitBox as a simple ZIP plus Python launcher.

Why:

- It keeps the repo small and easy to inspect.
- It avoids installer, antivirus, signing, and EXE packaging work while the app is still changing quickly.
- It lets testers prove the real first-run flow first: unzip, double-click, generate, save, export.

Current requirement:

- Windows
- Python 3.10 or newer
- No npm
- No API keys
- No Ollama
- No cloud account

Trigger for revisiting:

- If testers repeatedly fail before the browser opens because Python is missing or confusing.
- If Windows security prompts around `.bat` files become the biggest blocker.
- If people can generate and export reliably, but the remaining feedback is mostly "I wish this installed like a normal app."

Likely next packaging step:

- Build a local EXE release candidate from the same source, then test it beside the ZIP before making it the default download.
