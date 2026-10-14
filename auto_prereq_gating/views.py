"""CMS views for automatic prerequisite gating."""

import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.auth import has_studio_write_access
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .gating import GatingConfigurationError, configure_sequential_prerequisites


@login_required
@require_POST
def configure_gating(request):
    """Configure 100% completion gating across a course's ordered subsections."""
    try:
        payload = json.loads(request.body)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Expected a JSON request body."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Expected a JSON object."}, status=400)

    course_key_value = payload.get("course_key")
    if not isinstance(course_key_value, str):
        return JsonResponse({"error": "course_key is required."}, status=400)

    try:
        course_key = CourseKey.from_string(course_key_value)
    except InvalidKeyError:
        return JsonResponse({"error": "course_key is invalid."}, status=400)

    if not has_studio_write_access(request.user, course_key):
        raise PermissionDenied

    store = modulestore()
    try:
        with store.bulk_operations(course_key):
            course = store.get_course(course_key, depth=None)
            total, configured = configure_sequential_prerequisites(course_key, course)
    except ItemNotFoundError:
        return JsonResponse({"error": "Course was not found."}, status=404)
    except GatingConfigurationError as error:
        return JsonResponse({"error": str(error)}, status=400)

    return JsonResponse({
        "course_key": str(course_key),
        "subsections_found": total,
        "gates_configured": configured,
        "min_completion": 100,
    })
