"""
URL configuration for filterproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import current_user,list_users, create_user, delete_user


urlpatterns = [
    path('admin/', admin.site.urls),
    path('scraper/', include('scraper.urls')), 
    path('sorter/', include('sorter.urls')),  
    path('', lambda request: HttpResponse("Welcome to the Filter Project Dashboard!")),  # Root path
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user/', current_user, name='current_user'),
    path('api/users/', list_users, name='list_users'),
    path('api/users/create/', create_user, name='create_user'),
    path('api/users/<int:user_id>/delete/', delete_user, name='delete_user'),
]
