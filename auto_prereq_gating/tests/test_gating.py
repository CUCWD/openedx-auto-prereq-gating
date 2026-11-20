"""Tests for automatic subsection prerequisite configuration."""

# Pytest fixtures are passed as test parameters by design.
# pylint: disable=redefined-outer-name, no-member

import sys
from contextlib import nullcontext
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from auto_prereq_gating.gating import (
    configure_sequential_prerequisites,
    remove_all_gating,
    remove_subsection_prerequisites,
    setup_sequential_gating,
)


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
        location=BlockLocation(name),
        prereq="existing-prerequisite",
        prereq_min_score=50,
        prereq_min_completion=50,
    )


class BlockLocation:
    """Stand in for an opaque block locator, which is not a string."""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"block-v1:org+course+run+type@sequential+block@{self.name}"


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


@pytest.mark.parametrize("value", [-1, 101, 1.5, True])
def test_invalid_service_thresholds_rejected(value):
    """Reject invalid threshold values before accessing the modulestore."""
    with pytest.raises(ValueError, match="Thresholds"):
        setup_sequential_gating("course-v1:org+course+run", None, value)


@pytest.mark.django_db
def test_configure_rejects_disabled_gating():
    """The configuration service checks the course's advanced setting."""
    with pytest.raises(ValueError, match="Advanced Settings"):
        configure_sequential_prerequisites("course-v1:org+course+run", make_course(enabled=False))


@pytest.mark.django_db
def test_single_subsection_rejected(modulestore_modules):
    """A course needs at least two subsections for a chain."""
    course = make_course([make_subsection("only")])
    store, user = configure_store(modulestore_modules, course)

    with pytest.raises(ValueError, match="at least two subsections"):
        setup_sequential_gating("course-v1:org+course+run", user)

    store.update_item.assert_not_called()
    store.bulk_operations.assert_not_called()


def test_setup_uses_gating_service(modulestore_modules, monkeypatch):
    """The button endpoint uses the milestone-backed gating service."""
    first, second, third = (make_subsection(name) for name in ("first", "second", "third"))
    course = make_course([first, second], [third])
    store, user = configure_store(modulestore_modules, course)
    course_key = "course-v1:org+course+run"
    branch, _, _ = modulestore_modules
    configure = MagicMock(return_value=(3, 2))
    monkeypatch.setattr("auto_prereq_gating.gating.configure_sequential_prerequisites", configure)

    assert setup_sequential_gating(course_key, user) == {"total": 3, "gated": 2}

    store.branch_setting.assert_called_once_with(branch, course_key)
    store.get_course.assert_called_once_with(course_key, depth=2)
    configure.assert_called_once_with(course_key, course, 100, 0)
    store.update_item.assert_not_called()


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
    api_module.is_prerequisite = MagicMock(return_value=True)
    api_module.set_required_content = MagicMock()
    for name, module in openedx_modules.items():
        monkeypatch.setitem(__import__("sys").modules, name, module)

    first, second = make_subsection("first"), make_subsection("second")
    course = make_course([first, second])
    course_key = "course-v1:org+course+run"

    assert configure_sequential_prerequisites(course_key, course, 75, 80) == (2, 1)

    api_module.set_required_content.assert_any_call(course_key, str(first.location), None)
    api_module.add_prerequisite.assert_not_called()
    api_module.set_required_content.assert_any_call(
        course_key,
        str(second.location),
        str(first.location),
        min_score=80,
        min_completion=75,
    )


@pytest.mark.django_db
def test_four_subsections_form_chain_across_sections(modulestore_modules, monkeypatch):
    """Configure every gate in outline order, including across sections."""
    api = ModuleType("openedx.core.lib.gating.api")
    api.add_prerequisite = MagicMock()
    api.is_prerequisite = MagicMock(return_value=False)
    api.set_required_content = MagicMock()
    for name in ("openedx", "openedx.core", "openedx.core.lib", "openedx.core.lib.gating"):
        module = ModuleType(name)
        module.__path__ = []
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setitem(sys.modules, "openedx.core.lib.gating.api", api)

    subsections = [make_subsection(str(i)) for i in range(4)]
    course = make_course(subsections[:2], [SimpleNamespace(category="other"), *subsections[2:]])
    store, user = configure_store(modulestore_modules, course)
    key = "course-v1:org+course+run"

    assert setup_sequential_gating(key, user) == {"total": 4, "gated": 3}
    assert api.set_required_content.call_count == 4
    api.set_required_content.assert_any_call(key, str(subsections[0].location), None)
    for previous, current in zip(subsections, subsections[1:]):
        api.add_prerequisite.assert_any_call(key, str(previous.location))
        api.set_required_content.assert_any_call(
            key, str(current.location), str(previous.location), min_score=0, min_completion=100
        )
    assert api.add_prerequisite.call_count == 3
    store.update_item.assert_not_called()


@pytest.mark.django_db
def test_remove_prerequisites_clears_requirements_before_markers(monkeypatch):
    """Clear requirements before removing their prerequisite markers."""
    api = ModuleType("openedx.core.lib.gating.api")
    calls = []
    api.get_required_content = lambda course, key: ("manual", 0, 100) if key.endswith("@b") else (None, None, None)
    api.set_required_content = lambda course, key, value: calls.append(("clear", key))
    api.is_prerequisite = lambda course, key: key.endswith("@a")
    api.remove_prerequisite = lambda key: calls.append(("marker", key))
    monkeypatch.setitem(sys.modules, "openedx.core.lib.gating.api", api)
    course = make_course([make_subsection("a"), make_subsection("b")])
    assert remove_subsection_prerequisites("course", course) == (2, 1)
    assert [(action, key.split("@")[-1]) for action, key in calls] == [("clear", "b"), ("marker", "a")]


def test_remove_all_gating_uses_draft_course(modulestore_modules, monkeypatch):
    """Load the draft course and return removal totals from the service."""
    course = make_course([make_subsection("a"), make_subsection("b")])
    store, user = configure_store(modulestore_modules, course)
    branch, _, _ = modulestore_modules
    remove = MagicMock(return_value=(2, 1))
    monkeypatch.setattr("auto_prereq_gating.gating.remove_subsection_prerequisites", remove)
    course_key = "course-v1:org+course+run"

    assert remove_all_gating(course_key, user) == {"total": 2, "removed": 1}
    store.branch_setting.assert_called_once_with(branch, course_key)
    store.get_course.assert_called_once_with(course_key, depth=2)
    remove.assert_called_once_with(course_key, course)


@pytest.mark.parametrize("raise_not_found", [False, True])
def test_remove_all_gating_reports_missing_course(modulestore_modules, raise_not_found):
    """Report missing courses returned or raised by the modulestore."""
    _, _, exceptions_module = modulestore_modules
    store, user = configure_store(modulestore_modules, None)
    if raise_not_found:
        store.get_course.side_effect = exceptions_module.ItemNotFoundError("missing")

    with pytest.raises(ValueError, match="Course not found"):
        remove_all_gating("course-v1:org+course+run", user)
