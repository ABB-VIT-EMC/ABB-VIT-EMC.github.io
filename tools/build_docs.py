"""Build the documentation hub and all configured Sphinx submodule projects."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "docs" / "projects.toml"
HUB_SOURCE = ROOT / "docs" / "hub"
WORK = ROOT / ".docs-build"
SITE = ROOT / "_site"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    projects = config.get("project", [])
    if not isinstance(projects, list):
        raise ValueError("'project' must be an array in docs/projects.toml")

    shutil.rmtree(WORK, ignore_errors=True)
    shutil.rmtree(SITE, ignore_errors=True)
    shutil.copytree(HUB_SOURCE, WORK / "hub")
    SITE.mkdir(parents=True)

    links: list[str] = []
    for project in projects:
        name = project["name"]
        slug = project["slug"]
        source = ROOT / project["source"]
        if not source.is_dir() or not (source / "conf.py").is_file():
            raise FileNotFoundError(f"{name}: no Sphinx source at {source}")

        requirements = project.get("requirements")
        if requirements:
            requirements_path = ROOT / requirements
            if not requirements_path.is_file():
                raise FileNotFoundError(f"{name}: no requirements file at {requirements_path}")
            run(sys.executable, "-m", "pip", "install", "--requirement", str(requirements_path))

        run(
            sys.executable,
            "-m",
            "sphinx",
            "-W",
            "--keep-going",
            "-b",
            "html",
            "-D",
            "html_theme=furo",
            str(source),
            str(SITE / slug),
        )
        links.append(f"* `{escape(name)} <../{escape(slug)}/>`_")

    project_page = "Projects\n========\n\n"
    project_page += "\n".join(links) if links else "No projects are configured yet."
    (WORK / "hub" / "projects.rst").write_text(project_page + "\n", encoding="utf-8")

    run(
        sys.executable,
        "-m",
        "sphinx",
        "-W",
        "--keep-going",
        "-b",
        "html",
        str(WORK / "hub"),
        str(SITE),
    )


if __name__ == "__main__":
    main()
