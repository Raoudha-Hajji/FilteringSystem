from django.urls import path
from .views import get_filtered_table, get_rejected_table

urlpatterns = [
    path('api/filtered_data/', get_filtered_table, name='filtered_data'),
    path('api/rejected_data/', get_rejected_table, name='rejected_data'),
]
