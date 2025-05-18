using System;
using System.Diagnostics;
using System.Net;  // Para WebUtility
using System.Windows;
using System.Windows.Documents;
using System.Windows.Controls;         // Para RichTextBox, Border, ScrollViewer, TextBox, Button...
using System.Windows.Media;            // Para Brushes, Colors, etc.
using System.Windows.Input;            // Para eventos de input (opcional)
using System.Windows.Threading;       // Para Dispatcher.Invoke (se já estiver usando)
using System.Windows.Shapes;           // Para formas (opcional)
using System.Windows.Controls.Primitives; // Para ScrollViewer
using System.Windows.Media.Animation;  // Para animações (opcional)
using System.Windows.Media.Effects;    // Para efeitos (opcional)
using System.Windows.Media.TextFormatting; // Texto avançado (opcional)
using System.Windows.Media.Imaging;   // Para imagens (opcional)
using Markdig;

namespace QuickLearnerUI
{
    public partial class ChatWindow : Window
    {
        private PythonBackend backend;

        private FlowDocument chatDocument = new();

        public ChatWindow(PythonBackend backend)
        {
            InitializeComponent();
            
            this.backend = backend;
            backend.OnOutput += AppendText;

            //ChatViewer.Document = chatDocument;

            this.Closed += (s, e) => Environment.Exit(0); // 🔥 Fecha tudo, inclusive dotnet run
        }

        private async void AppendText(string text)
        {
            if (text.StartsWith("[Python]"))
                text = text.Replace("[Python] ", "");

            if (text.Trim().StartsWith("{") && text.Contains("\"answer\""))
            {
                try
                {
                    var answer = System.Text.Json.JsonDocument.Parse(text).RootElement.GetProperty("answer").GetString();
                    var op = Dispatcher.InvokeAsync(() => AnimateTyping(answer ?? "", isUser: false));
                    await op.Task;
                }
                catch
                {
                    var op = Dispatcher.InvokeAsync(() => AnimateTyping("❌ Erro ao ler resposta da IA.", isUser: false));
                    await op.Task;
                }
            }
            else
            {
                var op = Dispatcher.InvokeAsync(() => AnimateTyping(text, isUser: false));
                await op.Task;
            }
        }


        private async void Enviar_Click(object sender, RoutedEventArgs e)
        {
            var input = InputBox.Text.Trim();
            if (!string.IsNullOrEmpty(input))
            {
                await AnimateTyping(input, isUser: true);

                var jsonInput = $"{{\"question\": \"{input.Replace("\"", "\\\"")}\"}}";
                backend.Send(jsonInput);

                InputBox.Clear();
            }
        }

        private void InputBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter && !Keyboard.IsKeyDown(Key.LeftShift) && !Keyboard.IsKeyDown(Key.RightShift))
            {
                Enviar_Click(sender, e);
                e.Handled = true; // Evita quebra de linha
            }
        }
        /*
                private void AddMarkdownBubble(string markdown, bool isUser)
                {
                    // Decodifica as entidades HTML (como &quot; para ")
                    string decodedMarkdown = WebUtility.HtmlDecode(markdown);

                    // Converte Markdown para HTML
                    string html = Markdown.ToHtml(decodedMarkdown);

                    // Converte HTML para FlowDocument (você pode usar seu HtmlToFlowDocumentConverter)
                    FlowDocument doc = HtmlToFlowDocumentConverter.Convert(html);

                    var richTextBox = new RichTextBox
                    {
                        Document = doc,
                        IsReadOnly = true,
                        Background = Brushes.Transparent,
                        BorderThickness = new Thickness(0),
                        Padding = new Thickness(0),
                        Width = 600,
                    };

                    var border = new Border
                    {
                        Background = isUser ? Brushes.LightBlue : Brushes.LightGray,
                        CornerRadius = new CornerRadius(8),
                        Padding = new Thickness(10),
                        Margin = new Thickness(10),
                        MaxWidth = 600,
                        HorizontalAlignment = isUser ? HorizontalAlignment.Right : HorizontalAlignment.Left,
                        Child = richTextBox,
                    };

                    ChatStackPanel.Children.Add(border);

                    // Rola para o final do ScrollViewer que contém o ChatStackPanel
                    // (Supondo que o ScrollViewer é o pai direto do ChatStackPanel)
                    if (VisualTreeHelper.GetParent(ChatStackPanel) is ScrollViewer scrollViewer)
                    {
                        scrollViewer.ScrollToEnd();
                    }
                }*/

        private async Task AnimateTyping(string markdown, bool isUser)
        {
            string decoded = WebUtility.HtmlDecode(markdown);
            string html = Markdown.ToHtml(decoded);
            string plainText = HtmlToPlainTextConverter.StripHtmlTags(html);

            var paragraph = new Paragraph();
            var doc = new FlowDocument(paragraph);
            var rtb = new RichTextBox
            {
                Document = doc,
                IsReadOnly = true,
                Background = Brushes.Transparent,
                BorderThickness = new Thickness(0),
                Padding = new Thickness(0),
                Width = 600
            };

            var border = new Border
            {
                Background = isUser ? Brushes.LightBlue : Brushes.LightGray,
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(10),
                Margin = new Thickness(10),
                MaxWidth = 600,
                HorizontalAlignment = isUser ? HorizontalAlignment.Right : HorizontalAlignment.Left,
                Child = rtb,
            };

            ChatStackPanel.Children.Add(border);

            // Simulate typing
            foreach (char c in plainText)
            {
                paragraph.Inlines.Add(new Run(c.ToString()));
                await Task.Delay(15); // adjust speed if needed
            }

            ScrollToBottom();
        }

        private void ScrollToBottom()
        {
            if (VisualTreeHelper.GetParent(ChatStackPanel) is ScrollViewer scrollViewer)
            {
                scrollViewer.ScrollToEnd();
            }
        }
    }
}
