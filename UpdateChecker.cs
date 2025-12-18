using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Diagnostics;

namespace Ikiflow
{
    public static class UpdateChecker
    {
        private const string UpdateUrl =
            "https://raw.githubusercontent.com/designswithharshit/ikiflow/main/update.json";

        public static async Task CheckForUpdateAsync()
        {
            try
            {
                using var client = new HttpClient
                {
                    Timeout = TimeSpan.FromSeconds(5)
                };

                var json = await client.GetStringAsync(UpdateUrl);

                if (string.IsNullOrWhiteSpace(json))
                    return;

                using var doc = JsonDocument.Parse(json);

                if (!doc.RootElement.TryGetProperty("latestVersion", out var latestProp))
                    return;

                if (!doc.RootElement.TryGetProperty("downloadUrl", out var urlProp))
                    return;

                var latestString = latestProp.GetString();
                var downloadUrl = urlProp.GetString();

                if (!Version.TryParse(latestString, out var latestVersion))
                    return;

                var currentVersion = typeof(App).Assembly.GetName().Version;
                if (currentVersion == null)
                    return;

                if (latestVersion <= currentVersion)
                    return;

                var result = MessageBox.Show(
                    $"New update available.\n\n" +
                    $"Current: {currentVersion}\n" +
                    $"Latest: {latestVersion}\n\n" +
                    $"Download now?",
                    "Ikiflow Update",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Information
                );

                if (result == MessageBoxResult.Yes)
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = downloadUrl,
                        UseShellExecute = true
                    });
                }
            }
            catch
            {
                // ABSOLUTE RULE:
                // Updater must never crash the app.
            }
        }
    }
}
