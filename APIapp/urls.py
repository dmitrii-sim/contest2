from django.urls import path
from .views import CitizenInfoView, CitizenInfoImportView, CitizenPatch, \
    CitizensAgeView, CitizensPresentsView


urlpatterns = [
    path('imports', CitizenInfoImportView.as_view(), name="post_citizens"),
    path('imports/<int:import_id>/citizens', CitizenInfoView.as_view(),
         name="get_all_import_citizens"),
    path('imports/<int:import_id>/citizens/<int:citizen_id>',
         CitizenPatch.as_view(), name="patch_citizen"),
    path('imports/<int:import_id>/citizens/birthdays',
         CitizensPresentsView.as_view(), name="get_presents"),
    path('imports/<int:import_id>/towns/stat/percentile/age',
         CitizensAgeView.as_view(), name="get_percentile_age"),
]
