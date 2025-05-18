using Microsoft.Win32;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows;

namespace QuickLearnerUI
{
    public partial class FileSelectorWindow : Window
    {
        public FileSelectorWindow()
        {
            InitializeComponent();
        }

        public string? SelectedFile { get; private set; }

        private void SelectButton_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Microsoft.Win32.OpenFileDialog();
            dialog.Filter = "Documentos|*.chm;*.pdf;*.html";
            if (dialog.ShowDialog() == true)
            {
                SelectedFile = dialog.FileName;
                DialogResult = true;
                Close();
            }
        }
    }
}