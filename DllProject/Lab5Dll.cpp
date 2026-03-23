#define LAB5DLL_EXPORTS
#include "Lab5Dll.h"

#include <cctype>
#include <cstdio>
#include <cstring>

BOOL AnalyzeCpuLoadW(const DOUBLE* loads, INT count, DOUBLE highThreshold, PINT peakIndex, DOUBLE* averageLoad) {
    if (!loads || !peakIndex || !averageLoad || count <= 0) {
        return FALSE;
    }

    DOUBLE sum = 0.0;
    DOUBLE maxValue = loads[0];
    INT maxIdx = 0;
    BOOL hasHighLoad = FALSE;

    for (INT i = 0; i < count; ++i) {
        sum += loads[i];
        if (loads[i] > maxValue) {
            maxValue = loads[i];
            maxIdx = i;
        }
        if (loads[i] > highThreshold) {
            hasHighLoad = TRUE;
        }
    }

    *averageLoad = sum / static_cast<DOUBLE>(count);
    *peakIndex = maxIdx;
    return hasHighLoad;
}

INT CountStableTransitionsW(const INT* states, INT count, BOOL ignoreRepeats, PINT longestRun) {
    if (!states || !longestRun || count <= 0) {
        return -1;
    }

    INT transitions = 0;
    INT run = 1;
    INT maxRun = 1;

    for (INT i = 1; i < count; ++i) {
        if (states[i] == states[i - 1]) {
            ++run;
        } else {
            run = 1;
        }

        if (run > maxRun) {
            maxRun = run;
        }

        if (ignoreRepeats) {
            if (states[i] != states[i - 1]) {
                ++transitions;
            }
        } else {
            ++transitions;
        }
    }

    *longestRun = maxRun;
    return transitions;
}

DOUBLE EstimateDeliveryCostW(INT distanceKm, DOUBLE fuelPer100Km, DOUBLE fuelPrice, BOOL returnTrip, INT cargoKg) {
    if (distanceKm < 0 || fuelPer100Km <= 0.0 || fuelPrice <= 0.0 || cargoKg < 0) {
        return -1.0;
    }

    DOUBLE fuelLiters = (static_cast<DOUBLE>(distanceKm) / 100.0) * fuelPer100Km;
    if (returnTrip) {
        fuelLiters *= 2.0;
    }

    DOUBLE baseCost = fuelLiters * fuelPrice;
    INT overWeight = cargoKg > 50 ? (cargoKg - 50) : 0;
    DOUBLE surcharge = static_cast<DOUBLE>(overWeight) * 0.002;
    if (surcharge > 0.30) {
        surcharge = 0.30;
    }

    return baseCost * (1.0 + surcharge);
}

BOOL BuildUserTagW(LPCSTR fullName, CHAR separator, INT serial, LPSTR outTag, INT outTagSize) {
    if (!fullName || !outTag || outTagSize <= 0 || serial < 0) {
        return FALSE;
    }

    CHAR initials[3] = {0, 0, 0};
    INT initialsCount = 0;
    BOOL newWord = TRUE;

    for (INT i = 0; fullName[i] != '\0' && initialsCount < 2; ++i) {
        unsigned char ch = static_cast<unsigned char>(fullName[i]);
        if (std::isalpha(ch) && newWord) {
            initials[initialsCount++] = static_cast<CHAR>(std::toupper(ch));
            newWord = FALSE;
        } else if (fullName[i] == ' ' || fullName[i] == '-' || fullName[i] == '_') {
            newWord = TRUE;
        }
    }

    if (initialsCount == 0) {
        return FALSE;
    }
    if (initialsCount == 1) {
        initials[1] = 'X';
    }

    INT written = std::snprintf(outTag, static_cast<size_t>(outTagSize), "%c%c%c%04d",
                                initials[0], initials[1], separator, serial);
    return (written > 0 && written < outTagSize) ? TRUE : FALSE;
}

INT EvaluatePasswordStrengthW(LPCSTR password, INT minLength, BOOL requireSpecial, CHAR requiredSpecial, PINT score) {
    if (!password || !score || minLength <= 0) {
        return -1;
    }

    INT len = static_cast<INT>(std::strlen(password));
    BOOL hasUpper = FALSE;
    BOOL hasLower = FALSE;
    BOOL hasDigit = FALSE;
    BOOL hasAnySpecial = FALSE;
    BOOL hasRequiredSpecial = FALSE;

    for (INT i = 0; password[i] != '\0'; ++i) {
        unsigned char ch = static_cast<unsigned char>(password[i]);
        if (std::isupper(ch)) {
            hasUpper = TRUE;
        } else if (std::islower(ch)) {
            hasLower = TRUE;
        } else if (std::isdigit(ch)) {
            hasDigit = TRUE;
        } else {
            hasAnySpecial = TRUE;
            if (password[i] == requiredSpecial) {
                hasRequiredSpecial = TRUE;
            }
        }
    }

    INT localScore = 0;
    localScore += (len >= minLength) ? 20 : (len * 20 / minLength);
    localScore += hasUpper ? 20 : 0;
    localScore += hasLower ? 20 : 0;
    localScore += hasDigit ? 20 : 0;
    localScore += hasAnySpecial ? 20 : 0;

    if (requireSpecial && !hasRequiredSpecial) {
        localScore -= 15;
    }

    if (localScore < 0) {
        localScore = 0;
    }
    if (localScore > 100) {
        localScore = 100;
    }

    *score = localScore;

    if (localScore < 30) {
        return 0;
    }
    if (localScore < 50) {
        return 1;
    }
    if (localScore < 70) {
        return 2;
    }
    if (localScore < 85) {
        return 3;
    }
    return 4;
}
