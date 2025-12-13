using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;

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
                var latest = doc.RootElement.GetProperty("latestVersion").GetString();
                var url = doc.RootElement.GetProperty("downloadUrl").GetString();

                var current = typeof(App).Assembly.GetName().Version?.ToString();

                if (latest != null && current != null && latest != current)
                {
                    var result = MessageBox.Show(
                        $"New update available!\n\nCurrent: {current}\nLatest: {latest}",
                        "Ikiflow Update",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Information);

                    if (result == MessageBoxResult.Yes)
                    {
                        System.Diagnostics.Process.Start(
                            new System.Diagnostics.ProcessStartInfo
                            {
                                FileName = url,
                                UseShellExecute = true
                            });
                    }
                }
            }
            catch
            {
                // Silent fail — no internet, no noise
            }
        }
    }
}
