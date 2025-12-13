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
                using var client = new HttpClient();
                var json = await client.GetStringAsync(UpdateUrl);

                var doc = JsonDocument.Parse(json);
                var latestString = doc.RootElement.GetProperty("latestVersion").GetString();
                var downloadUrl = doc.RootElement.GetProperty("downloadUrl").GetString();

                if (latestString == null || downloadUrl == null)
                    return;

                // ✅ Proper version comparison
                var latestVersion = new Version(latestString);
                var currentVersion = typeof(App).Assembly.GetName().Version;

                if (currentVersion == null)
                    return;

                if (latestVersion > currentVersion)
                {
                    var result = MessageBox.Show(
                        $"New update available!\n\nCurrent: {currentVersion}\nLatest: {latestVersion}",
                        "Ikiflow Update",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Information);

                    if (result == MessageBoxResult.Yes)
                    {
                        Process.Start(new ProcessStartInfo
                        {
                            FileName = downloadUrl,
                            UseShellExecute = true
                        });
                    }
                }
            }
            catch
            {
                // silent fail
            }
        }
    }
}
