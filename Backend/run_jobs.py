import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "filterproject.settings")
django.setup()

from apscheduler.schedulers.blocking import BlockingScheduler
from scraper.web_scraper import run_web_scraper
from scraper.email_scraper import run_email_scraper
from sorter.filter import train_with_sbert
from datetime import datetime, timedelta
import logging


logger = logging.getLogger("myjobs")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("/home/filtersystem/FilteringSystem/Backend/logs/myjobs.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
if file_handler not in logger.handlers:
    logger.addHandler(file_handler)

scheduler = BlockingScheduler()

# Staggered initial runs
scheduler.add_job(train_with_sbert, 'date', run_date=datetime.now() + timedelta(minutes=1), args=["training_data"], id="initial_training_job")
scheduler.add_job(run_email_scraper, 'date', run_date=datetime.now() + timedelta(minutes=2), id="initial_email_scraper_job")
scheduler.add_job(run_web_scraper, 'date', run_date=datetime.now() + timedelta(minutes=4), id="initial_web_scraper_job")

# Regular schedules
scheduler.add_job(train_with_sbert, "interval", weeks=1, args=["training_data"], id="weekly_training_job", replace_existing=True)
scheduler.add_job(run_email_scraper, 'cron', hour=7, minute=0, id="email_scraper_job", replace_existing=True)
scheduler.add_job(run_web_scraper, 'interval', minutes=30, id="web_scraper_job", replace_existing=True)

if __name__ == "__main__":
    logger.info("Starting standalone scheduler for background jobs.")
    scheduler.start() 
