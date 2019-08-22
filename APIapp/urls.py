from django.urls import path
from .views import CitizenInfoView, CitizenInfoImportView, CitizenPatch, \
    CitizensAgeView, CitizensPresentsView


urlpatterns = [
    path('imports', CitizenInfoImportView.as_view()),
    path('imports/<int:import_id>/citizens', CitizenInfoView.as_view()),
    path('imports/<int:import_id>/citizens/<int:citizen_id>',
         CitizenPatch.as_view()),
    path('imports/<int:import_id>/citizens/birthdays',
         CitizensPresentsView.as_view()),
    path('imports/<int:import_id>/towns/stat/percentile/age',
         CitizensAgeView.as_view()),
]
