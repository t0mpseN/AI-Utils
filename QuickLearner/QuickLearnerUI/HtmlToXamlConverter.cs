using System.IO;
using System.Text;
using System.Windows.Markup;
using System.Xml;

namespace QuickLearnerUI
{
    public static class HtmlToXamlConverter
    {
        public static string ConvertHtmlToXaml(string html, bool asFlowDocument)
        {
            string xaml = HtmlToXaml(html, asFlowDocument);
            return xaml;
        }

        private static string HtmlToXaml(string htmlString, bool asFlowDocument)
        {
            string xamlString = "";

            // Usa o WebBrowser embutido para interpretar o HTML
            var html = $"<html><body>{htmlString}</body></html>";
            var xamlBuilder = new StringBuilder();

            using (var stringReader = new StringReader(html))
            using (var xmlReader = XmlReader.Create(stringReader))
            using (var xamlWriter = new StringWriter(xamlBuilder))
            {
                try
                {
                    var xamlSettings = new XmlWriterSettings
                    {
                        Indent = true,
                        OmitXmlDeclaration = true
                    };

                    using (var writer = XmlWriter.Create(xamlWriter, xamlSettings))
                    {
                        writer.WriteStartElement(asFlowDocument ? "FlowDocument" : "Section", "http://schemas.microsoft.com/winfx/2006/xaml/presentation");
                        writer.WriteStartElement("Paragraph");
                        writer.WriteStartElement("Run");
                        writer.WriteString(StripHtmlTags(htmlString));
                        writer.WriteEndElement(); // Run
                        writer.WriteEndElement(); // Paragraph
                        writer.WriteEndElement(); // FlowDocument or Section
                    }

                    xamlString = xamlBuilder.ToString();
                }
                catch
                {
                    xamlString = "<Section xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\"><Paragraph>❌ Erro ao converter markdown</Paragraph></Section>";
                }
            }

            return xamlString;
        }

        private static string StripHtmlTags(string input)
        {
            return System.Text.RegularExpressions.Regex.Replace(input, "<.*?>", string.Empty);
        }
    }
}
