from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.web_scraper import run_web_scraper  # Import the actual job (not the view)
from scraper.email_scraper import run_email_scraper  # Import the actual job (not the view)
import logging
import os


class ScraperConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scraper'

    def ready(self):
        # Avoid double-scheduler on autoreload
            if os.environ.get('RUN_MAIN') == 'true': 
                run_web_scraper()
                run_email_scraper()
            
            scheduler = BackgroundScheduler()
            scheduler.add_job(run_web_scraper, 'interval', minutes=30, id='web_scraper_job', replace_existing=True)
            scheduler.add_job(run_email_scraper, 'cron',hour=7, minute=0, id='email_scraper_job', replace_existing=True)
            scheduler.start()

            logging.getLogger().info("APScheduler started with email and web jobs.") 
                # This code will run once the app is ready

                   # Only run the scheduler if the server is running
"""         if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler import start
            start() """