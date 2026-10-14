"""Service functions for applying automatic subsection prerequisites."""

from django.db import transaction
from openedx.core.lib.gating.api import add_prerequisite, is_prerequisite, set_required_content


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
