import unittest
from src.uploader.base import Uploader

class TestUploaderBase(unittest.TestCase):
    def test_can_instantiate_concrete_class(self):
        class ConcreteUploader(Uploader):
            def upload(self, file_paths=None):
                pass
                
        uploader = ConcreteUploader()
        self.assertIsInstance(uploader, Uploader)

    def test_abstract_upload_raises_error(self):
        with self.assertRaises(TypeError):
            Uploader()
