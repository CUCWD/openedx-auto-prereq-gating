"""Tests for automatic subsection prerequisite configuration."""

# Pytest fixtures are passed as test parameters by design.
# pylint: disable=redefined-outer-name

from contextlib import nullcontext
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from auto_prereq_gating.gating import configure_sequential_prerequisites, setup_sequential_gating


@pytest.fixture
def modulestore_modules(monkeypatch):
    """Install lightweight xmodule modulestore modules for isolated tests."""
    xmodule = ModuleType("xmodule")
    modulestore_module = ModuleType("xmodule.modulestore")
    django_module = ModuleType("xmodule.modulestore.django")
    exceptions_module = ModuleType("xmodule.modulestore.exceptions")
    branch = object()
    modulestore_module.ModuleStoreEnum = SimpleNamespace(
        Branch=SimpleNamespace(draft_preferred=branch)
    )
    exceptions_module.ItemNotFoundError = type("ItemNotFoundError", (Exception,), {})

    for name, module in (
        ("xmodule", xmodule),
        ("xmodule.modulestore", modulestore_module),
        ("xmodule.modulestore.django", django_module),
        ("xmodule.modulestore.exceptions", exceptions_module),
    ):
        monkeypatch.setitem(__import__("sys").modules, name, module)

    return branch, django_module, exceptions_module


def make_course(*subsection_groups, enabled=True):
    """Build a course whose section children preserve the supplied order."""
    sections = [SimpleNamespace(get_children=lambda group=group: group) for group in subsection_groups]
    return SimpleNamespace(
        enable_subsection_gating=enabled,
        get_children=lambda: sections,
    )


def make_subsection(name):
    return SimpleNamespace(
        category="sequential",
        location=f"block-v1:org+course+run+type@sequential+block@{name}",
        prereq="existing-prerequisite",
        prereq_min_score=50,
        prereq_min_completion=50,
    )


def configure_store(modulestore_modules, course):
    """Configure a mocked modulestore for the requested course."""
    _, django_module, _ = modulestore_modules
    store = MagicMock()
    store.branch_setting.return_value = nullcontext()
    store.bulk_operations.return_value = nullcontext()
    store.get_course.return_value = course
    django_module.modulestore = lambda: store
    user = SimpleNamespace(id=42)
    return store, user


def test_missing_course_raises_value_error(modulestore_modules):
    """Report a missing course when the modulestore returns no course."""
    store, user = configure_store(modulestore_modules, None)

    with pytest.raises(ValueError, match="Course not found"):
        setup_sequential_gating("course-v1:org+course+run", user)

    store.update_item.assert_not_called()


def test_modulestore_missing_course_error_is_reported(modulestore_modules):
    """Convert the modulestore's missing-item exception to ValueError."""
    _, _, exceptions_module = modulestore_modules
    store, user = configure_store(modulestore_modules, None)
    store.get_course.side_effect = exceptions_module.ItemNotFoundError("missing")

    with pytest.raises(ValueError, match="Course not found"):
        setup_sequential_gating("course-v1:org+course+run", user)


def test_gating_must_be_enabled(modulestore_modules):
    """Reject courses without subsection gating enabled."""
    course = make_course(enabled=False)
    store, user = configure_store(modulestore_modules, course)

    with pytest.raises(ValueError, match="Advanced Settings"):
        setup_sequential_gating("course-v1:org+course+run", user)

    store.update_item.assert_not_called()


def test_single_subsection_returns_without_writes(modulestore_modules):
    """Avoid updates when there is only one subsection."""
    course = make_course([make_subsection("only")])
    store, user = configure_store(modulestore_modules, course)

    assert setup_sequential_gating("course-v1:org+course+run", user) == {
        "total": 1,
        "gated": 0,
    }

    store.update_item.assert_not_called()
    store.bulk_operations.assert_not_called()


def test_subsections_are_gated_in_flattened_course_order(modulestore_modules):
    """Write each predecessor relationship in flattened course order."""
    first, second, third = (make_subsection(name) for name in ("first", "second", "third"))
    course = make_course([first, second], [third])
    store, user = configure_store(modulestore_modules, course)
    course_key = "course-v1:org+course+run"
    branch, _, _ = modulestore_modules

    assert setup_sequential_gating(course_key, user) == {"total": 3, "gated": 2}

    store.branch_setting.assert_called_once_with(branch, course_key)
    store.get_course.assert_called_once_with(course_key, depth=2)
    store.bulk_operations.assert_called_once_with(course_key)
    store.update_item.assert_has_calls(
        [call(first, user.id), call(second, user.id), call(third, user.id)]
    )
    assert first.prereq == ""
    for subsection, previous in ((second, first), (third, second)):
        assert subsection.prereq == str(previous.location)
        assert subsection.prereq_min_score == 0
        assert subsection.prereq_min_completion == 100


@pytest.mark.django_db
def test_configure_sequential_prerequisites_uses_openedx_gating_api(monkeypatch):
    """Keep the existing gating API integration available and configured."""
    openedx_modules = {
        name: ModuleType(name)
        for name in (
            "openedx",
            "openedx.core",
            "openedx.core.lib",
            "openedx.core.lib.gating",
            "openedx.core.lib.gating.api",
        )
    }
    api_module = openedx_modules["openedx.core.lib.gating.api"]
    api_module.add_prerequisite = MagicMock()
    api_module.is_prerequisite = MagicMock(return_value=False)
    api_module.set_required_content = MagicMock()
    for name, module in openedx_modules.items():
        monkeypatch.setitem(__import__("sys").modules, name, module)

    first, second = make_subsection("first"), make_subsection("second")
    course = make_course([first, second])
    course_key = "course-v1:org+course+run"

    assert configure_sequential_prerequisites(course_key, course) == (2, 1)

    api_module.set_required_content.assert_any_call(course_key, first.location, None)
    api_module.add_prerequisite.assert_called_once_with(course_key, first.location)
    api_module.set_required_content.assert_any_call(
        course_key,
        second.location,
        first.location,
        min_score=0,
        min_completion=100,
    )
