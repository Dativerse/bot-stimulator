import unittest
from src.uploader.base import Uploader
from src.uploader.factory import create_uploader, register_uploader, _uploader_registry

class DummyUploader(Uploader):
    def upload(self, file_paths=None):
        pass

class TestFactory(unittest.TestCase):
    def setUp(self):
        # Save original registry
        self.original_registry = _uploader_registry.copy()
        _uploader_registry.clear()

    def tearDown(self):
        # Restore original registry
        _uploader_registry.clear()
        _uploader_registry.update(self.original_registry)

    def test_register_uploader(self):
        @register_uploader("dummy", "test")
        class TestDummyUploader(Uploader):
            def upload(self, file_paths=None):
                pass
                
        self.assertIn("dummy", _uploader_registry)
        self.assertIn("test", _uploader_registry)
        self.assertEqual(_uploader_registry["dummy"], TestDummyUploader)
        self.assertEqual(_uploader_registry["test"], TestDummyUploader)

    def test_create_uploader_success(self):
        @register_uploader("dummy")
        class TestDummyUploader(Uploader):
            def upload(self, file_paths=None):
                pass
                
        uploader = create_uploader("dummy")
        self.assertIsInstance(uploader, TestDummyUploader)
        
        uploader = create_uploader("DuMmY")
        self.assertIsInstance(uploader, TestDummyUploader)

    def test_create_uploader_unsupported(self):
        with self.assertRaises(ValueError) as context:
            create_uploader("unsupported")
        self.assertIn("Unsupported uploader provider: unsupported", str(context.exception))
