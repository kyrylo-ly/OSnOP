import ctypes
import os
import sys


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_dll() -> ctypes.CDLL:
    search_paths = [
        "Lab5Dll.dll",
        os.path.join(os.path.dirname(__file__), "Lab5Dll.dll"),
        os.path.join(os.path.dirname(__file__), "..", "Lab5Dll.dll"),
    ]

    last_error = None
    for path in search_paths:
        try:
            return ctypes.CDLL(path)
        except OSError as ex:
            last_error = ex

    raise OSError(f"Could not load Lab5Dll.dll from known paths. Last error: {last_error}")


def main() -> int:
    if os.name != "nt":
        print("This test is intended for Windows because it loads a Win32 DLL.")
        return 1

    dll = load_dll()

    BOOL = ctypes.c_int
    INT = ctypes.c_int
    DOUBLE = ctypes.c_double
    CHAR = ctypes.c_char

    dll.AnalyzeCpuLoadW.argtypes = [
        ctypes.POINTER(DOUBLE),
        INT,
        DOUBLE,
        ctypes.POINTER(INT),
        ctypes.POINTER(DOUBLE),
    ]
    dll.AnalyzeCpuLoadW.restype = BOOL

    dll.CountStableTransitionsW.argtypes = [
        ctypes.POINTER(INT),
        INT,
        BOOL,
        ctypes.POINTER(INT),
    ]
    dll.CountStableTransitionsW.restype = INT

    dll.EstimateDeliveryCostW.argtypes = [INT, DOUBLE, DOUBLE, BOOL, INT]
    dll.EstimateDeliveryCostW.restype = DOUBLE

    dll.BuildUserTagW.argtypes = [ctypes.c_char_p, CHAR, INT, ctypes.c_char_p, INT]
    dll.BuildUserTagW.restype = BOOL

    dll.EvaluatePasswordStrengthW.argtypes = [ctypes.c_char_p, INT, BOOL, CHAR, ctypes.POINTER(INT)]
    dll.EvaluatePasswordStrengthW.restype = INT

    loads = (DOUBLE * 4)(45.2, 61.0, 72.5, 58.0)
    peak_index = INT(-1)
    avg_load = DOUBLE(0.0)
    has_high = dll.AnalyzeCpuLoadW(loads, 4, DOUBLE(70.0), ctypes.byref(peak_index), ctypes.byref(avg_load))
    require(has_high != 0, "AnalyzeCpuLoadW: expected hasHigh=true")
    require(peak_index.value == 2, "AnalyzeCpuLoadW: expected peakIndex=2")
    require(59.16 < avg_load.value < 59.18, "AnalyzeCpuLoadW: average out of expected range")

    states = (INT * 8)(1, 1, 2, 2, 3, 3, 3, 2)
    longest_run = INT(0)
    transitions_ignore = dll.CountStableTransitionsW(states, 8, BOOL(1), ctypes.byref(longest_run))
    require(transitions_ignore == 3, "CountStableTransitionsW(ignore=true): expected transitions=3")
    require(longest_run.value == 3, "CountStableTransitionsW(ignore=true): expected longestRun=3")

    transitions_all = dll.CountStableTransitionsW(states, 8, BOOL(0), ctypes.byref(longest_run))
    require(transitions_all == 7, "CountStableTransitionsW(ignore=false): expected transitions=7")
    require(longest_run.value == 3, "CountStableTransitionsW(ignore=false): expected longestRun=3")

    cost = dll.EstimateDeliveryCostW(INT(120), DOUBLE(8.0), DOUBLE(1.7), BOOL(1), INT(80))
    require(34.59 < cost < 34.60, "EstimateDeliveryCostW: expected value in range 34.59..34.60")

    bad_cost = dll.EstimateDeliveryCostW(INT(-1), DOUBLE(8.0), DOUBLE(1.7), BOOL(1), INT(80))
    require(abs(bad_cost - (-1.0)) < 1e-12, "EstimateDeliveryCostW: expected -1.0 for invalid input")

    tag_buffer = ctypes.create_string_buffer(32)
    tag_ok = dll.BuildUserTagW(b"Ada Lovelace", CHAR(b"-"), INT(42), tag_buffer, INT(32))
    require(tag_ok != 0, "BuildUserTagW: expected success for valid name")
    require(tag_buffer.value.decode("ascii") == "AL-0042", "BuildUserTagW: expected AL-0042")

    bad_tag = ctypes.create_string_buffer(8)
    tag_fail = dll.BuildUserTagW(b"1234", CHAR(b"-"), INT(10), bad_tag, INT(8))
    require(tag_fail == 0, "BuildUserTagW: expected fail for invalid fullName")

    strong_score = INT(0)
    cls_strong = dll.EvaluatePasswordStrengthW(b"Lab5#Secure2026", INT(10), BOOL(1), CHAR(b"#"), ctypes.byref(strong_score))
    require(cls_strong == 4, "EvaluatePasswordStrengthW: expected class=4 for strong password")
    require(strong_score.value == 100, "EvaluatePasswordStrengthW: expected score=100 for strong password")

    weak_score = INT(0)
    cls_weak = dll.EvaluatePasswordStrengthW(b"abc", INT(10), BOOL(1), CHAR(b"#"), ctypes.byref(weak_score))
    require(cls_weak == 0, "EvaluatePasswordStrengthW: expected class=0 for weak password")
    require(0 <= weak_score.value < 30, "EvaluatePasswordStrengthW: expected weak score in [0,30)")

    print("Python ctypes: all DLL tests passed.")
    print(f"avgLoad={avg_load.value:.3f}, peakIndex={peak_index.value}, cost={cost:.4f}")
    print(f"tag={tag_buffer.value.decode('ascii')}, strongScore={strong_score.value}, weakScore={weak_score.value}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as ex:
        print(f"Test failed: {ex}", file=sys.stderr)
        raise SystemExit(2)
