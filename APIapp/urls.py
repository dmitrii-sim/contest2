from django.contrib import admin
from django.urls import path, include
from .views import CitizenCreateView, CitizenListView


urlpatterns = [
    path('imports', CitizenCreateView.as_view()),
    path('imports/<int:import_id>/citizens', CitizenListView.as_view()),

]
