from django.urls import path
from .views import get_filtered_table, get_rejected_table, keyword_handler, refilter_handler
from django.urls import path


urlpatterns = [
    path('api/filtered_data/', get_filtered_table, name='filtered_data'),
    path('api/rejected_data/', get_rejected_table, name='rejected_data'),
    path('api/keywords/', keyword_handler, name='keywords'),  # Handles GET and POST
    path('api/keywords/<int:keyword_id>/', keyword_handler, name='keyword_detail'),  # Handles DELETE
    path('api/refilter/', refilter_handler, name='refilter'),
]
