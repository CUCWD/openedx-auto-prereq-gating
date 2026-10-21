"""Tests for the CMS REST views."""

# Fixtures are supplied as test parameters by pytest.
# pylint: disable=redefined-outer-name, unused-argument

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
from django.urls import reverse

from auto_prereq_gating import gating


pytestmark = pytest.mark.django_db

COURSE_ID = "course-v1:org+course+run"


@pytest.fixture
def platform_api(monkeypatch):
    """Stub the edx-platform APIs imported by the REST view."""
    common = ModuleType("common")
    common.__path__ = []
    djangoapps = ModuleType("common.djangoapps")
    djangoapps.__path__ = []
    student = ModuleType("common.djangoapps.student")
    student.__path__ = []
    auth = ModuleType("common.djangoapps.student.auth")
    has_course_author_access = Mock(return_value=True)
    auth.has_course_author_access = has_course_author_access

    invalid_key_error = type("InvalidKeyError", (Exception,), {})
    opaque_keys = ModuleType("opaque_keys")
    opaque_keys.__path__ = []
    opaque_keys.InvalidKeyError = invalid_key_error
    opaque_edx = ModuleType("opaque_keys.edx")
    opaque_edx.__path__ = []
    keys = ModuleType("opaque_keys.edx.keys")

    def parse_course_key(course_id):
        """Parse a course key or raise the platform's invalid-key error."""
        if not course_id.startswith("course-v1:"):
            raise invalid_key_error(course_id)
        return course_id

    keys.CourseKey = SimpleNamespace(from_string=parse_course_key)
    modules = (
        ("common", common),
        ("common.djangoapps", djangoapps),
        ("common.djangoapps.student", student),
        ("common.djangoapps.student.auth", auth),
        ("opaque_keys", opaque_keys),
        ("opaque_keys.edx", opaque_edx),
        ("opaque_keys.edx.keys", keys),
    )
    for name, module in modules:
        monkeypatch.setitem(sys.modules, name, module)
    return {"has_course_author_access": has_course_author_access}


@pytest.fixture
def authenticated_author(client, django_user_model):
    """Return a client logged in as a course author."""
    user = django_user_model.objects.create_user(username="author", password="secret")
    client.force_login(user)
    return client, user


def setup_url(course_id=COURSE_ID):
    """Return the URL for the setup endpoint."""
    return reverse("setup_gating", kwargs={"course_id": course_id})


def test_get_returns_405(platform_api, authenticated_author):
    """Reject GET requests to the POST-only endpoint."""
    client, _ = authenticated_author

    response = client.get(setup_url())

    assert response.status_code == 405


def test_unauthenticated_post_redirects_to_login(platform_api, client):
    """Redirect unauthenticated POST requests to the login page."""
    response = client.post(setup_url())

    assert response.status_code == 302
    assert response["Location"].startswith("/login")


def test_missing_author_access_returns_json_403(platform_api, authenticated_author):
    """Return a JSON forbidden response when the caller cannot author the course."""
    client, _ = authenticated_author
    platform_api["has_course_author_access"].return_value = False

    response = client.post(setup_url())

    assert response.status_code == 403
    assert response.json() == {"error": "You do not have author access to this course."}


def test_invalid_course_id_returns_json_400(platform_api, authenticated_author):
    """Return a JSON bad request for an invalid course key."""
    client, _ = authenticated_author

    response = client.post(setup_url("not-a-course-key"))

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid course ID."}


def test_gating_disabled_returns_advanced_settings_message(
    platform_api, authenticated_author, monkeypatch
):
    """Return the service's validation message when gating is disabled."""
    client, _ = authenticated_author
    message = "Subsection Prerequisites must be enabled in Advanced Settings."
    setup = Mock(side_effect=ValueError(message))
    monkeypatch.setattr(gating, "setup_sequential_gating", setup)

    response = client.post(setup_url())

    assert response.status_code == 400
    assert response.json() == {"error": message}


def test_success_returns_total_and_gated_counts(
    platform_api, authenticated_author, monkeypatch
):
    """Return success and counts from the gating service."""
    client, user = authenticated_author
    setup = Mock(return_value={"total": 12, "gated": 11})
    monkeypatch.setattr(gating, "setup_sequential_gating", setup)

    response = client.post(setup_url())

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "total_subsections": 12,
        "gating_configured": 11,
    }
    setup.assert_called_once_with(COURSE_ID, user)


def test_unexpected_service_error_is_logged_and_returns_json_500(
    platform_api, authenticated_author, monkeypatch
):
    """Log unexpected service errors and return JSON rather than a traceback."""
    client, _ = authenticated_author
    setup = Mock(side_effect=RuntimeError("unexpected failure"))
    monkeypatch.setattr(gating, "setup_sequential_gating", setup)
    log_exception = Mock()
    monkeypatch.setattr("auto_prereq_gating.views.log.exception", log_exception)

    response = client.post(setup_url())

    assert response.status_code == 500
    assert response.json() == {
        "error": "An unexpected error occurred. Check server logs."
    }
    log_exception.assert_called_once_with(
        "Unexpected error in auto-gating setup for %s", COURSE_ID
    )
