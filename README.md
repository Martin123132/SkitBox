# SkitBox

SkitBox is a local-first skit workshop for tiny sitcoms from weird
ideas. Build a show bible, add cast, locations, props, running jokes, and
rules, then generate repeatable skits with no API keys, cloud accounts, npm,
or build step.

The app teaches by state: separate pages, red/amber/green readiness lights,
starter templates, clickable scene sparks, a local "Describe A Weird Scene"
translator, and clear next actions.

## Start On Windows

1. Double-click `START_SkitBox_WINDOWS.bat`.
2. Your browser opens.
3. Press `Show Me A Funny One` for an instant demo, or follow the 7-step flow.
4. Pick a starting sitcom template.
5. Choose an example prompt, type your own weird scene, or pick 1-3 scene sparks.
6. Press `Use Description`, then `Generate Skit`.

The launcher prefers `D:\SkitBoxData` and `D:\Temp` when D: is available,
then falls back to `user_data` beside the app. You can force any folder with
`SKITBOX_HOME`.

To close a running local server, double-click `STOP_SkitBox_WINDOWS.bat`.

## D-Drive Development

Use D-drive runtime folders during development:

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\SkitBoxData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:SKITBOX_HOME = "D:\SkitBoxData"
python -m sitcom_engine_app.app
```

Close it after testing:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_dev_processes.ps1
```

## Checks

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\SkitBoxData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:SKITBOX_HOME = "D:\SkitBoxData"
python -m unittest discover -s tests
python -m compileall sitcom_engine_app tests scripts
python scripts\sample_episodes.py --count 5
python scripts\sample_episodes.py --count 3 --prompt "A saucer beam, police tape, and a heart above two people."
python -m sitcom_engine_app.app --doctor
```

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

## Design Promise

The app should teach through state: traffic lights, counts, next actions, and
separate pages. Demo Mode and prompt examples should help new users see the
shape before they have to invent anything. It should never feel like a cramped
control panel.

## License

SkitBox is source-available for personal and non-commercial use under the
PolyForm Noncommercial License 1.0.0. Commercial use requires a separate
written license from the licensor.
