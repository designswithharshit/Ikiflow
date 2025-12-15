using System;
using System.Windows;
using System.Windows.Threading;

namespace Ikiflow
{
    public partial class MainWindow : Window
    {
        private FloatingWidget _widget;
        private readonly DispatcherTimer _timer;

        // --- TIME CONFIG ---
        private TimeSpan _screenTime = TimeSpan.FromMinutes(30);
        private TimeSpan _breakTime  = TimeSpan.FromSeconds(300);

        // --- RUNTIME STATE ---
        private TimeSpan _remaining;
        private bool _isRunning;
        private bool _uiReady = false;

        public MainWindow()
        {
            InitializeComponent();

            _remaining = _screenTime;

            _timer = new DispatcherTimer
            {
                Interval = TimeSpan.FromSeconds(1)
            };
            _timer.Tick += Timer_Tick;

            _uiReady = true; // VERY IMPORTANT
        }

        // =========================
        // SCREEN TIME CONTROL
        // =========================
        private void IntervalSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (IntervalLabel == null) return;

            int minutes = (int)IntervalSlider.Value;
            _screenTime = TimeSpan.FromMinutes(minutes);

            IntervalLabel.Text = $"{minutes} min";

            // UI only
            if (!_isRunning)
            {
                CountdownText.Text = "Next: --";
                Title = "Ikiflow";
            }
        }

        // =========================
        // BREAK TIME CONTROL
        // =========================
        private bool _isUpdatingBreak;


        private void BreakSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (BreakLabel == null || _isUpdatingBreak) return;

            _isUpdatingBreak = true;

            int seconds = (int)BreakSlider.Value;
            _breakTime = TimeSpan.FromSeconds(seconds);

            BreakInput.Text = seconds.ToString();
            BreakLabel.Text = $"{seconds} sec";

            _isUpdatingBreak = false;
        }
        private void BreakInput_TextChanged(object sender, System.Windows.Controls.TextChangedEventArgs e)
        {
            if (!_uiReady || _isUpdatingBreak) return;
            if (BreakSlider == null || BreakLabel == null) return;

            if (int.TryParse(BreakInput.Text, out int seconds))
            {
                if (seconds < 10) seconds = 10;
                if (seconds > 600) seconds = 600;

                _isUpdatingBreak = true;

                _breakTime = TimeSpan.FromSeconds(seconds);
                BreakSlider.Value = seconds;
                BreakLabel.Text = $"{seconds} sec";

                _isUpdatingBreak = false;
            }
        }


        // =========================
        // START / PAUSE
        // =========================
        private void StartBtn_Click(object sender, RoutedEventArgs e)
        {
            _remaining = _screenTime;
            _isRunning = true;
            _timer.Start();

            IntervalSlider.IsEnabled = false;
            BreakSlider.IsEnabled = false;

            StatusText.Text = "Status: Running";
            Title = $"Ikiflow — {_remaining:mm\\:ss}";

            if (_widget == null)
            {
                _widget = new FloatingWidget();
                _widget.Show();
            }

            this.WindowState = WindowState.Minimized;

        }

        private void PauseBtn_Click(object sender, RoutedEventArgs e)
        {
            _isRunning = false;
            _timer.Stop();

            IntervalSlider.IsEnabled = true;
            BreakSlider.IsEnabled = true;

            StatusText.Text = "Status: Paused";
            Title = "Ikiflow — Paused";

            _widget?.UpdateTime("Paused");
        }

        // =========================
        // TIMER LOOP
        // =========================
        private void Timer_Tick(object sender, EventArgs e)
        {
            if (!_isRunning) return;

            _remaining -= TimeSpan.FromSeconds(1);

            if (_remaining <= TimeSpan.Zero)
            {
                EndScreenSession();
                return;
            }

            UpdateRunningUI();
        }

        private void UpdateRunningUI()
        {
            string time = _remaining.ToString(@"mm\:ss");

            CountdownText.Text = $"Next: {time}";
            Title = $"Ikiflow — {time}";

            _widget?.UpdateTime(time);

            double progress =
                _remaining.TotalSeconds / _screenTime.TotalSeconds;

            _widget?.UpdateProgress(progress);
        }

        // =========================
        // SCREEN SESSION END
        // =========================
        private void EndScreenSession()
        {
            _timer.Stop();
            _isRunning = false;

            IntervalSlider.IsEnabled = true;
            BreakSlider.IsEnabled = true;

            StatusText.Text = "Status: Break";

            _widget?.Close();
            _widget = null;

            ShowOverlay();
        }

        // =========================
        // BREAK OVERLAY
        // =========================
        private void ShowOverlay()
        {
            var overlay = new OverlayWindow((int)_breakTime.TotalSeconds);
            overlay.Show();

            // Prepare for next cycle
            StatusText.Text = "Status: Ready";
            CountdownText.Text = "Next: --";
            Title = "Ikiflow";
        }

        // =========================
        // OPTIONAL (TESTING)
        // =========================
        private void TestOverlayButton_Click(object sender, RoutedEventArgs e)
        {
            ShowOverlay();
        }

        protected override void OnClosed(EventArgs e)
        {
            _timer?.Stop();
            _widget?.Close();
            _widget = null;

            Application.Current.Shutdown();
            base.OnClosed(e);
        }
        
    }
    
}
