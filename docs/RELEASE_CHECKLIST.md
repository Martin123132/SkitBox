# SkitBox Release Checklist

Use this before publishing a public ZIP.

## Local Checks

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\SkitBoxData, D:\SkitBoxVerifyWork | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:SKITBOX_HOME = "D:\SkitBoxData"
python -m unittest discover -s tests
python -m compileall sitcom_engine_app tests scripts
python scripts\sample_episodes.py --count 5
python scripts\sample_episodes.py --count 3 --room kitchen
python scripts\sample_memory.py --room kitchen
python scripts\sample_episodes.py --count 3 --prompt "A saucer beam, police tape, and a heart above two people."
python -m sitcom_engine_app.app --doctor
```

## Manual Browser Smoke

Start the app from the repo with D-safe runtime folders:

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\SkitBoxData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:SKITBOX_HOME = "D:\SkitBoxData"
$env:SKITBOX_DISABLE_OPEN = "1"
python -m sitcom_engine_app.app --no-open --port 0
```

1. Press `Show Me A Funny One` and confirm a skit appears.
2. Press `Start Tester Run`.
3. On Tester, press `Generate Demo Scene`.
4. Press `Save Current Scene As Canon`.
5. Press `Open Memory` and confirm the saved room incident appears.
6. Return to Tester and press `Generate Remembered Scene`.
7. Confirm `Previously In This Room` appears when memory exists.
8. Press `Export Share Card`.
9. Press `Copy Feedback Summary`.
10. Confirm the side navigation shows page readiness dots.
11. Confirm one page is marked `Next`.
12. Choose a template.
13. Export Current World from Templates.
14. Paste that JSON back into Import World JSON and apply it.
15. Open Rooms, select a room, move one cast member or prop, and save the room map.
16. Generate in that room and confirm the room appears in the skit and trace.
17. Reset canon memory and confirm rooms, cast, jokes, and favourites remain.
18. Open Sparks and click an example prompt button.
19. Describe a weird scene on Sparks and press `Use Description`.
20. Confirm the chosen sparks match the description.
21. Generate a skit.
22. Save favourite.
23. Copy Share Text.
24. Export TXT and HTML.
25. Open exports folder.
26. Check mobile width has no horizontal overflow.
27. Stop the app with `powershell -ExecutionPolicy Bypass -File scripts\stop_dev_processes.ps1`.

## Release ZIP

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\SkitBoxData, D:\SkitBoxVerifyWork | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:SKITBOX_HOME = "D:\SkitBoxData"
powershell -ExecutionPolicy Bypass -File scripts\make_release_zip.ps1
$zip = (Get-ChildItem dist\SkitBox-v*.zip | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
powershell -ExecutionPolicy Bypass -File scripts\verify_release_zip.ps1 -ZipPath $zip -WorkRoot D:\SkitBoxVerifyWork
```

The ZIP must not contain `.git`, `__pycache__`, `.pytest_cache`, `dist`, or
`user_data`. It must include `START_SkitBox_WINDOWS.bat` and
`STOP_SkitBox_WINDOWS.bat`.

Before publishing, skim `docs\demo-room-scenes` and
`docs\demo-memory-scenes`. The proof cases should show room choice steering
setting, cast, memory, and trace output.
