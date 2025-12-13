using System;
using System.Windows;
using System.Windows.Threading;

namespace Ikiflow
{
    public partial class App : Application
    {
        public App()
        {
            this.DispatcherUnhandledException += Crash;
        }

        protected override async void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            await UpdateChecker.CheckForUpdateAsync();
        }

        private void Crash(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            MessageBox.Show(
                $"MAIN ERROR:\n{e.Exception.Message}\n\n" +
                $"INNER STACK:\n{e.Exception.InnerException?.StackTrace}\n\n" +
                $"INNER ERROR:\n{e.Exception.InnerException?.Message}\n\n" +
                $"STACK:\n{e.Exception.StackTrace}",
                "Ikiflow Crash",
                MessageBoxButton.OK,
                MessageBoxImage.Error
            );

            e.Handled = true;
        }
    }
}
