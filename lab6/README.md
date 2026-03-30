# Lab 6 - Using DLL in C++ (implicit and explicit linking)

This folder contains two sample client apps (Empty Project style) that use the DLL from lab 5.

## Folder structure

- ImplicitLinkProject/main.cpp: client app with implicit linking
- ExplicitLinkProject/main.cpp: client app with explicit linking

## Preconditions

1. Build the DLL project from lab 5 and get these files:
   - Lab5Dll.dll
   - Lab5Dll.lib
2. Put both files in one shared folder, for example:
   - C:\\dlls\\lab5

## Project 1 - Implicit linking

1. Create an Empty Project in Visual Studio and add:
   - source file from ImplicitLinkProject/main.cpp
2. Configure include path:
   - Project -> Properties -> C/C++ -> General -> Additional Include Directories
   - add path to folder with Lab5Dll.h
3. Configure LIB path:
   - Linker -> General -> Additional Library Directories
   - add path to folder with Lab5Dll.lib
4. Configure import library name:
   - Linker -> Input -> Additional Dependencies
   - add Lab5Dll.lib
5. Build and run from Visual Studio (Local Windows Debugger).
6. To run EXE outside Visual Studio:
   - copy Lab5Dll.dll into output folder (Debug or Release) near EXE
   - run EXE directly from that folder

## Project 2 - Explicit linking

1. Create another Empty Project and add:
   - source file from ExplicitLinkProject/main.cpp
2. No import LIB setup is required.
3. Build and run.
4. The code loads DLL with LoadLibraryA and resolves functions with GetProcAddress.
5. Make sure Lab5Dll.dll is in one of the paths listed in source code.

## What is tested

Both projects test all 5 DLL functions:

1. AnalyzeCpuLoadW
2. CountStableTransitionsW
3. EstimateDeliveryCostW
4. BuildUserTagW
5. EvaluatePasswordStrengthW

Each function is called with valid input, and selected invalid cases are also checked.

## Expected output examples

Implicit app:

- Implicit linking: all DLL tests passed.

Explicit app:

- Explicit linking: all DLL tests passed.
- Loaded from: <path>

## Notes for report

- Describe difference between compile-time binding (implicit) and runtime binding (explicit).
- Show that EXE fails outside IDE without DLL in output folder, then works after DLL is copied.
- Attach screenshots of both runs and output.

## GitHub Actions automation

- Root workflow file: ../.github/workflows/lab6-dll.yml
- Workflow builds DLL from lab5 sources, builds both lab6 clients, and validates behavior:
  - implicit client fails when DLL is missing
  - both clients pass when DLL is placed near EXE

To run this workflow, repository root must be a GitHub repository.
