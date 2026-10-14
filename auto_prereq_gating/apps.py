"""Django application configuration for Auto Prerequisite Gating."""

from django.apps import AppConfig


class AutoPrereqGatingConfig(AppConfig):
    name = "auto_prereq_gating"
    verbose_name = "Auto Prerequisite Gating"

    plugin_app = {
        "url_config": {
            "cms.djangoapp": {
                "namespace": "auto_prereq_gating",
                "regex": r"^auto_prereq_gating/",
                "relative_path": "urls",
            },
        },
    }
