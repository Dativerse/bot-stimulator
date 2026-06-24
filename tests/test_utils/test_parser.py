import unittest
import bs4
from src.utils.parser import html_to_markdown

class TestParser(unittest.TestCase):
    def test_html_to_markdown_basic(self):
        html = "<h1>Hello</h1><p>World</p>"
        md = html_to_markdown(html)
        self.assertEqual(md, "# Hello\n\nWorld\n")
        
    def test_html_to_markdown_edge_cases(self):
        # class as a string instead of a list
        soup = bs4.BeautifulSoup('<html><body><div>Should be stripped</div></body></html>', "html.parser")
        div = soup.find('div')
        div['class'] = "nav" # Mocking class as a string
        md = html_to_markdown(str(soup))
        self.assertEqual(md, "\n")
        
        # id as a list instead of a string (beautifulsoup sometimes does this if multiple ids are provided, though rare)
        # Actually BeautifulSoup just parses id as a string usually, but we can construct an element.
        soup2 = bs4.BeautifulSoup('<html><body><div>Should be stripped</div></body></html>', "html.parser")
        div2 = soup2.find('div')
        div2['id'] = ['nav', 'bar'] # Mocking id as a list
        md2 = html_to_markdown(str(soup2))
        self.assertEqual(md2, "\n")
        
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
