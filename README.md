# openedx-auto-prereq-gating

Studio plugin for Open edX Ulmo that adds an **Auto-Setup Prerequisite Gating** button to the course outline. It configures each subsection to require completion of the previous subsection, saving manual setup.

## What it does

- Reads sections and subsections in course order and gates each subsection after the first on its predecessor.
- Defaults to 100% completion and 0% minimum score; authors can choose thresholds in the configuration dialog.
- Shows the button only when **Enable Subsection Prerequisites** is enabled in Advanced Settings.
- Replaces existing prerequisite requirements for the affected subsections. A course must have at least two subsections.

## Compatibility

| Platform | Status |
| --- | --- |
| Open edX Ulmo | Supported |
| Open edX Teak | May work; untested |
| Earlier releases | Not supported; course outline architecture differs |

Enable subsection prerequisites in the course's Advanced Settings before using the button.

## Backend API

The Django app registers its endpoints in Studio under `/auto_prereq_gating/`.
The Authoring MFE calls them with the JWT supplied by
`getAuthenticatedHttpClient`. Studio session and OAuth bearer authentication
are also supported through Open edX's standard `view_auth_classes` policy.
Every endpoint separately verifies that the authenticated user can modify the
requested course.

### Configure gating with custom thresholds

```http
POST /auto_prereq_gating/setup/<course-id>/
Content-Type: application/json

{
  "prereqMinCompletion": 100,
  "prereqMinScore": 0
}
```

Both thresholds must be integers between 0 and 100. The endpoint replaces the
prerequisite requirement on each subsection after the first with a reference
to the preceding subsection.

### Configure default completion gating

```http
POST /auto_prereq_gating/configure/
Content-Type: application/json

{
  "course_key": "course-v1:example+course+run"
}
```

This endpoint applies a 100% minimum-completion requirement. The course must
have subsection prerequisites enabled in Advanced Settings.

## Repo layout

These are separate repositories in this workspace:

| Directory | Package | Purpose |
| --- | --- | --- |
| `openedx-auto-prereq-gating/` | Python | Django API running in CMS |
| `frontend-plugin-auto-prereq-gating/` | JavaScript | React plugin running in the authoring MFE |
| `tutor-plugins/tutor-contrib-auto-prereq-gating/` | Python | Tutor plugin connecting the packages to a deployment |

## Local development setup

### Backend

```bash
cd openedx-auto-prereq-gating
python -m pip install -e .
python -m pip install -r requirements/test.txt 'Django>=4,<5'
# In an edx-platform development environment:
python manage.py cms migrate
```

The backend relies on edx-platform APIs at runtime. The standalone tests mock those APIs.

### Frontend

```bash
cd frontend-plugin-auto-prereq-gating
npm install
npm run build
```

Install the package in your local `frontend-app-authoring` checkout and register `AutoGatingButton` in the course outline header actions slot. The Tutor plugin's MFE configuration patch provides an example of the registration.

### Running tests

Run each command from the workspace root:

```bash
cd openedx-auto-prereq-gating
python -m pytest auto_prereq_gating/tests/ --cov=auto_prereq_gating --cov-report=term-missing
```

```bash
cd frontend-plugin-auto-prereq-gating
npm test
```

## Production deployment with Tutor

With a compatible Ulmo Tutor installation, install the Tutor plugin from its checkout and enable it:

```bash
python -m pip install ./tutor-plugins/tutor-contrib-auto-prereq-gating
tutor plugins enable auto-prereq-gating
tutor images build openedx
tutor images build mfe
tutor local launch
```

The plugin patches install pinned backend and frontend Git revisions during image builds. Update those pins when deploying newer changes. See the Tutor plugin's README for its installation details.

## Getting help

Implementation details and API behavior are documented in this README and the
repository's architecture decision records. For project-specific problems,
[open an issue](https://github.com/CUCWD/openedx-auto-prereq-gating/issues)
with the relevant logs and reproduction steps.

Open edX community support is available through the
[discussion forums](https://discuss.openedx.org), the
[community Slack workspace](https://openedx.slack.com/), and the broader
[Open edX support resources](https://openedx.org/getting-help).

## Contributing

Bug fixes, security fixes, maintenance work, and features are welcome. For
larger changes, open an issue before starting implementation so the approach
can be discussed with the maintainers. Contributors must follow the
[Open edX Code of Conduct](https://openedx.org/code-of-conduct/) and the
[Open edX contribution guidance](https://openedx.org/r/how-to-contribute).

Project ownership and maintainer information is available in
[`catalog-info.yaml`](catalog-info.yaml) and the corresponding
[Backstage entry](https://backstage.openedx.org/catalog/default/component/openedx-auto-prereq-gating).

## Security

Do not report security vulnerabilities in public issues. Email
security@openedx.org instead.

## License

This project is licensed under the GNU Affero General Public License v3.0.
See [LICENSE.txt](LICENSE.txt) for details.
