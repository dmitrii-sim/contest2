from django.contrib import admin
from django.urls import path, include
from .views import CitizenInfoView, CitizenInfoImportView


urlpatterns = [
    path('imports', CitizenInfoImportView.as_view()),
    path('imports/<int:import_id>/citizens', CitizenInfoView.as_view()),

]
