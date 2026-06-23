from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

def start_cron_job(job_func, cron_schedule, id='bot-stimulator-sync', replace_existing=True):
    """
    Start a blocking scheduler to run the provided job function.
    """
    scheduler = BlockingScheduler()
    trigger = CronTrigger.from_crontab(cron_schedule)
    
    # Add the job to run based on the schedule
    scheduler.add_job(job_func, trigger, id=id, replace_existing=replace_existing)
    
    print("Scheduler started. Task will run based on the provided trigger.")
    print("Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
