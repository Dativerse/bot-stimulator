import unittest
from unittest.mock import patch, MagicMock, ANY
from src.scheduler.runner import start_cron_job

class TestRunner(unittest.TestCase):
    @patch('src.scheduler.runner.BlockingScheduler')
    @patch('src.scheduler.runner.CronTrigger.from_crontab')
    def test_start_cron_job_normal_execution(self, mock_cron_trigger, mock_scheduler_class):
        mock_scheduler_instance = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler_instance
        
        mock_trigger_instance = MagicMock()
        mock_cron_trigger.return_value = mock_trigger_instance
        
        dummy_func = MagicMock()
        
        start_cron_job(dummy_func, "0 0 * * *", id="test-id", replace_existing=False)
        
        mock_scheduler_class.assert_called_once()
        mock_cron_trigger.assert_called_once_with("0 0 * * *")
        
        mock_scheduler_instance.add_job.assert_called_once_with(
            dummy_func, mock_trigger_instance, id="test-id", replace_existing=False, next_run_time=ANY
        )
        mock_scheduler_instance.start.assert_called_once()
        
    @patch('src.scheduler.runner.BlockingScheduler')
    @patch('src.scheduler.runner.CronTrigger.from_crontab')
    def test_start_cron_job_keyboard_interrupt(self, mock_cron_trigger, mock_scheduler_class):
        mock_scheduler_instance = MagicMock()
        mock_scheduler_instance.start.side_effect = KeyboardInterrupt()
        mock_scheduler_class.return_value = mock_scheduler_instance
        
        dummy_func = MagicMock()
        
        # This shouldn't raise KeyboardInterrupt since it's caught
        start_cron_job(dummy_func, "0 0 * * *")
        
        mock_scheduler_instance.start.assert_called_once()
