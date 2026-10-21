"""CMS routes for Auto Prerequisite Gating."""

from django.urls import path

from .views import configure_gating, setup_gating_view

app_name = "auto_prereq_gating"

urlpatterns = [
    path("setup/<str:course_id>/", setup_gating_view, name="setup_gating"),
    path("configure/", configure_gating, name="configure"),
]
