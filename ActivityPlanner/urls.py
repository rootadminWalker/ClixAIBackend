from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('select_course/', views.select_course, name='select_course'),
    path('api_ttb_get_division/', views.api_ttb_get_division, name='api_ttb_get_division'),
    path('api_ttb_autocomplete_input/', views.api_ttb_autocomplete_input, name='api_ttb_autocomplete_input'),
    path('api_ttb_search_times/', views.api_ttb_search_times, name='api_ttb_search_times'),
    path('generate_study_schedule/', views.generate_study_schedule, name='generate_study_schedule'),
]
