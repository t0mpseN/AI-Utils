using HtmlAgilityPack;
using System.Windows;
using System.Windows.Documents;
using System.Windows.Media;

namespace QuickLearnerUI
{
    public static class HtmlToFlowDocumentConverter
    {
        public static FlowDocument Convert(string html)
        {
            var doc = new FlowDocument();
            var htmlDoc = new HtmlDocument();
            htmlDoc.LoadHtml(html);

            foreach (var node in htmlDoc.DocumentNode.ChildNodes)
            {
                if (string.IsNullOrWhiteSpace(node.InnerText))
                    continue;

                var block = ParseNodeToBlock(node);
                if (block != null)
                    doc.Blocks.Add(block);
            }

            return doc;
        }

        private static Block ParseNodeToBlock(HtmlNode node)
        {
            switch (node.Name)
            {
                case "#text":
                    return new Paragraph(new Run(HtmlEntity.DeEntitize(node.InnerText.Trim())));

                case "p":
                    return new Paragraph(ParseInlineChildren(node));

                case "ul":
                    return ParseList(node, false);

                case "ol":
                    return ParseList(node, true);

                case "pre":
                    var prePara = new Paragraph(new Run(HtmlEntity.DeEntitize(node.InnerText)));
                    prePara.Background = Brushes.LightGray;
                    prePara.FontFamily = new FontFamily("Consolas");
                    prePara.Margin = new Thickness(5);
                    return prePara;

                case "h1":
                case "h2":
                case "h3":
                case "h4":
                case "h5":
                case "h6":
                    var header = new Paragraph(ParseInlineChildren(node));
                    header.FontWeight = FontWeights.Bold;
                    header.FontSize = 20;
                    return header;

                default:
                    return new Paragraph(ParseInlineChildren(node));
            }
        }

        private static List ParseList(HtmlNode node, bool ordered)
        {
            var list = new List
            {
                MarkerStyle = ordered ? TextMarkerStyle.Decimal : TextMarkerStyle.Disc,
                Margin = new Thickness(20, 0, 0, 0)
            };

            foreach (var li in node.SelectNodes("li") ?? new HtmlNodeCollection(null))
            {
                var listItem = new ListItem(new Paragraph(ParseInlineChildren(li)));
                list.ListItems.Add(listItem);
            }

            return list;
        }

        private static Inline ParseInlineChildren(HtmlNode node)
        {
            var span = new Span();

            for (int i = 0; i < node.ChildNodes.Count; i++)
            {
                var child = node.ChildNodes[i];
                Inline inline = null;

                string trimmed = HtmlEntity.DeEntitize(child.InnerText).Trim();

                if (child.Name == "#text")
                {
                    inline = new Run(trimmed);
                }
                else
                {
                    switch (child.Name)
                    {
                        case "strong":
                        case "b":
                            inline = new Bold(ParseInlineChildren(child));
                            break;
                        case "em":
                        case "i":
                            inline = new Italic(ParseInlineChildren(child));
                            break;
                        case "u":
                            inline = new Underline(ParseInlineChildren(child));
                            break;
                        case "a":
                            var hyperlink = new Hyperlink(ParseInlineChildren(child));
                            var href = child.GetAttributeValue("href", null);
                            if (!string.IsNullOrEmpty(href))
                                hyperlink.NavigateUri = new Uri(href);
                            hyperlink.RequestNavigate += (s, e) =>
                            {
                                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(e.Uri.AbsoluteUri) { UseShellExecute = true });
                                e.Handled = true;
                            };
                            inline = hyperlink;
                            break;
                        case "code":
                            inline = new Run(trimmed)
                            {
                                FontFamily = new FontFamily("Consolas"),
                                Background = Brushes.LightGray
                            };
                            break;
                        default:
                            inline = ParseInlineChildren(child);
                            break;
                    }
                }

                if (inline != null)
                {
                    span.Inlines.Add(inline);

                    // 🔧 Check if the next sibling is text and doesn't start with space, add a space manually
                    if (i < node.ChildNodes.Count - 1)
                    {
                        var next = node.ChildNodes[i + 1];
                        if (next.Name == "#text" && !next.InnerText.StartsWith(" "))
                        {
                            span.Inlines.Add(new Run(" "));
                        }
                    }
                }
            }

            return span;
        }
    }
}
