import unittest
from unittest.mock import patch, MagicMock, mock_open
from src.uploader.openai_uploader import OpenAIUploader
import sys
import json
from pathlib import Path

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

    @patch('src.uploader.base.Path')
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_missing_stage_file(self, mock_openai, mock_config, mock_path_cls):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_stage_path = MagicMock()
        mock_stage_path.exists.return_value = False
        mock_path_cls.return_value = mock_stage_path
        
        uploader = OpenAIUploader()
        with patch('builtins.print') as mock_print:
            uploader.upload("missing.json")
            mock_print.assert_any_call("Error: Stage file 'missing.json' not found.")

    @patch('src.uploader.base.config')
    @patch('src.uploader.base.Path')
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_empty_stage_file_no_action(self, mock_openai, mock_config, mock_path_cls, mock_base_config):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_stage_path = MagicMock()
        mock_stage_path.exists.return_value = True
        mock_path_cls.return_value = mock_stage_path
        
        uploader = OpenAIUploader()
        # Stage data with only 'Unchanged' which is not handled
        m_open = mock_open(read_data='{"file.md": "Unchanged"}')
        with patch('builtins.open', m_open):
            with patch('builtins.print') as mock_print:
                uploader.upload("stage.json")
                mock_print.assert_any_call("No actionable changes found for OpenAI in stage file.")

    @patch('src.uploader.base.config')
    @patch('src.uploader.base.Path')
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_creates_new_vector_store(self, mock_openai, mock_config, mock_path_cls, mock_base_config):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_config.VECTOR_STORE_NAME = "new_store"
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.vector_stores.list.return_value = []
        mock_new_store = MagicMock()
        mock_new_store.id = "vs_123"
        mock_client.vector_stores.create.return_value = mock_new_store
        
        mock_stage_path = MagicMock()
        mock_stage_path.exists.return_value = True
        mock_path_cls.return_value = mock_stage_path
        
        mock_filepath = MagicMock()
        mock_filepath.exists.return_value = True
        mock_filepath.name = "new.md"
        mock_base_config.ARTICLES_DIR.__truediv__.return_value = mock_filepath
        
        stage_data = {"new.md": "New"}
        
        mock_file_batch = MagicMock()
        mock_file_batch.status = "completed"
        mock_client.vector_stores.file_batches.upload_and_poll.return_value = mock_file_batch
        
        # mock files.list to return empty
        mock_client.files.list.return_value.data = []

        uploader = OpenAIUploader()
        
        m_open = mock_open(read_data=json.dumps(stage_data))
        with patch('builtins.open', m_open):
            uploader.upload("stage.json")
            
        mock_client.vector_stores.create.assert_called_once_with(name="new_store")
        mock_client.vector_stores.file_batches.upload_and_poll.assert_called_once()

    @patch('src.uploader.base.config')
    @patch('src.uploader.base.Path')
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_modifies_and_deletes(self, mock_openai, mock_config, mock_path_cls, mock_base_config):
        mock_config.OPENAI_API_KEY = "test_key"
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_store = MagicMock()
        mock_store.name = "test_store"
        mock_store.id = "vs_123"
        mock_client.vector_stores.list.return_value = [mock_store]
        
        mock_stage_path = MagicMock()
        mock_stage_path.exists.return_value = True
        mock_path_cls.return_value = mock_stage_path
        
        mock_filepath = MagicMock()
        mock_filepath.exists.return_value = True
        mock_filepath.name = "mod.md"
        mock_base_config.ARTICLES_DIR.__truediv__.return_value = mock_filepath
        
        stage_data = {"mod.md": "Modified", "del.md": "Deleted"}
        
        mock_file_batch = MagicMock()
        mock_file_batch.status = "completed"
        mock_client.vector_stores.file_batches.upload_and_poll.return_value = mock_file_batch
        
        mock_file_mod = MagicMock()
        mock_file_mod.filename = "mod.md"
        mock_file_mod.id = "file_mod"
        mock_file_del = MagicMock()
        mock_file_del.filename = "del.md"
        mock_file_del.id = "file_del"
        mock_client.files.list.return_value.data = [mock_file_mod, mock_file_del]

        uploader = OpenAIUploader()
        
        m_open = mock_open(read_data=json.dumps(stage_data))
        with patch('builtins.open', m_open):
            uploader.upload("stage.json")
            
        mock_client.files.delete.assert_any_call("file_mod")
        mock_client.files.delete.assert_any_call("file_del")
        mock_client.vector_stores.file_batches.upload_and_poll.assert_called_once()

    @patch('src.uploader.base.config')
    @patch('src.uploader.base.Path')
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    @patch('src.uploader.openai_uploader.time.sleep')
    def test_upload_retry_logic(self, mock_sleep, mock_openai, mock_config, mock_path_cls, mock_base_config):
        mock_config.OPENAI_API_KEY = "test_key"
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_store = MagicMock()
        mock_store.name = "test_store"
        mock_store.id = "vs_123"
        mock_client.vector_stores.list.return_value = [mock_store]
        
        mock_stage_path = MagicMock()
        mock_stage_path.exists.return_value = True
        mock_path_cls.return_value = mock_stage_path
        
        mock_filepath = MagicMock()
        mock_filepath.exists.return_value = True
        mock_filepath.name = "new.md"
        mock_base_config.ARTICLES_DIR.__truediv__.return_value = mock_filepath
        
        stage_data = {"new.md": "New"}
        
        mock_file_batch = MagicMock()
        mock_file_batch.status = "completed"
        mock_client.vector_stores.file_batches.upload_and_poll.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            mock_file_batch
        ]
        
        mock_client.files.list.return_value.data = []

        uploader = OpenAIUploader()
        
        m_open = mock_open(read_data=json.dumps(stage_data))
        with patch('builtins.open', m_open):
            uploader.upload("stage.json")
            
        self.assertEqual(mock_client.vector_stores.file_batches.upload_and_poll.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

if __name__ == "__main__":
    unittest.main()
