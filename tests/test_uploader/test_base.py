import unittest
from src.uploader.base import Uploader

class TestUploaderBase(unittest.TestCase):
    def test_can_instantiate_concrete_class(self):
        class ConcreteUploader(Uploader):
            def execute_new(self, filename):
                return "new_id"
            def execute_update(self, filename, file_id):
                return "updated_id"
            def execute_delete(self, filename, file_id):
                return True
                
        uploader = ConcreteUploader()
        self.assertIsInstance(uploader, Uploader)

    def test_abstract_upload_raises_error(self):
        with self.assertRaises(TypeError):
            Uploader()
