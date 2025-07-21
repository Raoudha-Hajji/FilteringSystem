# apps.py
from django.apps import AppConfig

class SorterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sorter'

    def ready(self):
        # Scheduler/job logic removed. All background jobs are now managed by run_jobs.py
        pass

