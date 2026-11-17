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
