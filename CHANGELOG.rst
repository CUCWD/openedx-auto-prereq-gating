Change Log
##########

..
   All enhancements and patches to auto_prereq_gating will be documented
   in this file.  It adheres to the structure of https://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (https://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
**********

*

1.0.2 – 2026-11-20
******************

Added
=====

* Added regression coverage for API requests whose data stream has already
  been consumed by DRF request parsing.

Fixed
=====

* Read setup and configuration payloads from DRF's parsed request data to
  prevent ``RawPostDataException`` responses after authentication consumes the
  raw request stream.
* Preserve HTTP 400 responses for malformed JSON instead of reporting an
  unexpected server error.

1.0.1 – 2026-11-20
******************

Added
=====

* Added an API endpoint that removes subsection prerequisite relationships and
  prerequisite markers from a course.
* Added service and API tests for successful gating removal, missing courses,
  invalid course IDs, author access, validation errors, and unexpected errors.

Fixed
=====

* Authenticate requests to remove course gating with Open edX's standard JWT,
  OAuth bearer, and Studio session authentication policy so the Authoring MFE
  can call the endpoint.
* Corrected lazy platform import formatting and lint suppressions so the
  package passes its CI quality checks.

1.0.0 – 2026-11-20
******************

Added
=====

* Added CMS endpoints for configuring sequential subsection prerequisites.
* Added configurable minimum-completion and minimum-score thresholds.
* Added backend tests for request validation, course authorization, and gating
  behavior.

Changed
========

* Authenticate MFE API requests with Open edX's standard JWT, OAuth bearer,
  and Studio session authentication policy.
* Consolidated project documentation in ``README.md``.

Fixed
=====

* Prevent authenticated Authoring MFE requests from being redirected to the
  LMS OAuth flow and reported by browsers as CORS failures.
* Validate subsection gating before loading platform APIs and configure gates
  through the Open edX gating service.

0.2.0 – 2026-10-08
******************

Added
=====

* First release on PyPI.
