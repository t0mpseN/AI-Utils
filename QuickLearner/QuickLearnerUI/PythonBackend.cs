using System;
using System.Diagnostics;
using System.IO;
using System.Text;

namespace QuickLearnerUI
{
    public class PythonBackend
    {
        private Process process = null!; // tell compiler "I will initialize it"
        private StreamWriter? stdin;
        public event Action<string> OnOutput = delegate { };

        private readonly string pythonExe;
        private readonly string scriptPath;

        public PythonBackend(string filePath)
        {
            pythonExe = Path.GetFullPath(@"../PythonBackend/venv/Scripts/python.exe");
            scriptPath = Path.GetFullPath(@"../PythonBackend/main.py");

            StartPythonProcess(filePath);
            // Uncomment the below line to debug with visible terminal window (no comms)
            //StartPythonProcessWithTerminal(filePath);
        }

        private void StartPythonProcess(string filePath)
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = $"\"{scriptPath}\" \"{filePath}\"",
                WorkingDirectory = Path.GetFullPath("../PythonBackend"),
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            process = new Process { StartInfo = startInfo };
            process.OutputDataReceived += (s, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                    OnOutput?.Invoke("[Python] " + e.Data);
            };
            process.ErrorDataReceived += (s, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                    OnOutput?.Invoke("[Python ERROR] " + e.Data);
            };

            try
            {
                process.Start();

                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                stdin = process.StandardInput;
            }
            catch (Exception ex)
            {
                OnOutput?.Invoke("Erro ao iniciar Python: " + ex.Message);
            }
        }

        private void StartPythonProcessWithTerminal(string filePath)
        {
            // Build command line to run python script with argument in your venv
            string cmdArgs = $"/k \"\"{pythonExe}\" \"{scriptPath}\" \"{filePath}\"\"";

            var startInfo = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = cmdArgs,
                WorkingDirectory = Path.GetFullPath("../PythonBackend"),
                UseShellExecute = true,    // must be true for terminal window
                CreateNoWindow = false     // show terminal window
            };

            Process.Start(startInfo);
        }

        public void Send(string input)
        {
            if (!process.HasExited)
                stdin?.WriteLine(input);
        }
    }
}
