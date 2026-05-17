# Lab 3 - COM program model

This folder contains files for lab 3 where COM program execution is modeled.

## Files

- `lab3_step1_notepad.bat` - BAT for step 1 (`Start notepad.exe`)
- `lab3_step2_start_bat.cs` - C# app for step 2 (`Process.Start` for BAT)
- `lab3_step3_build_com.cs` - C# app that writes COM binaries from byte arrays
- `lab3_step4_run_com.bat` - BAT template for step 4 (run generated `.com`)
- `lab3_report.txt` - text report for the lab
- `lab3_submission_manifest.txt` - checklist of submission files
- `vDOS_for_Win64/` - DOS emulator files for 64-bit Windows

## Why CI is used

The local machine is macOS, so Windows-specific parts are prepared and validated in GitHub Actions on `windows-latest`.

Workflow:

- `.github/workflows/lab3-com-model.yml`

CI builds both C# utilities and generates COM files from defined byte arrays.

## Manual part for final screenshots

For report screenshots, run manually on Windows with vDos:

1. Start `vDos.exe` in `lab3/vDOS_for_Win64/`
2. Type `list1`, then input any text, verify output line
3. Exit with `exit`
4. Copy generated `lab3_message.com` into that folder
5. Run `lab3_message.com` in vDos and capture screenshot
6. Run `lab3_message_long.com` and capture screenshot for step 6
