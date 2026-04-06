using System;
using System.Runtime.InteropServices;
using System.Text;

internal static class Program
{
    private const string DllName = "Lab5Dll.dll";

    [DllImport(DllName, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool AnalyzeCpuLoadW(
        [In] double[] loads,
        int count,
        double highThreshold,
        out int peakIndex,
        out double averageLoad);

    [DllImport(DllName, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi, ExactSpelling = true)]
    private static extern int CountStableTransitionsW(
        [In] int[] states,
        int count,
        [MarshalAs(UnmanagedType.Bool)] bool ignoreRepeats,
        out int longestRun);

    [DllImport(DllName, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi, ExactSpelling = true)]
    private static extern double EstimateDeliveryCostW(
        int distanceKm,
        double fuelPer100Km,
        double fuelPrice,
        [MarshalAs(UnmanagedType.Bool)] bool returnTrip,
        int cargoKg);

    [DllImport(DllName, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool BuildUserTagW(
        string fullName,
        byte separator,
        int serial,
        StringBuilder outTag,
        int outTagSize);

    [DllImport(DllName, CallingConvention = CallingConvention.Cdecl, CharSet = CharSet.Ansi, ExactSpelling = true)]
    private static extern int EvaluatePasswordStrengthW(
        string password,
        int minLength,
        [MarshalAs(UnmanagedType.Bool)] bool requireSpecial,
        byte requiredSpecial,
        out int score);

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static void Main()
    {
        try
        {
            var loads = new[] { 45.2, 61.0, 72.5, 58.0 };
            bool hasHigh = AnalyzeCpuLoadW(loads, loads.Length, 70.0, out int peakIndex, out double avgLoad);
            Require(hasHigh, "AnalyzeCpuLoadW: expected hasHigh=true");
            Require(peakIndex == 2, "AnalyzeCpuLoadW: expected peakIndex=2");
            Require(avgLoad > 59.16 && avgLoad < 59.18, "AnalyzeCpuLoadW: average out of expected range");

            var states = new[] { 1, 1, 2, 2, 3, 3, 3, 2 };
            int transitionsIgnore = CountStableTransitionsW(states, states.Length, true, out int longestRun1);
            Require(transitionsIgnore == 3, "CountStableTransitionsW(ignore=true): expected transitions=3");
            Require(longestRun1 == 3, "CountStableTransitionsW(ignore=true): expected longestRun=3");

            int transitionsAll = CountStableTransitionsW(states, states.Length, false, out int longestRun2);
            Require(transitionsAll == 7, "CountStableTransitionsW(ignore=false): expected transitions=7");
            Require(longestRun2 == 3, "CountStableTransitionsW(ignore=false): expected longestRun=3");

            double cost = EstimateDeliveryCostW(120, 8.0, 1.7, true, 80);
            Require(cost > 34.59 && cost < 34.60, "EstimateDeliveryCostW: expected value in range 34.59..34.60");

            double badCost = EstimateDeliveryCostW(-1, 8.0, 1.7, true, 80);
            Require(Math.Abs(badCost - (-1.0)) < 1e-12, "EstimateDeliveryCostW: expected -1.0 for invalid input");

            var tag = new StringBuilder(32);
            bool tagOk = BuildUserTagW("Ada Lovelace", (byte)'-', 42, tag, tag.Capacity);
            Require(tagOk, "BuildUserTagW: expected success for valid name");
            Require(tag.ToString() == "AL-0042", "BuildUserTagW: expected AL-0042");

            var badTag = new StringBuilder(8);
            bool tagFail = BuildUserTagW("1234", (byte)'-', 10, badTag, badTag.Capacity);
            Require(!tagFail, "BuildUserTagW: expected fail for invalid fullName");

            int clsStrong = EvaluatePasswordStrengthW("Lab5#Secure2026", 10, true, (byte)'#', out int strongScore);
            Require(clsStrong == 4, "EvaluatePasswordStrengthW: expected class=4 for strong password");
            Require(strongScore == 100, "EvaluatePasswordStrengthW: expected score=100 for strong password");

            int clsWeak = EvaluatePasswordStrengthW("abc", 10, true, (byte)'#', out int weakScore);
            Require(clsWeak == 0, "EvaluatePasswordStrengthW: expected class=0 for weak password");
            Require(weakScore >= 0 && weakScore < 30, "EvaluatePasswordStrengthW: expected weak score in [0,30)");

            Console.WriteLine("C# implicit P/Invoke: all DLL tests passed.");
            Console.WriteLine($"avgLoad={avgLoad:F3}, peakIndex={peakIndex}, cost={cost:F4}");
            Console.WriteLine($"tag={tag}, strongScore={strongScore}, weakScore={weakScore}");
        }
        catch (DllNotFoundException ex)
        {
            Console.Error.WriteLine("Could not load Lab5Dll.dll. Place DLL near EXE or in PATH.");
            Console.Error.WriteLine(ex.Message);
            Environment.Exit(1);
        }
        catch (EntryPointNotFoundException ex)
        {
            Console.Error.WriteLine("One of exported functions was not found in Lab5Dll.dll.");
            Console.Error.WriteLine(ex.Message);
            Environment.Exit(2);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Test failed: {ex.Message}");
            Environment.Exit(3);
        }
    }
}
