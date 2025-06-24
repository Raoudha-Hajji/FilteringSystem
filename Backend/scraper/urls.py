# scraper/urls.py
from django.urls import path
from .views import run_web_scraper_view, run_email_scraper_view

urlpatterns = [
    path('tuneps/', run_web_scraper_view, name='run_web_scraper_manual'),
    path('tunisurf/', run_email_scraper_view, name='run_email_scraper_manual'),
]
