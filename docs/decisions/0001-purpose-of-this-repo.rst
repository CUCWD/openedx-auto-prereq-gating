0001 Purpose of This Repo
#########################

Status
******

**Provisional**

Context
*******

Course teams currently configure subsection prerequisites one subsection at
a time in Studio. Courses that follow a sequential progression need a quicker
way to apply the same rule consistently across the outline.

Decision
********

We will provide a reusable CMS Django app that configures sequential
subsection prerequisites through Open edX's gating API. A separately
versioned Studio frontend package will provide the course outline action that
invokes the API. The backend owns the rule and applies 100% completion of the
preceding subsection to each subsequent subsection.

Consequences
************

The frontend package can be versioned independently from
frontend-app-authoring, leaving a small slot integration in the host app.
The CMS package must be installed and discovered by edx-platform. Enabling
subsection gating remains a course setting, and applying the action replaces
existing prerequisite settings for affected subsections.

Rejected Alternatives
*********************

Editing Redux and course outline components directly in
frontend-app-authoring was rejected because it would create more code to
reconcile during release upgrades and couple the feature to the host
application's internals.

References
**********

Open edX gating API reference:
https://docs.openedx.org/projects/edx-platform/en/latest/references/docstrings/openedx/openedx.core.lib.gating.html
