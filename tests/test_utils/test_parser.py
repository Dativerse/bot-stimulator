import unittest
from src.utils.parser import html_to_markdown

class TestParser(unittest.TestCase):
    def test_html_to_markdown_basic(self):
        html = "<h1>Hello</h1><p>World</p>"
        md = html_to_markdown(html)
        self.assertEqual(md, "# Hello\n\nWorld\n")
        
    def test_html_to_markdown_removes_ignore_tags(self):
        html = "<div><nav>Navigation</nav><p>Content</p><script>alert('test')</script></div>"
        md = html_to_markdown(html)
        self.assertEqual(md, "Content\n")
        
    def test_html_to_markdown_removes_ignore_keywords_in_class(self):
        html = "<div><div class='sidebar-menu'>Sidebar</div><p>Content</p></div>"
        md = html_to_markdown(html)
        self.assertEqual(md, "Content\n")
        
    def test_html_to_markdown_removes_ignore_keywords_in_id(self):
        html = "<div><div id='promo-banner'>Promo</div><p>Content</p></div>"
        md = html_to_markdown(html)
        self.assertEqual(md, "Content\n")

    def test_html_to_markdown_collapses_blank_lines(self):
        html = "<p>Line 1</p>\n\n\n\n\n<p>Line 2</p>"
        md = html_to_markdown(html)
        self.assertEqual(md, "Line 1\n\nLine 2\n")
