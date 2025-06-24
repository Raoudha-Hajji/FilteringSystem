from django.shortcuts import render
from django.http import JsonResponse
from .web_scraper import run_web_scraper
from .email_scraper import run_email_scraper

def run_web_scraper_view(request):
    run_web_scraper()
    return JsonResponse({'status': 'Web Scraper executed successfully'})

def run_email_scraper_view(request):
    run_email_scraper()
    return JsonResponse({'status': 'Email Scraper executed successfully'})

