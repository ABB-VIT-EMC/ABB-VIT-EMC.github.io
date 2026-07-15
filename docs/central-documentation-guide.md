# Central documentation guide

This repository is the public documentation hub for ABB VIT EMC projects. It
builds a single GitHub Pages site from Sphinx documentation stored in project
repositories such as `saarto`, `matta`, and `AutoTestLib`.

The hub owns publishing and presentation. Each project continues to own its
own documentation source files.

## Design

```text
project repository ──┐
                       ├─ Git submodules in modules/ ── central build ── GitHub Pages
project repository ──┘                                      (Book theme)
```

The scheduled central build deliberately uses the latest commit of each
submodule's tracked branch. It does **not** commit updated submodule pointers.
This means source documentation can change without creating automated commits
in this repository.

## What is already configured

| File | Purpose |
| --- | --- |
| `.github/workflows/publish-docs.yml` | Builds and deploys the Pages artifact every 15 minutes, on manual runs, and after central configuration changes. |
| `tools/build_docs.py` | Builds the hub and every project listed in `docs/projects.toml`. |
| `docs/projects.toml` | The single inventory of published projects. |
| `docs/hub/conf.py` | The hub Sphinx configuration, using `sphinx_book_theme`. |
| `docs/hub/index.rst` | The source of the generated homepage. |

Build output is written to `_site/`; it is ignored by Git and uploaded directly
to GitHub Pages. The root-level `index.html` is the legacy branch-publishing
page and is not used after Pages is switched to GitHub Actions.

## One-time GitHub Pages setup

After committing the workflow:

1. Open the `ABB-VIT-EMC.github.io` repository on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, choose **GitHub Actions**.
4. Run the **Publish documentation** workflow from the Actions tab once.
5. Open the deployment URL reported by the workflow.

GitHub Pages supports custom GitHub Actions workflows for builds that need more
than a branch copy, such as this Sphinx build. See [GitHub Pages publishing
sources](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Add a public documentation project

### 1. Add the project as a submodule

Run this from the root of this repository. Use the branch that should be
published, normally `main`.

```bash
git submodule add -b main https://github.com/ABB-VIT-EMC/saarto.git modules/saarto
git commit -m "docs: add saarto source submodule"
```

The resulting `.gitmodules` entry should retain `branch = main`. The workflow
uses `git submodule update --remote`, so it fetches the newest commit on that
branch every time it runs.

### 2. Register the Sphinx source directory

Add an entry to `docs/projects.toml`:

```toml
[[project]]
name = "SAARTO"
slug = "saarto"
source = "modules/saarto/docs/source"
requirements = "modules/saarto/docs/requirements.txt"
```

Fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | Yes | Display name on the hub Projects page. |
| `slug` | Yes | Public URL folder, for example `/saarto/`. Must be unique. |
| `source` | Yes | Directory containing the project's Sphinx `conf.py`. |
| `requirements` | No | Project-specific Python requirements for Sphinx extensions. |

Omit `requirements` when the project only needs Sphinx and the Book theme.
Keep documentation-only dependencies in a small requirements file where
possible. If importing the package is required by `conf.py`, make sure its
requirements are listed there too.

### 3. Verify and publish

```bash
python -m pip install sphinx sphinx-book-theme
python tools/build_docs.py
```

Check `_site/saarto/index.html` locally, commit the submodule and TOML changes,
then push. The action will publish the combined site.

## Theme migration: Shibuya to Sphinx Book Theme

The central builder currently passes this Sphinx override to every registered
project:

```text
-D html_theme=sphinx_book_theme
```

Therefore newly generated public pages use the Book theme immediately, without
editing the documentation content or each project's `conf.py`. Theme-specific
Shibuya options are normally ignored by the Book theme, but a project can still
fail if it depends on a Shibuya-only extension, template, or CSS selector.

When ready to migrate a source project permanently, change only its build
configuration:

```python
# docs/source/conf.py
html_theme = "sphinx_book_theme"
```

Then remove `shibuya` from its documentation dependencies and review custom
CSS/templates. The Book theme exposes options such as repository buttons,
navigation depth, and source paths through `html_theme_options`; see the
[Sphinx Book Theme reference](https://sphinx-book-theme.readthedocs.io/en/stable/reference.html).

Do this project by project. It is intentionally not part of the central setup,
so source documentation content stays unchanged until each project is ready.

## Private submodules

The default GitHub Actions `GITHUB_TOKEN` is scoped to this repository, so it
cannot clone private submodules. Give the central workflow a separate,
read-only credential.

### Recommended for many projects: GitHub App

Create a GitHub App and install it only on this hub repository and the private
documentation-source repositories. Grant **Contents: Read-only**. Store its
client ID as the `DOCS_APP_CLIENT_ID` Actions variable and its generated private
key as the `DOCS_APP_PRIVATE_KEY` Actions secret in this repository. The workflow
generates a short-lived installation token and provides it to `actions/checkout`.

This is preferred over a personal token because it is not tied to an employee
account and can be limited to selected repositories.

### Simple option: fine-grained PAT

Create a fine-grained PAT for a bot/service account with:

* Repository access limited to the required private source repositories.
* **Contents: Read-only** permission.

Save it in this repository as the Actions secret `DOCS_SUBMODULE_TOKEN`, then
change the checkout step in `publish-docs.yml`:

```yaml
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.DOCS_SUBMODULE_TOKEN }}
    submodules: recursive
```

The later `git submodule update --remote --recursive` reuses that authenticated
checkout configuration. GitHub's checkout action documents that a separate PAT
is required when checking out another private repository. See
[actions/checkout](https://github.com/actions/checkout).

Never place a token in `.gitmodules`, a Git URL, a build log, or a committed
file.

## Scheduled versus immediate updates

The current design is intentionally low-maintenance:

| Approach | Credential needed | Delay | Source-repo changes |
| --- | --- | --- | --- |
| Scheduled central refresh (current) | No for public modules; read credential for private modules | Up to roughly 15 minutes, plus GitHub scheduling delay | None |
| `repository_dispatch` on source push | Yes, to trigger the hub | Usually minutes | One small workflow in every source repo |

Use the scheduled approach unless an immediate publish is genuinely needed.
If that changes, add a `repository_dispatch` trigger to the hub workflow and a
small notification workflow to each source repository. The central build and
project inventory remain the same.

## Security checklist

The deployed Pages site is public. Before registering a project, confirm that
its generated HTML does not expose:

* credentials, access tokens, or internal hostnames;
* private API schemas or implementation details that should remain private;
* source links pointing to repositories that must not be disclosed.

Restrict a private-submodule credential to read-only access and only the
specific repositories required. Rotate a PAT immediately if it is exposed;
prefer a GitHub App for long-lived automation.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `Repository not found` during checkout | A private submodule lacks an authorized PAT/App token, or the token is not supplied to `actions/checkout`. |
| `no theme named sphinx_book_theme` | Install `sphinx-book-theme`; the workflow already does this. |
| `no Sphinx source at ...` | Correct the `source` path in `docs/projects.toml`; it must contain `conf.py`. |
| Missing Python extension/module | Add a documentation requirements file and set the project's `requirements` field. |
| Site still shows the old landing page | Switch Pages publishing to **GitHub Actions** and inspect the most recent deploy job. |
| Two projects overwrite each other | Give every project a distinct `slug`. |
