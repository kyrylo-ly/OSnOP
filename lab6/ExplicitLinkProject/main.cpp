#include <Windows.h>

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>

struct DllApi {
    BOOL (*AnalyzeCpuLoadW)(const DOUBLE*, INT, DOUBLE, PINT, DOUBLE*);
    INT (*CountStableTransitionsW)(const INT*, INT, BOOL, PINT);
    DOUBLE (*EstimateDeliveryCostW)(INT, DOUBLE, DOUBLE, BOOL, INT);
    BOOL (*BuildUserTagW)(LPCSTR, CHAR, INT, LPSTR, INT);
    INT (*EvaluatePasswordStrengthW)(LPCSTR, INT, BOOL, CHAR, PINT);
};

static HMODULE LoadLibraryWithFallback(const char** loadedFrom) {
    static const std::array<const char*, 4> kPaths = {
        "Lab5Dll.dll",
        "..\\Lab5Dll.dll",
        "..\\..\\Lab5Dll.dll",
        "..\\..\\..\\lab5\\x64\\Debug\\Lab5Dll.dll"
    };

    for (const char* path : kPaths) {
        HMODULE module = LoadLibraryA(path);
        if (module != nullptr) {
            *loadedFrom = path;
            return module;
        }
    }

    return nullptr;
}

static bool ResolveApi(HMODULE module, DllApi* api) {
    api->AnalyzeCpuLoadW = reinterpret_cast<BOOL (*)(const DOUBLE*, INT, DOUBLE, PINT, DOUBLE*)>(
        GetProcAddress(module, "AnalyzeCpuLoadW"));
    api->CountStableTransitionsW = reinterpret_cast<INT (*)(const INT*, INT, BOOL, PINT)>(
        GetProcAddress(module, "CountStableTransitionsW"));
    api->EstimateDeliveryCostW = reinterpret_cast<DOUBLE (*)(INT, DOUBLE, DOUBLE, BOOL, INT)>(
        GetProcAddress(module, "EstimateDeliveryCostW"));
    api->BuildUserTagW = reinterpret_cast<BOOL (*)(LPCSTR, CHAR, INT, LPSTR, INT)>(
        GetProcAddress(module, "BuildUserTagW"));
    api->EvaluatePasswordStrengthW = reinterpret_cast<INT (*)(LPCSTR, INT, BOOL, CHAR, PINT)>(
        GetProcAddress(module, "EvaluatePasswordStrengthW"));

    return api->AnalyzeCpuLoadW &&
           api->CountStableTransitionsW &&
           api->EstimateDeliveryCostW &&
           api->BuildUserTagW &&
           api->EvaluatePasswordStrengthW;
}

int main() {
    const char* loadedFrom = nullptr;
    HMODULE module = LoadLibraryWithFallback(&loadedFrom);
    if (!module) {
        std::cerr << "Could not load Lab5Dll.dll. Copy DLL to EXE folder or update path list in source.\n";
        return 1;
    }

    DllApi api{};
    if (!ResolveApi(module, &api)) {
        std::cerr << "Failed to resolve one or more exported functions from DLL.\n";
        FreeLibrary(module);
        return 2;
    }

    const DOUBLE loads[] = {45.2, 61.0, 72.5, 58.0};
    INT peakIndex = -1;
    DOUBLE avgLoad = 0.0;
    BOOL hasHigh = api.AnalyzeCpuLoadW(loads, 4, 70.0, &peakIndex, &avgLoad);
    assert(hasHigh == TRUE);
    assert(peakIndex == 2);
    assert(avgLoad > 59.16 && avgLoad < 59.18);

    const INT states[] = {1, 1, 2, 2, 3, 3, 3, 2};
    INT longestRun = 0;
    INT transitionsIgnore = api.CountStableTransitionsW(states, 8, TRUE, &longestRun);
    assert(transitionsIgnore == 3);
    assert(longestRun == 3);

    INT transitionsAll = api.CountStableTransitionsW(states, 8, FALSE, &longestRun);
    assert(transitionsAll == 7);
    assert(longestRun == 3);

    DOUBLE cost = api.EstimateDeliveryCostW(120, 8.0, 1.7, TRUE, 80);
    assert(cost > 34.59 && cost < 34.60);

    DOUBLE badCost = api.EstimateDeliveryCostW(-1, 8.0, 1.7, TRUE, 80);
    assert(badCost == -1.0);

    CHAR tag[32] = {0};
    BOOL tagOk = api.BuildUserTagW("Ada Lovelace", '-', 42, tag, 32);
    assert(tagOk == TRUE);
    assert(std::strcmp(tag, "AL-0042") == 0);

    CHAR badTag[8] = {0};
    BOOL tagFail = api.BuildUserTagW("1234", '-', 10, badTag, 8);
    assert(tagFail == FALSE);

    INT score = 0;
    INT clsStrong = api.EvaluatePasswordStrengthW("Lab5#Secure2026", 10, TRUE, '#', &score);
    assert(clsStrong == 4);
    assert(score == 100);

    INT scoreWeak = 0;
    INT clsWeak = api.EvaluatePasswordStrengthW("abc", 10, TRUE, '#', &scoreWeak);
    assert(clsWeak == 0);
    assert(scoreWeak >= 0 && scoreWeak < 30);

    std::cout << "Explicit linking: all DLL tests passed.\n";
    std::cout << "Loaded from: " << loadedFrom << "\n";
    std::cout << "avgLoad=" << avgLoad << ", peakIndex=" << peakIndex << ", cost=" << cost << "\n";
    std::cout << "tag=" << tag << ", strongScore=" << score << ", weakScore=" << scoreWeak << "\n";

    FreeLibrary(module);
    return 0;
}
