from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

def _run_scheduler_safe(scheduler: BlockingScheduler):
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")

def start_cron_job(job_func, cron_schedule, id='bot-stimulator-sync', replace_existing=True):
    """
    Start a blocking scheduler to run the provided job function.
    """
    scheduler = BlockingScheduler()
    trigger = CronTrigger.from_crontab(cron_schedule)
    
    # Add the job to run based on the schedule, and set it to run immediately
    scheduler.add_job(
        job_func, 
        trigger, 
        id=id, 
        replace_existing=replace_existing,
        next_run_time=datetime.now()
    )
    
    print("Scheduler started. Task will run immediately, and then based on the provided trigger.")
    print("Press Ctrl+C to exit.")
    _run_scheduler_safe(scheduler)
