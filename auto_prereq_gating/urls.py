"""CMS routes for Auto Prerequisite Gating."""

from django.urls import path

from .views import configure_gating

app_name = "auto_prereq_gating"

urlpatterns = [
    path("configure/", configure_gating, name="configure"),
]
