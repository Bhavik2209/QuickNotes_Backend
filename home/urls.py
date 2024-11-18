# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('fetch-transcript/', views.fetch_youtube_transcript, name='fetch_transcript'),
]