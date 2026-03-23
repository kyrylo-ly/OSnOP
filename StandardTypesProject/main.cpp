#include <cassert>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <iostream>

// Prototypes
bool AnalyzeCpuLoad(const double* loads, int count, double highThreshold, int* peakIndex, double* averageLoad);
int CountStableTransitions(const int* states, int count, bool ignoreRepeats, int* longestRun);
double EstimateDeliveryCost(int distanceKm, double fuelPer100Km, double fuelPrice, bool returnTrip, int cargoKg);
bool BuildUserTag(const char* fullName, char separator, int serial, char* outTag, int outTagSize);
int EvaluatePasswordStrength(const char* password, int minLength, bool requireSpecial, char requiredSpecial, int* score);

bool AnalyzeCpuLoad(const double* loads, int count, double highThreshold, int* peakIndex, double* averageLoad) {
    if (!loads || !peakIndex || !averageLoad || count <= 0) {
        return false;
    }

    double sum = 0.0;
    double maxValue = loads[0];
    int maxIdx = 0;
    bool hasHighLoad = false;

    for (int i = 0; i < count; ++i) {
        sum += loads[i];
        if (loads[i] > maxValue) {
            maxValue = loads[i];
            maxIdx = i;
        }
        if (loads[i] > highThreshold) {
            hasHighLoad = true;
        }
    }

    *averageLoad = sum / static_cast<double>(count);
    *peakIndex = maxIdx;
    return hasHighLoad;
}

int CountStableTransitions(const int* states, int count, bool ignoreRepeats, int* longestRun) {
    if (!states || !longestRun || count <= 0) {
        return -1;
    }

    int transitions = 0;
    int run = 1;
    int maxRun = 1;

    for (int i = 1; i < count; ++i) {
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

double EstimateDeliveryCost(int distanceKm, double fuelPer100Km, double fuelPrice, bool returnTrip, int cargoKg) {
    if (distanceKm < 0 || fuelPer100Km <= 0.0 || fuelPrice <= 0.0 || cargoKg < 0) {
        return -1.0;
    }

    double fuelLiters = (static_cast<double>(distanceKm) / 100.0) * fuelPer100Km;
    if (returnTrip) {
        fuelLiters *= 2.0;
    }

    double baseCost = fuelLiters * fuelPrice;
    int overWeight = cargoKg > 50 ? (cargoKg - 50) : 0;
    double surcharge = static_cast<double>(overWeight) * 0.002;
    if (surcharge > 0.30) {
        surcharge = 0.30;
    }

    return baseCost * (1.0 + surcharge);
}

bool BuildUserTag(const char* fullName, char separator, int serial, char* outTag, int outTagSize) {
    if (!fullName || !outTag || outTagSize <= 0 || serial < 0) {
        return false;
    }

    char initials[3] = {0, 0, 0};
    int initialsCount = 0;
    bool newWord = true;

    for (int i = 0; fullName[i] != '\0' && initialsCount < 2; ++i) {
        unsigned char ch = static_cast<unsigned char>(fullName[i]);
        if (std::isalpha(ch) && newWord) {
            initials[initialsCount++] = static_cast<char>(std::toupper(ch));
            newWord = false;
        } else if (fullName[i] == ' ' || fullName[i] == '-' || fullName[i] == '_') {
            newWord = true;
        }
    }

    if (initialsCount == 0) {
        return false;
    }
    if (initialsCount == 1) {
        initials[1] = 'X';
    }

    int written = std::snprintf(outTag, static_cast<size_t>(outTagSize), "%c%c%c%04d",
                                initials[0], initials[1], separator, serial);
    return written > 0 && written < outTagSize;
}

int EvaluatePasswordStrength(const char* password, int minLength, bool requireSpecial, char requiredSpecial, int* score) {
    if (!password || !score || minLength <= 0) {
        return -1;
    }

    int len = static_cast<int>(std::strlen(password));
    bool hasUpper = false;
    bool hasLower = false;
    bool hasDigit = false;
    bool hasAnySpecial = false;
    bool hasRequiredSpecial = false;

    for (int i = 0; password[i] != '\0'; ++i) {
        unsigned char ch = static_cast<unsigned char>(password[i]);
        if (std::isupper(ch)) {
            hasUpper = true;
        } else if (std::islower(ch)) {
            hasLower = true;
        } else if (std::isdigit(ch)) {
            hasDigit = true;
        } else {
            hasAnySpecial = true;
            if (password[i] == requiredSpecial) {
                hasRequiredSpecial = true;
            }
        }
    }

    int localScore = 0;
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

int main() {
    const double loads[] = {45.2, 61.0, 72.5, 58.0};
    int peakIndex = -1;
    double avgLoad = 0.0;
    bool hasHigh = AnalyzeCpuLoad(loads, 4, 70.0, &peakIndex, &avgLoad);
    assert(hasHigh == true);
    assert(peakIndex == 2);

    const int states[] = {1, 1, 2, 2, 3, 3, 3, 2};
    int longestRun = 0;
    int transitions = CountStableTransitions(states, 8, true, &longestRun);
    assert(transitions == 3);
    assert(longestRun == 3);

    double cost = EstimateDeliveryCost(120, 8.0, 1.7, true, 80);
    assert(cost > 34.59 && cost < 34.60);

    char tag[32] = {0};
    bool tagOk = BuildUserTag("Ada Lovelace", '-', 42, tag, 32);
    assert(tagOk == true);
    assert(std::strcmp(tag, "AL-0042") == 0);

    int score = 0;
    int cls = EvaluatePasswordStrength("Lab5#Secure2026", 10, true, '#', &score);
    assert(cls == 4);
    assert(score == 100);

    std::cout << "All standard-type tests passed.\n";
    std::cout << "avgLoad=" << avgLoad << ", peakIndex=" << peakIndex << ", cost=" << cost << "\n";
    std::cout << "tag=" << tag << ", passwordScore=" << score << "\n";

    return 0;
}
