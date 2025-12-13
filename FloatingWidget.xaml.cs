using System;
using System.Windows;
using System.Windows.Shapes;


namespace Ikiflow
{
    public partial class FloatingWidget : Window
    {
        private Rectangle[] _bars;

        public FloatingWidget()
        {
            InitializeComponent();

            // Collect bars into an array for easy control
            _bars = new Rectangle[]
            {
                Bar0, Bar1, Bar2, Bar3, Bar4, Bar5,
                Bar6, Bar7, Bar8, Bar9, Bar10, Bar11
            };

            // Position at top center
            this.Left = (SystemParameters.PrimaryScreenWidth - this.Width) / 2;
            this.Top = 0;
        }

        // Update timer text
        public void UpdateTime(string text)
        {
            WidgetTime.Text = text;
        }

        // Bars disappear one-by-one based on progress
        public void UpdateProgress(double progress)
        {
            // progress: 1.0 = full remaining, 0.0 = finished
            int barsToShow = (int)Math.Ceiling(progress * _bars.Length);
            if (barsToShow > _bars.Length) barsToShow = _bars.Length;
            if (barsToShow < 0) barsToShow = 0;


            for (int i = 0; i < _bars.Length; i++)
            {
                _bars[i].Opacity = (i < barsToShow) ? 1.0 : 0.15;
            }
        }
    }
}
