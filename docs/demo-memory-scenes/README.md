# Demo Memory Scenes

These are reproducible canon-memory proof cases. They do not need API keys or
AI providers. Run from the repo root with D-drive runtime folders set:

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\SkitBoxData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:SKITBOX_HOME = "D:\SkitBoxData"
python scripts\sample_memory.py --room kitchen
```

Each case generates a first scene, saves it as canon, then generates a second
scene in the same room. The second scene should include `Previously In This
Room`, `Memory:`, and a `Memory read:` trace line.

The goal is proof of behavior, not freezing every joke forever. If tuning
changes the exact wording, keep the seeds and expected anchors updated.

