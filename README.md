# ABB VIT EMC documentation hub

This repository builds and publishes the shared documentation site at
[abb-vit-emc.github.io](https://abb-vit-emc.github.io/). Each software project
keeps its documentation in its own repository. This hub checks those projects
out as Git submodules, builds every Sphinx site, and publishes them together
with a common landing page.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/hub/` | Source for the main landing page. Edit `index.rst` for its content and `_static/custom.css` for hub-specific styling. |
| `docs/projects.toml` | The authoritative list of project documentation to build and show in the hub navigation. |
| `modules/` | Git submodules containing the source repositories. Do not maintain package documentation as copied files here. |
| `.gitmodules` | Submodule URLs and the branches followed by the automated build. |
| `tools/build_docs.py` | Installs project documentation requirements and builds the hub and project sites. |
| `.github/workflows/publish-docs.yml` | GitHub Actions workflow that refreshes submodules, builds the site, and deploys GitHub Pages. |
| `_site/` | Generated website from a local build. It is ignored by Git. |
| `.docs-build/` | Temporary generated hub source. It is ignored by Git. |

The root `index.html` is a legacy static page. The published home page is built
from `docs/hub/index.rst` into `_site/index.html`.

## How publishing works

The workflow runs in three situations:

- immediately after relevant hub files are pushed to `main`;
- every 15 minutes, so documentation pushed to a project repository is picked up;
- manually through **Actions > Publish documentation > Run workflow**.

During a run, GitHub Actions creates a short-lived GitHub App token, checks out
the submodules, follows their configured branches, builds each project with
Sphinx, builds the landing page, and deploys `_site/` to GitHub Pages.

A push to `saarto`, `AutoTestLib`, `matta`, or another source repository does
not directly start this repository's workflow. The scheduled run normally
publishes it within 15 minutes. Use the manual workflow when an update must be
available immediately.

## Normal documentation update

Package documentation belongs to the package repository:

1. Edit files under that package's `docs/source/` directory.
2. Build the documentation locally and fix every warning. The central build
   treats Sphinx warnings as errors.
3. Commit and push the change to the branch configured in `.gitmodules`,
   normally `main`.
4. Wait for the scheduled hub workflow, or run it manually.
5. Check the project page on the published site.

There is normally no need to commit an updated submodule pointer to this hub:
the workflow runs `git submodule update --remote` and follows the configured
branch. A pointer may still be updated when making an intentional, reviewed hub
change that should record a known source revision.

To change the landing page or project list, edit this repository directly,
commit the change to `main`, and let the push-triggered workflow deploy it.

## Local setup and build

Python 3.12 matches the CI environment. On Windows PowerShell:

```powershell
git clone --recurse-submodules https://github.com/ABB-VIT-EMC/ABB-VIT-EMC.github.io.git
cd ABB-VIT-EMC.github.io
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip sphinx shibuya
git submodule update --init --remote --recursive
python tools/build_docs.py
python -m http.server 8000 --directory _site
```

Open <http://localhost:8000>. The builder automatically installs every
project-specific `docs/requirements.txt` listed in `docs/projects.toml`.

If the repository was cloned without its submodules, run:

```powershell
git submodule update --init --recursive
```

To refresh only one source repository:

```powershell
git submodule update --init --remote modules/saarto
```

## Add a project

Before adding a project, make sure its repository contains a working Sphinx
site, normally with:

```text
docs/
|-- requirements.txt
`-- source/
    |-- conf.py
    `-- index.rst
```

Then:

1. Add the repository as a submodule under `modules/` and configure its branch.

   ```powershell
   git submodule add -b main https://github.com/ABB-VIT-EMC/PROJECT.git modules/PROJECT
   ```

2. Add an entry to `docs/projects.toml`.

   ```toml
   [[project]]
   name = "PROJECT - Short description"
   slug = "PROJECT"
   source = "modules/PROJECT/docs/source"
   requirements = "modules/PROJECT/docs/requirements.txt"
   ```

3. If the repository is private, install the documentation GitHub App on it.
4. Run `python tools/build_docs.py` and correct all warnings.
5. Commit `.gitmodules`, the new submodule pointer, and
   `docs/projects.toml`, then push them together.

The `slug` becomes the public URL path and is case-sensitive. Avoid changing an
existing slug because old links will stop working.

## Remove a project

Remove its entry from `docs/projects.toml`, remove the submodule using the
normal Git submodule procedure, build locally, and commit all related changes
together. Removing only the registry entry stops the project from being built
but leaves the submodule in the repository.

## Private submodules and GitHub App access

The publishing workflow uses these repository or organization settings:

- variable `DOCS_APP_CLIENT_ID`: the GitHub App client ID;
- secret `DOCS_APP_PRIVATE_KEY`: the complete private-key file contents.

The GitHub App must be installed on this hub repository and every private
source repository that the workflow checks out. It only needs repository
**Contents: Read-only** permission. Never commit the private key, an installation
token, or a personal access token.

If a new private project fails during checkout, verify the App installation
includes that repository and that the two Actions settings above are present.

## Themes and navigation

Each project owns its Sphinx theme configuration in its own
`docs/source/conf.py`. The central builder does not override it. Keep the theme
package in that project's `docs/requirements.txt`.

The project links in the hub sidebar are generated from `docs/projects.toml`.
Do not edit `.docs-build/hub/projects.rst`; it is regenerated on every build.

## Troubleshooting

### The build finishes with warnings treated as errors

The builder deliberately uses `sphinx -W --keep-going`. Read all warnings,
fix broken references, missing toctree entries, duplicate labels, and autodoc
import errors, then rebuild locally.

### Autodoc cannot import a package

Check that the project's `conf.py` makes its `src/` directory importable and
that documentation dependencies are listed in `docs/requirements.txt`.
Optional hardware or platform-only dependencies may need documented autodoc
mocks, but the package itself should remain importable during the build.

### A pushed project update is not visible

Check the latest **Publish documentation** workflow run. Confirm that:

- the update was pushed to the branch configured in `.gitmodules`;
- the scheduled workflow has run since the push;
- the GitHub App can read the source repository;
- Sphinx completed without warnings or errors;
- the expected URL uses the exact `slug` from `docs/projects.toml`.

Run the workflow manually after correcting the problem.

### A submodule is in detached HEAD state locally

That is normal after a standard submodule checkout. To edit package
documentation, enter the package repository, switch to its maintained branch,
commit there, and push to that repository. Do not accidentally commit package
changes only as a hub submodule pointer.

## Maintainer checklist

Before merging a hub change:

- update `docs/projects.toml` and `.gitmodules` consistently;
- run `python tools/build_docs.py` successfully;
- verify the landing page and affected project under `_site/`;
- keep generated `_site/` and `.docs-build/` files out of Git;
- confirm private repositories remain accessible to the documentation App;
- review the deployed GitHub Pages URL after the workflow completes.
