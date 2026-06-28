# Demo Room Scenes

These are reproducible room-map proof cases for tester demos and tuning. Run
them from the repo root with D-drive runtime folders set:

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\SkitBoxData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:SKITBOX_HOME = "D:\SkitBoxData"
python scripts\sample_episodes.py --count 3 --room kitchen
```

Each file lists seed, mode, room, expected anchors, and the command to recreate
the scene. The goal is not to freeze every line forever; it is to keep proof
that room selection visibly steers setting, cast, memory, and trace output.

For canon-memory proofs that save a first scene and show it affecting the
second, see `docs\demo-memory-scenes`.

