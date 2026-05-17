#!/usr/bin/env python3
"""Lab 2: file attributes and properties for *.dat files.

Console dialog application that:
1) Finds two *.dat files in current directory or nested ./problem directory.
2) Shows full names and full paths.
3) Prints file properties/attributes table.
4) Shows text content of selected file (without OpenFileDialog).
5) Sums numbers with correction of invalid tokens.

Run example:
    python3 lab2_file_attributes.py
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SessionState:
    """Stores discovered files and protocol settings for current session."""

    dat_files: list[Path]
    protocol_enabled: bool
    protocol_path: Path


def now_str() -> str:
    """Returns current timestamp string for protocol records."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_protocol(state: SessionState, message: str) -> None:
    """Appends message to protocol file when protocol mode is enabled."""
    if not state.protocol_enabled:
        return
    with state.protocol_path.open("a", encoding="utf-8") as f:
        f.write(f"[{now_str()}] {message}\n")


def discover_dat_files(base_dir: Path) -> list[Path]:
    """Finds *.dat files only in base_dir or base_dir/problem directory."""
    files: list[Path] = []

    # Search in current folder.
    files.extend(sorted(base_dir.glob("*.dat")))

    # Search in nested folder problem if it exists.
    problem_dir = base_dir / "problem"
    if problem_dir.exists() and problem_dir.is_dir():
        files.extend(sorted(problem_dir.glob("*.dat")))

    # Normalize to absolute unique paths, stable order.
    normalized = sorted({f.resolve() for f in files})
    return normalized


def bool_mark(value: bool) -> str:
    """Formats bool as Yes/No for table output."""
    return "Yes" if value else "No"


def format_dt(ts: float) -> str:
    """Converts timestamp to human readable date/time."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def get_windows_attr_bits(path: Path) -> dict[str, bool]:
    """Returns Windows-like attribute flags if platform provides them."""
    result = {"hidden": False, "system": False, "archive": False}
    st = path.stat()

    # On Windows, Python may expose st_file_attributes bitmask.
    attrs = getattr(st, "st_file_attributes", None)
    if attrs is None:
        return result

    # Constant values are standard for Windows API file attributes.
    FILE_ATTRIBUTE_HIDDEN = 0x2
    FILE_ATTRIBUTE_SYSTEM = 0x4
    FILE_ATTRIBUTE_ARCHIVE = 0x20

    result["hidden"] = bool(attrs & FILE_ATTRIBUTE_HIDDEN)
    result["system"] = bool(attrs & FILE_ATTRIBUTE_SYSTEM)
    result["archive"] = bool(attrs & FILE_ATTRIBUTE_ARCHIVE)
    return result


def file_info_rows(path: Path) -> list[tuple[str, str]]:
    """Builds key-value rows with file properties and attributes."""
    st = path.stat()
    win_bits = get_windows_attr_bits(path)
    read_only = not os.access(path, os.W_OK)
    hidden_unix = path.name.startswith(".")

    return [
        ("Full name", str(path.resolve())),
        ("File name", path.name),
        ("Extension", path.suffix),
        ("Parent folder", str(path.parent.resolve())),
        ("Size (bytes)", str(st.st_size)),
        ("Created", format_dt(st.st_ctime)),
        ("Modified", format_dt(st.st_mtime)),
        ("Last access", format_dt(st.st_atime)),
        ("Read only", bool_mark(read_only)),
        ("Directory", bool_mark(path.is_dir())),
        ("Regular file", bool_mark(stat.S_ISREG(st.st_mode))),
        ("Hidden", bool_mark(hidden_unix or win_bits["hidden"])),
        ("System", bool_mark(win_bits["system"])),
        ("Archive", bool_mark(win_bits["archive"])),
    ]


def print_table(rows: list[tuple[str, str]]) -> None:
    """Prints aligned two-column table."""
    key_w = max(len(k) for k, _ in rows)
    print("-" * (key_w + 3 + 50))
    for key, value in rows:
        print(f"{key:<{key_w}} | {value}")
    print("-" * (key_w + 3 + 50))


def op1_list_full_names(state: SessionState, base_dir: Path) -> None:
    """Operation 1: discover and show full names of *.dat files."""
    state.dat_files = discover_dat_files(base_dir)

    if len(state.dat_files) == 0:
        msg = "No *.dat files found in current folder or ./problem."
        print(msg)
        write_protocol(state, msg)
        return

    print("Found *.dat files:")
    write_protocol(state, "Operation 1: list full names")
    for idx, path in enumerate(state.dat_files, 1):
        line = f"{idx}. {path.resolve()}"
        print(line)
        write_protocol(state, line)


def op2_show_full_path(state: SessionState) -> None:
    """Operation 2: show full path from root for each discovered file."""
    if not state.dat_files:
        msg = "Run operation 1 first to discover files."
        print(msg)
        write_protocol(state, msg)
        return

    write_protocol(state, "Operation 2: show full paths")
    for idx, path in enumerate(state.dat_files, 1):
        line = f"{idx}. {path.resolve()}"
        print(line)
        write_protocol(state, line)


def op3_show_properties(state: SessionState) -> None:
    """Operation 3: show properties/attributes table for each file."""
    if not state.dat_files:
        msg = "Run operation 1 first to discover files."
        print(msg)
        write_protocol(state, msg)
        return

    write_protocol(state, "Operation 3: show file properties and attributes")
    for idx, path in enumerate(state.dat_files, 1):
        title = f"File #{idx}: {path.name}"
        print(f"\n{title}")
        print_table(file_info_rows(path))
        write_protocol(state, title)
        for k, v in file_info_rows(path):
            write_protocol(state, f"{k}: {v}")


def pick_file(state: SessionState) -> Path | None:
    """Asks user to select one discovered file by index."""
    if not state.dat_files:
        print("Run operation 1 first to discover files.")
        return None

    for idx, path in enumerate(state.dat_files, 1):
        print(f"{idx}. {path.name}")

    selected = input("Select file number: ").strip()
    if not selected.isdigit():
        print("Invalid number.")
        return None

    index = int(selected) - 1
    if index < 0 or index >= len(state.dat_files):
        print("Index out of range.")
        return None

    return state.dat_files[index]


def op4_show_text(state: SessionState) -> None:
    """Operation 4: print text content of selected file."""
    path = pick_file(state)
    if path is None:
        return

    text = path.read_text(encoding="utf-8", errors="replace")
    print(f"\n----- BEGIN: {path.name} -----")
    print(text)
    print(f"----- END: {path.name} -----\n")

    write_protocol(state, f"Operation 4: show text from {path}")
    write_protocol(state, "File content shown in console.")


def parse_numeric_token(token: str) -> float | None:
    """Parses token as integer/float; returns None for invalid token."""
    try:
        return float(token)
    except ValueError:
        return None


def tokenize(raw: str) -> list[str]:
    """Splits input text into tokens by common separators."""
    separators = [",", ";", "\n", "\t"]
    normalized = raw
    for sep in separators:
        normalized = normalized.replace(sep, " ")
    return [t for t in normalized.split(" ") if t != ""]


def op5_sum_numbers_with_correction(state: SessionState) -> None:
    """Operation 5: sum numbers replacing invalid tokens with chosen value."""
    path = pick_file(state)
    if path is None:
        return

    replacement_raw = input(
        "Replacement for invalid tokens (Enter for 0): "
    ).strip()
    replacement = 0.0 if replacement_raw == "" else float(replacement_raw)

    content = path.read_text(encoding="utf-8", errors="replace")
    tokens = tokenize(content)

    total = 0.0
    fixes: list[tuple[int, str, float]] = []

    for i, token in enumerate(tokens, 1):
        value = parse_numeric_token(token)
        if value is None:
            fixes.append((i, token, replacement))
            value = replacement
        total += value

    print(f"Tokens processed: {len(tokens)}")
    print(f"Sum: {total}")
    if fixes:
        print("Corrections:")
        for idx, bad, repl in fixes:
            print(f"  token #{idx}: '{bad}' -> {repl}")
    else:
        print("No corrections needed.")

    write_protocol(state, f"Operation 5: sum numbers from {path}")
    write_protocol(state, f"Replacement value: {replacement}")
    write_protocol(state, f"Tokens processed: {len(tokens)}")
    write_protocol(state, f"Sum: {total}")
    if fixes:
        for idx, bad, repl in fixes:
            write_protocol(state, f"Corrected token #{idx}: '{bad}' -> {repl}")
    else:
        write_protocol(state, "No corrections needed.")


def print_menu() -> None:
    """Prints the menu of operations."""
    print("\nLab 2 - File Attributes and Properties")
    print("1 - Find and show full names (*.dat)")
    print("2 - Show full path from disk root")
    print("3 - Show file properties and attributes")
    print("4 - Show text of one file")
    print("5 - Sum numbers with correction")
    print("6 - Toggle protocol logging")
    print("0 - Exit")


def main() -> None:
    """Main dialog loop."""
    base_dir = Path.cwd()
    state = SessionState(
        dat_files=[],
        protocol_enabled=True,
        protocol_path=base_dir / "lab2_protocol.txt",
    )

    write_protocol(state, "=== Program started ===")
    write_protocol(state, f"Working directory: {base_dir}")

    while True:
        print_menu()
        choice = input("Choose operation: ").strip()

        if choice == "1":
            op1_list_full_names(state, base_dir)
        elif choice == "2":
            op2_show_full_path(state)
        elif choice == "3":
            op3_show_properties(state)
        elif choice == "4":
            op4_show_text(state)
        elif choice == "5":
            try:
                op5_sum_numbers_with_correction(state)
            except ValueError:
                msg = "Replacement value must be numeric."
                print(msg)
                write_protocol(state, msg)
        elif choice == "6":
            state.protocol_enabled = not state.protocol_enabled
            status = "ON" if state.protocol_enabled else "OFF"
            print(f"Protocol logging is now: {status}")
            write_protocol(state, f"Protocol switched to {status}")
        elif choice == "0":
            write_protocol(state, "=== Program finished ===")
            print("Goodbye.")
            break
        else:
            print("Unknown command.")


if __name__ == "__main__":
    main()
