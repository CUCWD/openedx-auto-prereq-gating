"""Minimal Open edX API decorator stubs for standalone plugin tests."""

import json
import sys
from functools import wraps
from types import ModuleType

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def _unauthenticated(request):  # pylint: disable=useless-return
    """Return no authentication result by default."""
    del request
    return None


JWT_AUTHENTICATE = _unauthenticated


def install():
    """Install the host modules needed while testing outside edx-platform."""
    rest_framework = ModuleType("rest_framework")
    rest_framework.__path__ = []
    rest_framework_decorators = ModuleType("rest_framework.decorators")
    rest_framework_decorators.api_view = _api_view

    openedx = ModuleType("openedx")
    openedx.__path__ = []
    openedx_core = ModuleType("openedx.core")
    openedx_core.__path__ = []
    openedx_lib = ModuleType("openedx.core.lib")
    openedx_lib.__path__ = []
    openedx_api = ModuleType("openedx.core.lib.api")
    openedx_api.__path__ = []
    view_utils = ModuleType("openedx.core.lib.api.view_utils")
    view_utils.view_auth_classes = _view_auth_classes

    modules = (
        ("rest_framework", rest_framework),
        ("rest_framework.decorators", rest_framework_decorators),
        ("openedx", openedx),
        ("openedx.core", openedx_core),
        ("openedx.core.lib", openedx_lib),
        ("openedx.core.lib.api", openedx_api),
        ("openedx.core.lib.api.view_utils", view_utils),
    )
    for name, module in modules:
        sys.modules[name] = module


def _view_auth_classes():
    """Stand in for Open edX's JWT and session authentication policy."""
    def decorator(view):
        @wraps(view)
        def authenticated_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                authenticated = JWT_AUTHENTICATE(request)  # pylint: disable=assignment-from-none
                if authenticated is not None:
                    request.user, request.auth = authenticated
            if not request.user.is_authenticated:
                return JsonResponse(
                    {"error": "Authentication credentials were not provided."},
                    status=401,
                )
            return view(request, *args, **kwargs)

        return authenticated_view

    return decorator


def _api_view(methods):
    """Parse request data before invoking a DRF-style API view."""
    def decorator(view):
        @require_http_methods(methods)
        @wraps(view)
        def parsed_view(request, *args, **kwargs):
            if request.content_type == "application/json":
                try:
                    request.data = json.loads(request.read() or b"{}")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return JsonResponse(
                        {"error": "Expected a JSON request body."},
                        status=400,
                    )
            else:
                request.data = request.POST
            return view(request, *args, **kwargs)

        return parsed_view

    return decorator
