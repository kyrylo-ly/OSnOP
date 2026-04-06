#include <Windows.h>

#include <cassert>
#include <cstring>
#include <iostream>

#include "../../lab5/DllProject/Lab5Dll.h"

#pragma comment(lib, "Lab5Dll.lib")

int main() {
    const DOUBLE loads[] = {45.2, 61.0, 72.5, 58.0};
    INT peakIndex = -1;
    DOUBLE avgLoad = 0.0;
    BOOL hasHigh = AnalyzeCpuLoadW(loads, 4, 70.0, &peakIndex, &avgLoad);
    assert(hasHigh == TRUE);
    assert(peakIndex == 2);
    assert(avgLoad > 59.16 && avgLoad < 59.18);

    const INT states[] = {1, 1, 2, 2, 3, 3, 3, 2};
    INT longestRun = 0;
    INT transitionsIgnore = CountStableTransitionsW(states, 8, TRUE, &longestRun);
    assert(transitionsIgnore == 3);
    assert(longestRun == 3);

    INT transitionsAll = CountStableTransitionsW(states, 8, FALSE, &longestRun);
    assert(transitionsAll == 7);
    assert(longestRun == 3);

    DOUBLE cost = EstimateDeliveryCostW(120, 8.0, 1.7, TRUE, 80);
    assert(cost > 34.59 && cost < 34.60);

    DOUBLE badCost = EstimateDeliveryCostW(-1, 8.0, 1.7, TRUE, 80);
    assert(badCost == -1.0);

    CHAR tag[32] = {0};
    BOOL tagOk = BuildUserTagW("Ada Lovelace", '-', 42, tag, 32);
    assert(tagOk == TRUE);
    assert(std::strcmp(tag, "AL-0042") == 0);

    CHAR badTag[8] = {0};
    BOOL tagFail = BuildUserTagW("1234", '-', 10, badTag, 8);
    assert(tagFail == FALSE);

    INT score = 0;
    INT clsStrong = EvaluatePasswordStrengthW("Lab5#Secure2026", 10, TRUE, '#', &score);
    assert(clsStrong == 4);
    assert(score == 100);

    INT scoreWeak = 0;
    INT clsWeak = EvaluatePasswordStrengthW("abc", 10, TRUE, '#', &scoreWeak);
    assert(clsWeak == 0);
    assert(scoreWeak >= 0 && scoreWeak < 30);

    std::cout << "Implicit linking: all DLL tests passed.\n";
    std::cout << "avgLoad=" << avgLoad << ", peakIndex=" << peakIndex << ", cost=" << cost << "\n";
    std::cout << "tag=" << tag << ", strongScore=" << score << ", weakScore=" << scoreWeak << "\n";

    return 0;
}
