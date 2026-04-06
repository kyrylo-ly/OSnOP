# Lab 7 - DLL usage from non-C++ languages

This lab reuses `Lab5Dll.dll` and `Lab5Dll.lib` from lab 5 and demonstrates calls from:

1. C# (`DllImport`, implicit linking / P-Invoke)
2. Python (`ctypes`)

## Files in this folder

- `lab7_csharp_dll_test.cs` - C# test program (single source file)
- `lab7_csharp_output_with_comments.txt` - printed C# output with comments
- `lab7_python_dll_test.py` - Python test program (single source file)
- `lab7_python_output_with_comments.txt` - printed Python output with comments
- `lab7_report.txt` - formal report text
- `lab7_submission_manifest.txt` - list of files for submission

## Prerequisites

1. Build lab 5 DLL and obtain files:
   - `Lab5Dll.dll`
   - `Lab5Dll.lib`
2. Put DLL where runtime can find it:
   - next to executable/script, or
   - in one of system `PATH` directories.

## Run C# test

Example with .NET SDK:

```bash
dotnet new console -n Lab7CSharpTemp
# replace generated Program.cs with lab7_csharp_dll_test.cs content
dotnet run
```

## Run Python test

```bash
python lab7_python_dll_test.py
```

## Expected key output

- `all DLL tests passed`
- `avgLoad=59.175, peakIndex=2, cost=34.5984`
- `tag=AL-0042, strongScore=100, weakScore=11`
