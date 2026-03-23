#pragma once

#include <Windows.h>

#ifdef LAB5DLL_EXPORTS
#define LAB5_API extern "C" __declspec(dllexport)
#else
#define LAB5_API extern "C" __declspec(dllimport)
#endif

LAB5_API BOOL AnalyzeCpuLoadW(const DOUBLE* loads, INT count, DOUBLE highThreshold, PINT peakIndex, DOUBLE* averageLoad);
LAB5_API INT CountStableTransitionsW(const INT* states, INT count, BOOL ignoreRepeats, PINT longestRun);
LAB5_API DOUBLE EstimateDeliveryCostW(INT distanceKm, DOUBLE fuelPer100Km, DOUBLE fuelPrice, BOOL returnTrip, INT cargoKg);
LAB5_API BOOL BuildUserTagW(LPCSTR fullName, CHAR separator, INT serial, LPSTR outTag, INT outTagSize);
LAB5_API INT EvaluatePasswordStrengthW(LPCSTR password, INT minLength, BOOL requireSpecial, CHAR requiredSpecial, PINT score);
