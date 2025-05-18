using HtmlAgilityPack;

namespace QuickLearnerUI
{
    public static class HtmlToPlainTextConverter
    {
        public static string StripHtmlTags(string html)
        {
            var doc = new HtmlDocument();
            doc.LoadHtml(html);
            return HtmlEntity.DeEntitize(doc.DocumentNode?.InnerText ?? "");
        }
    }
}
