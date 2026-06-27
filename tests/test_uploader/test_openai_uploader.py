import unittest
from unittest.mock import patch, MagicMock, mock_open
from src.uploader.openai_uploader import OpenAIUploader
from src.enums import SyncStatus
import json

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
        mock_config.ARTICLES_DIR.__truediv__.return_value = mock_filepath
        
        stage_data = {"new.md": {"status": SyncStatus.NEW}}
        
        mock_file_resp = MagicMock()
        mock_file_resp.id = "file_new"
        mock_client.files.create.return_value = mock_file_resp

        mock_file_batch = MagicMock()
        mock_file_batch.status = "completed"
        mock_client.vector_stores.files.create_and_poll.return_value = mock_file_batch
        
        uploader = OpenAIUploader()
        
        m_open = mock_open(read_data=json.dumps(stage_data))
        with patch('builtins.open', m_open):
            uploader.upload("stage.json")
            
        mock_client.vector_stores.create.assert_called_once_with(name="new_store")
        mock_client.files.create.assert_called_once()
        mock_client.vector_stores.files.create_and_poll.assert_called_once_with(
            vector_store_id="vs_123",
            file_id="file_new",
            chunking_strategy={
                "type": "static",
                "static": {
                    "max_chunk_size_tokens": 1000,
                    "chunk_overlap_tokens": 200
                }
            }
        )

    @patch('src.uploader.base.config')
    @patch('src.uploader.base.Path')
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_upload_modifies_and_deletes(self, mock_openai, mock_config, mock_path_cls, mock_base_config):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_config.VECTOR_STORE_NAME = "test_store"
        
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
        mock_config.ARTICLES_DIR.__truediv__.return_value = mock_filepath
        
        stage_data = {
            "mod.md": {"status": SyncStatus.MODIFIED, "file_id": "file_mod"}, 
            "del.md": {"status": SyncStatus.DELETED, "file_id": "file_del"}
        }
        
        mock_file_resp = MagicMock()
        mock_file_resp.id = "file_mod_new"
        mock_client.files.create.return_value = mock_file_resp

        mock_file_batch = MagicMock()
        mock_file_batch.status = "completed"
        mock_client.vector_stores.files.create_and_poll.return_value = mock_file_batch
        
        uploader = OpenAIUploader()
        
        m_open = mock_open(read_data=json.dumps(stage_data))
        with patch('builtins.open', m_open):
            uploader.upload("stage.json")
            
        mock_client.files.delete.assert_any_call("file_mod")
        mock_client.files.delete.assert_any_call("file_del")
        mock_client.vector_stores.files.create_and_poll.assert_called_once_with(
            vector_store_id="vs_123",
            file_id="file_mod_new",
            chunking_strategy={
                "type": "static",
                "static": {
                    "max_chunk_size_tokens": 1000,
                    "chunk_overlap_tokens": 200
                }
            }
        )

    @patch('src.uploader.base.config')
    @patch('src.uploader.base.Path')
    @patch('src.uploader.openai_uploader.config')
    @patch('src.uploader.openai_uploader.OpenAI')
    def test_execute_new_with_rollback(self, mock_openai, mock_config, mock_path_cls, mock_base_config):
        mock_config.OPENAI_API_KEY = "test_key"
        mock_config.VECTOR_STORE_NAME = "test_store"
        
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
        mock_config.ARTICLES_DIR.__truediv__.return_value = mock_filepath
        
        stage_data = {"new.md": {"status": SyncStatus.NEW}}
        
        mock_file_resp = MagicMock()
        mock_file_resp.id = "file_new"
        mock_client.files.create.return_value = mock_file_resp

        mock_client.vector_stores.files.create_and_poll.side_effect = Exception("Failed to attach to vector store")
        
        uploader = OpenAIUploader()
        
        m_open = mock_open(read_data=json.dumps(stage_data))
        with patch('builtins.open', m_open):
            uploader.upload("stage.json")
            
        self.assertEqual(mock_client.vector_stores.files.create_and_poll.call_count, 1)
        
        # Because vector store attach failed, rollback cleanup should have happened
        self.assertEqual(mock_client.files.delete.call_count, 1)
        mock_client.files.delete.assert_called_with("file_new")

if __name__ == "__main__":
    unittest.main()
