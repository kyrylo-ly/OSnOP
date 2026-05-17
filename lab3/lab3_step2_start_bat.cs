using System;
using System.Diagnostics;
using System.IO;

internal static class Program
{
    private static int Main(string[] args)
    {
        string batPath = args.Length > 0 ? args[0] : "lab3_step1_notepad.bat";
        string fullPath = Path.GetFullPath(batPath);

        if (!File.Exists(fullPath))
        {
            Console.Error.WriteLine($"BAT file not found: {fullPath}");
            return 1;
        }

        var info = new ProcessStartInfo
        {
            FileName = fullPath,
            UseShellExecute = true,
            WorkingDirectory = Path.GetDirectoryName(fullPath) ?? Directory.GetCurrentDirectory()
        };

        Process? process = Process.Start(info);
        if (process == null)
        {
            Console.Error.WriteLine("Could not start BAT process.");
            return 2;
        }

        Console.WriteLine($"Started BAT: {fullPath}");
        Console.WriteLine($"PID: {process.Id}");
        return 0;
    }
}
