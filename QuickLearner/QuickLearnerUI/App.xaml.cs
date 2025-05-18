using System;
using System.Windows;

namespace QuickLearnerUI
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            var fileSelector = new FileSelectorWindow();
            bool? result = fileSelector.ShowDialog();

            if (result == true && !string.IsNullOrEmpty(fileSelector.SelectedFile))
            {
                try
                {
                    var backend = new PythonBackend(fileSelector.SelectedFile);
                    var chatWindow = new ChatWindow(backend);

                    this.MainWindow = chatWindow;
                    chatWindow.Show();
                    return;           // exibe janela de chat
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Erro ao iniciar ChatWindow: " + ex.Message);
                    Shutdown(); // encerra com erro
                }
            }
            else
            {
                Shutdown(); // usuário cancelou seleção de arquivo
            }
        }
    }
}
