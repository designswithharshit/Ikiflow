using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Threading;
using System.Windows.Media.Animation;

namespace Ikiflow
{
    public partial class OverlayWindow : Window
    {
        private int _breakSeconds;

        public OverlayWindow(int breakSeconds)
        {
            InitializeComponent();

            _breakSeconds = breakSeconds;

            this.IsHitTestVisible = false;

            int countdown = _breakSeconds;
            BreakProgress.Maximum = countdown;
            BreakProgress.Value = countdown;

            var progressTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromSeconds(1)
            };

            progressTimer.Tick += (s, e) =>
            {
                countdown = Math.Max(0, countdown - 1);
                BreakProgress.Value = countdown;

                if (countdown <= 0)
                    progressTimer.Stop();
            };

            progressTimer.Start();

            var closeTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromSeconds(_breakSeconds)
            };

            closeTimer.Tick += (s, e) =>
            {
                closeTimer.Stop();
                FadeOutAndClose();
            };

            closeTimer.Start();
            }

            private void FadeOutAndClose()
            {
            var fade = new System.Windows.Media.Animation.DoubleAnimation
            {
                From = 0.85,
                To = 0,
                Duration = TimeSpan.FromSeconds(1)
            };

            fade.Completed += (s, e) => Close();
            BeginAnimation(Window.OpacityProperty, fade);
        }
    }

}
