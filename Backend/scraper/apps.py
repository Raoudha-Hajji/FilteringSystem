from django.apps import AppConfig


class ScraperConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scraper'

    def ready(self):
        # Scheduler/job logic removed. All background jobs are now managed by run_jobs.py
        pass
