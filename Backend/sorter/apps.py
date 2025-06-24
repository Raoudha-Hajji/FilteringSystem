# apps.py
from django.apps import AppConfig
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import time
from django.conf import settings
from datetime import datetime, timedelta
import os
from sorter.filter import train_with_sbert
from sorter.augment import augment_sqlite_with_translations

class SorterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sorter'

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true': 
            train_with_sbert("training_data")
            #augment_sqlite_with_translations()
        scheduler = BackgroundScheduler()

        scheduler.add_job(train_with_sbert,"interval",weeks=1,args=["training_data"],id="weekly_training_job",
            replace_existing=True
        )
        
        scheduler.start()
