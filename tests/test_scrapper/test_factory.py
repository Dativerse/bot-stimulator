import unittest
from src.scrapper.base import Fetcher
from src.scrapper.factory import create_fetcher, register_fetcher, _fetcher_registry

class DummyFetcher(Fetcher):
    def get_articles(self):
        yield {}

class TestFactory(unittest.TestCase):
    def setUp(self):
        # Save original registry
        self.original_registry = _fetcher_registry.copy()
        _fetcher_registry.clear()

    def tearDown(self):
        # Restore original registry
        _fetcher_registry.clear()
        _fetcher_registry.update(self.original_registry)

    def test_register_fetcher(self):
        @register_fetcher("dummy", "test")
        class TestDummyFetcher(Fetcher):
            def get_articles(self):
                yield {}
                
        self.assertIn("dummy", _fetcher_registry)
        self.assertIn("test", _fetcher_registry)
        self.assertEqual(_fetcher_registry["dummy"], TestDummyFetcher)
        self.assertEqual(_fetcher_registry["test"], TestDummyFetcher)

    def test_create_fetcher_success(self):
        @register_fetcher("dummy")
        class TestDummyFetcher(Fetcher):
            def get_articles(self):
                yield {}
                
        fetcher = create_fetcher("dummy")
        self.assertIsInstance(fetcher, TestDummyFetcher)
        
        fetcher = create_fetcher("DuMmY")
        self.assertIsInstance(fetcher, TestDummyFetcher)

    def test_create_fetcher_unsupported(self):
        with self.assertRaises(ValueError) as context:
            create_fetcher("unsupported")
        self.assertIn("Unsupported fetcher provider: unsupported", str(context.exception))
