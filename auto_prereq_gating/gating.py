"""Service functions for applying automatic subsection prerequisites."""

from django.db import transaction


def setup_sequential_gating(course_key, user):
    """Wire prerequisite gating across every subsection in course order.

    Each subsection after the first requires 100% completion of its immediate
    predecessor and a minimum score of 0%. Changes are written to the draft
    branch so they are visible in Studio before publishing.

    Returns a mapping with the number of subsections found and gated.
    """
    # Import from edx-platform only when this service is called, so the package
    # remains importable in standalone Django environments.
    # pylint: disable=import-outside-toplevel, import-error
    from xmodule.modulestore import ModuleStoreEnum
    from xmodule.modulestore.django import modulestore
    from xmodule.modulestore.exceptions import ItemNotFoundError

    store = modulestore()
    try:
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course_key):
            course = store.get_course(course_key, depth=2)
            if course is None:
                raise ValueError(f"Course not found: {course_key}")

            if not getattr(course, "enable_subsection_gating", False):
                raise ValueError(
                    "Subsection Prerequisites must be enabled in Advanced Settings "
                    "before auto-gating can be configured."
                )

            subsections = get_ordered_subsections(course)
            if len(subsections) < 2:
                return {"total": len(subsections), "gated": 0}

            with store.bulk_operations(course_key):
                for index, subsection in enumerate(subsections):
                    subsection.prereq = (
                        str(subsections[index - 1].location) if index else ""
                    )
                    subsection.prereq_min_score = 0
                    subsection.prereq_min_completion = 100
                    store.update_item(subsection, user.id)
    except ItemNotFoundError as error:
        raise ValueError(f"Course not found: {course_key}") from error

    return {"total": len(subsections), "gated": len(subsections) - 1}


class GatingConfigurationError(ValueError):
    """Raised when a course cannot be configured for sequential gating."""


def get_ordered_subsections(course):
    """Return all course subsections in outline order."""
    subsections = []
    for section in course.get_children():
        for subsection in section.get_children():
            if subsection.category == "sequential":
                subsections.append(subsection)
    return subsections


@transaction.atomic
def configure_sequential_prerequisites(course_key, course):
    """Gate each subsection on the previous subsection's 100% completion.

    Existing prerequisite requirements on these subsections are replaced by
    the sequential chain. A subsection with no predecessor is left ungated.
    """
    # pylint: disable=import-outside-toplevel
    from openedx.core.lib.gating.api import add_prerequisite, is_prerequisite, set_required_content

    if not course.enable_subsection_gating:
        raise GatingConfigurationError(
            "Enable subsection gating in the course's Advanced Settings first."
        )

    subsections = get_ordered_subsections(course)
    if len(subsections) < 2:
        raise GatingConfigurationError(
            "The course needs at least two subsections to configure sequential gating."
        )

    # Remove any prior gate from the first subsection: it has no predecessor.
    set_required_content(course_key, subsections[0].location, None)

    for previous, current in zip(subsections, subsections[1:]):
        if not is_prerequisite(course_key, previous.location):
            add_prerequisite(course_key, previous.location)
        set_required_content(
            course_key,
            current.location,
            previous.location,
            min_score=0,
            min_completion=100,
        )

    return len(subsections), len(subsections) - 1
