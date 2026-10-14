openedx-auto-prereq-gating
##########################

.. note::

  This project is under active development and is not yet published.

|pypi-badge| |ci-badge| |codecov-badge| |doc-badge| |pyversions-badge|
|license-badge| |status-badge|

Purpose
*******

This Django app adds a CMS endpoint that configures sequential subsection
prerequisites for an Open edX course. The Studio frontend plugin calls this
endpoint; the backend uses Open edX's gating API so the platform remains the
source of truth for prerequisite rules.

The configure endpoint is mounted in CMS at
``/auto_prereq_gating/configure/``. It accepts a JSON object containing a
``course_key`` and replaces the prerequisite setting on each subsection after
the first with a requirement for 100% completion of the previous subsection.
The course must have subsection gating enabled in Advanced Settings, and the
requesting user must have Studio write access to the course.

Getting Started with Development
********************************

Install this package into the CMS environment alongside edx-platform so the
``cms.djangoapp`` entry point can register the app. Use the Tutor development
workflow for the target Open edX release. See the Open edX documentation for
`guidance on Python development`_.

.. _guidance on Python development: https://docs.openedx.org/en/latest/developers/how-tos/get-ready-for-python-dev.html

Deploying
*********

This package is not published yet. For local development, install the checkout
into the CMS Python environment and restart CMS after changing the plugin
entry point or URL configuration.

.. _deployment how-to: https://docs.openedx.org/projects/openedx-auto-prereq-gating/how-tos/how-to-deploy-this-component.html

Getting Help
************

Documentation
=============

The implementation and API contract are documented in this README and the
repository's architecture decision records.

More Help
=========

If you're having trouble, we have discussion forums at
https://discuss.openedx.org where you can connect with others in the
community.

Our real-time conversations are on Slack. You can request a `Slack
invitation`_, then join our `community Slack workspace`_.

For anything non-trivial, the best path is to open an issue in this
repository with as many details about the issue you are facing as you
can provide.

https://github.com/CUCWD/openedx-auto-prereq-gating/issues

For more information about these options, see the `Getting Help <https://openedx.org/getting-help>`__ page.

.. _Slack invitation: https://openedx.org/slack
.. _community Slack workspace: https://openedx.slack.com/

License
*******

The code in this repository is licensed under the AGPL 3.0 unless
otherwise noted.

Please see `LICENSE.txt <LICENSE.txt>`_ for details.

Contributing
************

Contributions are very welcome.
Please read `How To Contribute <https://openedx.org/r/how-to-contribute>`_ for details.

This project is currently accepting all types of contributions, bug fixes,
security fixes, maintenance work, or new features.  However, please make sure
to discuss your new feature idea with the maintainers before beginning development
to maximize the chances of your change being accepted.
You can start a conversation by creating a new issue on this repo summarizing
your idea.

The Open edX Code of Conduct
****************************

All community members are expected to follow the `Open edX Code of Conduct`_.

.. _Open edX Code of Conduct: https://openedx.org/code-of-conduct/

People
******

The assigned maintainers for this component and other project details may be
found in `Backstage`_. Backstage pulls this data from the ``catalog-info.yaml``
file in this repo.

.. _Backstage: https://backstage.openedx.org/catalog/default/component/openedx-auto-prereq-gating

Reporting Security Issues
*************************

Please do not report security issues in public. Please email security@openedx.org.

.. |pypi-badge| image:: https://img.shields.io/pypi/v/openedx-auto-prereq-gating.svg
    :target: https://pypi.python.org/pypi/openedx-auto-prereq-gating/
    :alt: PyPI

.. |ci-badge| image:: https://github.com/CUCWD/openedx-auto-prereq-gating/actions/workflows/ci.yml/badge.svg?branch=main
    :target: https://github.com/CUCWD/openedx-auto-prereq-gating/actions/workflows/ci.yml
    :alt: CI

.. |codecov-badge| image:: https://codecov.io/github/CUCWD/openedx-auto-prereq-gating/coverage.svg?branch=main
    :target: https://codecov.io/github/CUCWD/openedx-auto-prereq-gating?branch=main
    :alt: Codecov

.. |doc-badge| image:: https://readthedocs.org/projects/openedx-auto-prereq-gating/badge/?version=latest
    :target: https://docs.openedx.org/projects/openedx-auto-prereq-gating
    :alt: Documentation

.. |pyversions-badge| image:: https://img.shields.io/pypi/pyversions/openedx-auto-prereq-gating.svg
    :target: https://pypi.python.org/pypi/openedx-auto-prereq-gating/
    :alt: Supported Python versions

.. |license-badge| image:: https://img.shields.io/github/license/CUCWD/openedx-auto-prereq-gating.svg
    :target: https://github.com/CUCWD/openedx-auto-prereq-gating/blob/main/LICENSE.txt
    :alt: License

.. TODO: Choose one of the statuses below and remove the other status-badge lines.
.. |status-badge| image:: https://img.shields.io/badge/Status-Experimental-yellow
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Deprecated-orange
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Unsupported-red
