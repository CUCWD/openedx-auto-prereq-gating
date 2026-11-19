"""CMS routes for Auto Prerequisite Gating."""

from django.urls import path

from .views import configure_gating, setup_gating_view, remove_gating_view

app_name = "auto_prereq_gating"

urlpatterns = [
    path("setup/<str:course_id>/", setup_gating_view, name="setup_gating"),
    path("remove/<str:course_id>/", remove_gating_view, name="remove_gating"),
    path("configure/", configure_gating, name="configure"),
]
