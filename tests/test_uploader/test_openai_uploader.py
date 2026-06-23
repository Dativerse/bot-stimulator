import unittest
from unittest.mock import patch, MagicMock, mock_open
from src.uploader.openai_uploader import OpenAIUploader
import sys

class TestOpenAIUploader(unittest.TestCase):
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_init_missing_api_key(self, mock_openai, mock_config):
        mock_config.OPENAI_API_KEY = None
        
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print') as mock_print:
                OpenAIUploader()
                mock_exit.assert_called_once_with(1)
                mock_print.assert_any_call("Failed to initialize OpenAI client:")

    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_init_success(self, mock_openai, mock_config):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_config.VECTOR_STORE_NAME = "test_store"
        
        uploader = OpenAIUploader()
        
        mock_openai.assert_called_once_with(api_key="test_key")
        self.assertEqual(uploader.vector_store_name, "test_store")
        self.assertEqual(uploader.client, mock_openai.return_value)

    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_missing_articles_dir(self, mock_openai, mock_config):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_config.ARTICLES_DIR.exists.return_value = False
        
        uploader = OpenAIUploader()
        
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print') as mock_print:
                uploader.upload()
                mock_exit.assert_called_once_with(1)

    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_no_markdown_files(self, mock_openai, mock_config):
        mock_config.OPENAI_API_KEY = "test_key"
        
        # Test case 1: file_paths is None, but ARTICLES_DIR is empty
        mock_config.ARTICLES_DIR.exists.return_value = True
        mock_config.ARTICLES_DIR.iterdir.return_value = []
        
        uploader = OpenAIUploader()
        
        with patch('builtins.print') as mock_print:
            uploader.upload()
            mock_print.assert_any_call("No markdown files found to upload.")

        # Test case 2: file_paths is empty list
        with patch('builtins.print') as mock_print:
            uploader.upload([])
            mock_print.assert_any_call("No markdown files found to upload.")

    @patch('src.uploader.openai_uploader.open', new_callable=mock_open)
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_existing_vector_store(self, mock_openai, mock_config, mock_file_open):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_config.VECTOR_STORE_NAME = "test_store"
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_store = MagicMock()
        mock_store.name = "test_store"
        mock_store.id = "store_id_123"
        mock_client.vector_stores.list.return_value = [mock_store]
        
        mock_file_batch = MagicMock()
        mock_file_batch.status = "completed"
        mock_file_batch.file_counts = {"completed": 1}
        mock_client.vector_stores.file_batches.upload_and_poll.return_value = mock_file_batch
        
        uploader = OpenAIUploader()
        
        # Mock file paths
        mock_path1 = MagicMock()
        mock_path1.suffix = ".md"
        mock_path2 = MagicMock()
        mock_path2.suffix = ".txt"
        
        mock_config.ARTICLES_DIR.exists.return_value = True
        mock_config.ARTICLES_DIR.iterdir.return_value = [mock_path1, mock_path2]
        
        uploader.upload()
        
        # Should not create new vector store
        mock_client.vector_stores.create.assert_not_called()
        
        # upload_and_poll should be called
        mock_client.vector_stores.file_batches.upload_and_poll.assert_called_once()
        args, kwargs = mock_client.vector_stores.file_batches.upload_and_poll.call_args
        self.assertEqual(kwargs['vector_store_id'], "store_id_123")
        
        # We also need to check that open was called for each file
        mock_file_open.assert_called_once_with(mock_path1, "rb")

    @patch('src.uploader.openai_uploader.open', new_callable=mock_open)
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_create_vector_store(self, mock_openai, mock_config, mock_file_open):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_config.VECTOR_STORE_NAME = "new_test_store"
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # No existing stores match
        mock_store = MagicMock()
        mock_store.name = "other_store"
        mock_client.vector_stores.list.return_value = [mock_store]
        
        # Mock create store
        mock_new_store = MagicMock()
        mock_new_store.id = "new_store_id_456"
        mock_client.vector_stores.create.return_value = mock_new_store
        
        mock_file_batch = MagicMock()
        mock_client.vector_stores.file_batches.upload_and_poll.return_value = mock_file_batch
        
        uploader = OpenAIUploader()
        
        # Provide explicit file_paths
        mock_path = "explicit_path.md"
        
        uploader.upload([mock_path])
        
        # Should create new vector store
        mock_client.vector_stores.create.assert_called_once_with(name="new_test_store")
        
        # upload_and_poll should be called
        mock_client.vector_stores.file_batches.upload_and_poll.assert_called_once()
        args, kwargs = mock_client.vector_stores.file_batches.upload_and_poll.call_args
        self.assertEqual(kwargs['vector_store_id'], "new_store_id_456")
