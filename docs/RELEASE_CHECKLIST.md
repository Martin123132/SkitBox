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

1. Start the app with `python -m sitcom_engine_app.app --no-open --port 0`.
2. Press `Show Me A Funny One` and confirm a skit appears.
3. Confirm the side navigation shows page readiness dots.
4. Confirm one page is marked `Next`.
5. Choose a template.
6. Open Rooms, select a room, move one cast member or prop, and save the room map.
7. Generate in that room and confirm the room appears in the skit and trace.
8. Press `Save This As Canon`.
9. Open Memory and confirm the saved room incident appears.
10. Generate again in the same room and confirm `Previously In This Room` appears.
11. Reset canon memory and confirm rooms, cast, jokes, and favourites remain.
12. Open Sparks and click an example prompt button.
13. Describe a weird scene on Sparks and press `Use Description`.
14. Confirm the chosen sparks match the description.
15. Generate a skit.
16. Save favourite.
17. Export TXT and HTML.
18. Open exports folder.
19. Check mobile width has no horizontal overflow.
20. Stop the app with `powershell -ExecutionPolicy Bypass -File scripts\stop_dev_processes.ps1`.

## Release ZIP

```powershell
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
