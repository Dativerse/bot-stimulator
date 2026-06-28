import unittest
from unittest.mock import patch, MagicMock

# Import main correctly to avoid running it
from main import main, run_sync

class TestMain(unittest.TestCase):
    @patch('main.create_uploader')
    @patch('main.create_fetcher')
    @patch('builtins.print')
    def test_run_sync(self, mock_print, mock_create_fetcher, mock_create_uploader):
        mock_fetcher = MagicMock()
        mock_stage_file = "stage.json"
        mock_fetcher.fetch_or_update.return_value = mock_stage_file
        mock_create_fetcher.return_value = mock_fetcher

        mock_uploader = MagicMock()
        mock_create_uploader.return_value = mock_uploader

        run_sync()

        mock_create_fetcher.assert_called_once_with("opti")
        mock_fetcher.fetch_or_update.assert_called_once()
        mock_create_uploader.assert_called_once_with("openai")
        mock_uploader.upload.assert_called_once_with(mock_stage_file)
        mock_print.assert_any_call("Starting sync task...")
        mock_print.assert_any_call("Sync task completed.")

    @patch('main.create_fetcher')
    @patch('sys.argv', ['main.py', 'fetch'])
    def test_main_fetch(self, mock_create_fetcher):
        mock_fetcher = MagicMock()
        mock_create_fetcher.return_value = mock_fetcher

        main()

        mock_create_fetcher.assert_called_once_with("opti")
        mock_fetcher.fetch_or_update.assert_called_once()

    @patch('main.run_sync')
    @patch('sys.argv', ['main.py', 'sync'])
    def test_main_sync(self, mock_run_sync):
        main()
        mock_run_sync.assert_called_once()

    @patch('main.start_cron_job')
    @patch('sys.argv', ['main.py', 'cron'])
    @patch('main.CRON_SCHEDULE', '0 0 * * *')
    def test_main_cron(self, mock_start_cron_job):
        main()
        mock_start_cron_job.assert_called_once()
        args, kwargs = mock_start_cron_job.call_args
        from main import run_sync
        self.assertEqual(args[0], run_sync)
        self.assertEqual(kwargs['cron_schedule'], '0 0 * * *')
        self.assertEqual(kwargs['id'], 'bot-stimulator-sync')
        self.assertEqual(kwargs['replace_existing'], True)

if __name__ == "__main__":
    unittest.main()
