from django.urls import path
from .views import CitizenInfoView, CitizenInfoImportView, CitizenPatch, \
    CitizensAge, CitizenGifts


urlpatterns = [
    path('imports', CitizenInfoImportView.as_view()),
    path('imports/<int:import_id>/citizens', CitizenInfoView.as_view()),
    path('imports/<int:import_id>/citizens/<int:citizen_id>',
         CitizenPatch.as_view()),
    path('imports/<int:import_id>/citizens/birthdays',
         CitizenGifts.as_view()),
    path('imports/<int:import_id>/towns/stat/percentile/age',
         CitizensAge.as_view()),
]
