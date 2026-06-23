import unittest
from unittest.mock import patch, MagicMock
from src.scrapper.optisign_fetcher import OptisignFetcher, fetch_json
import urllib.error

class TestOptisignFetcher(unittest.TestCase):

    @patch('src.scrapper.optisign_fetcher.urllib.request.urlopen')
    @patch('src.scrapper.optisign_fetcher.time.sleep')
    def test_fetch_json_success(self, mock_sleep, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"key": "value"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        result = fetch_json("http://example.com")
        self.assertEqual(result, {"key": "value"})
        mock_sleep.assert_not_called()

    @patch('src.scrapper.optisign_fetcher.urllib.request.urlopen')
    @patch('src.scrapper.optisign_fetcher.time.sleep')
    def test_fetch_json_retry_then_success(self, mock_sleep, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"success": true}'
        
        # First call raises URLError, second call succeeds
        mock_urlopen.side_effect = [
            urllib.error.URLError("Network error"),
            MagicMock(__enter__=MagicMock(return_value=mock_resp))
        ]
        
        result = fetch_json("http://example.com")
        self.assertEqual(result, {"success": True})
        mock_sleep.assert_called_once()

    @patch('src.scrapper.optisign_fetcher.urllib.request.urlopen')
    @patch('src.scrapper.optisign_fetcher.time.sleep')
    def test_fetch_json_rate_limit(self, mock_sleep, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"success": true}'
        
        # Mock HTTPError 429
        fp = MagicMock()
        http_error = urllib.error.HTTPError("http://example.com", 429, "Too Many Requests", {"Retry-After": "10"}, fp)
        
        mock_urlopen.side_effect = [
            http_error,
            MagicMock(__enter__=MagicMock(return_value=mock_resp))
        ]
        
        result = fetch_json("http://example.com")
        self.assertEqual(result, {"success": True})
        mock_sleep.assert_called_once_with(10)

    @patch('src.scrapper.optisign_fetcher.fetch_json')
    @patch('src.scrapper.optisign_fetcher.time.sleep')
    @patch('src.scrapper.optisign_fetcher.config')
    def test_get_articles(self, mock_config, mock_sleep, mock_fetch_json):
        mock_config.BASE_URL = "http://example.com/api"
        mock_config.PER_PAGE = 2
        mock_config.RATE_LIMIT_PAUSE = 0
        
        # Page 1 has 2 articles and next_page link
        # Page 2 has 1 article and no next_page link
        mock_fetch_json.side_effect = [
            {"articles": [{"id": 1}, {"id": 2}], "next_page": "http://example.com/api?page=2"},
            {"articles": [{"id": 3}], "next_page": None}
        ]
        
        fetcher = OptisignFetcher()
        articles = list(fetcher.get_articles())
        
        self.assertEqual(len(articles), 3)
        self.assertEqual(articles[0]["id"], 1)
        self.assertEqual(articles[1]["id"], 2)
        self.assertEqual(articles[2]["id"], 3)
        
        self.assertEqual(mock_fetch_json.call_count, 2)
