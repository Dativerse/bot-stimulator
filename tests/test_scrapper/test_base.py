import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.scrapper.base import Fetcher

class DummyFetcher(Fetcher):
    def get_articles(self):
        yield {"id": 1, "title": "Test Article"}

class TestBaseFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = DummyFetcher()

    def test_slugify(self):
        self.assertEqual(self.fetcher._slugify("Hello World!"), "hello-world")
        self.assertEqual(self.fetcher._slugify("Test_with_underscores"), "test-with-underscores")
        self.assertEqual(self.fetcher._slugify("Multiple---Dashes"), "multiple-dashes")
        self.assertEqual(self.fetcher._slugify("Special #@ Characters!"), "special-characters")
        self.assertEqual(self.fetcher._slugify("A" * 100), "a" * 80)

    def test_make_filename(self):
        article = {"id": 123, "title": "My Article Title"}
        self.assertEqual(self.fetcher._make_filename(article), "123-my-article-title.md")

        article_no_title = {"id": 456, "name": "Alternate Name"}
        self.assertEqual(self.fetcher._make_filename(article_no_title), "456-alternate-name.md")
        
        article_no_name_title = {"id": 789}
        self.assertEqual(self.fetcher._make_filename(article_no_name_title), "789-789.md")

    @patch('src.scrapper.base.html_to_markdown')
    def test_article_to_markdown(self, mock_html_to_markdown):
        mock_html_to_markdown.return_value = "Mocked Markdown Content"
        article = {
            "id": 101,
            "title": "Sample Article",
            "body": "<p>Sample body</p>",
            "html_url": "http://example.com/101",
            "section_id": "section1",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "edited_at": "2023-01-02T00:00:00Z",
            "author_id": 999,
            "draft": False,
            "promoted": True,
            "label_names": ["label1", "label2"]
        }
        
        md_content = self.fetcher._article_to_markdown(article)
        
        self.assertIn('title: "Sample Article"', md_content)
        self.assertIn('id: 101', md_content)
        self.assertIn('url: http://example.com/101', md_content)
        self.assertIn('labels: ["label1", "label2"]', md_content)
        self.assertIn('Mocked Markdown Content', md_content)
        
        mock_html_to_markdown.assert_called_once_with("<p>Sample body</p>")

    def test_article_to_markdown_no_body(self):
        article = {"id": 102}
        md_content = self.fetcher._article_to_markdown(article)
        self.assertIn('*No content.*', md_content)

    @patch('src.scrapper.base.config')
    @patch('src.scrapper.base.Path')
    def test_fetch_or_update(self, mock_path, mock_config):
        mock_dir = MagicMock()
        mock_config.ARTICLES_DIR = mock_dir
        
        # Test article yields 2 articles
        class TwoArticleFetcher(Fetcher):
            def get_articles(self):
                yield {"id": 1, "title": "Article 1", "updated_at": "2023-01-01"}
                yield {"id": 2, "title": "Article 2", "updated_at": "2023-01-01"}
                
        fetcher = TwoArticleFetcher()
        
        # Mock file operations
        mock_file1 = MagicMock()
        mock_file1.exists.return_value = False
        
        mock_file2 = MagicMock()
        mock_file2.exists.return_value = True
        mock_file2.read_text.return_value = "updated_at: 2023-01-01"
        
        # Configure the dir to return the mocked files
        def side_effect(filename):
            if "1-article-1" in filename:
                return mock_file1
            elif "2-article-2" in filename:
                return mock_file2
            return MagicMock()
        mock_dir.__truediv__.side_effect = side_effect
        
        saved_files = fetcher.fetch_or_update()
        
        # Article 1 should be added (exists=False)
        self.assertEqual(len(saved_files), 1)
        self.assertEqual(saved_files[0], mock_file1)
        mock_file1.write_text.assert_called_once()
        
        # Article 2 should be skipped (updated_at matches)
        mock_file2.write_text.assert_not_called()
