"""Build the documentation hub and all configured Sphinx submodule projects."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONFIG = ROOT / "docs" / "projects.toml"
PLUGIN_CONFIG = ROOT / "docs" / "plugins.toml"
HUB_SOURCE = ROOT / "docs" / "hub"
WORK = ROOT / ".docs-build"
SITE = ROOT / "_site"
SITE_URL = "https://abb-vit-emc.github.io"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def load_tables(path: Path, table: str) -> list[dict[str, object]]:
    config = tomllib.loads(path.read_text(encoding="utf-8"))
    entries = config.get(table, [])
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError(f"'{table}' must be an array of tables in {path.relative_to(ROOT)}")
    return entries


def required_text(entry: dict[str, object], field: str, label: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} requires a non-empty '{field}'")
    return value.strip()


def rst_text(value: str) -> str:
    for character in ("\\", "`", "*", "|", "_"):
        value = value.replace(character, f"\\{character}")
    return value


def render_plugins(entries: list[dict[str, object]]) -> str:
    lines = [
        "Plugins",
        "=======",
        "",
        "Plugins extend an application without becoming part of its core package.",
        "Configuration and usage documentation lives in each plugin repository's",
        "``README``.",
        "",
    ]
    for index, entry in enumerate(entries, start=1):
        label = f"plugin {index}"
        name = rst_text(required_text(entry, "name", label))
        description = rst_text(required_text(entry, "description", label))
        repository = required_text(entry, "repository", label)
        if not repository.startswith(("https://", "http://")):
            raise ValueError(f"{label} requires an HTTP(S) 'repository' URL")
        lines.extend((f"* `{name} <{repository}>`_ — {description}", ""))

    lines.extend(
        (
            "Maintaining this page",
            "---------------------",
            "",
            "``docs/plugins.toml`` is the source of truth. To add a plugin, append",
            "one ``[[plugins]]`` table containing only ``name``, ``description``, and",
            "``repository``. The page is regenerated automatically during each build.",
            "",
        )
    )
    return "\n".join(lines)


def main() -> None:
    projects = load_tables(PROJECT_CONFIG, "project")
    plugins = load_tables(PLUGIN_CONFIG, "plugins")

    shutil.rmtree(WORK, ignore_errors=True)
    shutil.rmtree(SITE, ignore_errors=True)
    shutil.copytree(HUB_SOURCE, WORK / "hub")
    (WORK / "hub" / "plugins.rst").write_text(render_plugins(plugins), encoding="utf-8")
    SITE.mkdir(parents=True)

    links: list[tuple[str, str]] = []
    for index, project in enumerate(projects, start=1):
        label = f"project {index}"
        name = required_text(project, "name", label)
        slug = required_text(project, "slug", label)
        source = ROOT / required_text(project, "source", label)
        if not source.is_dir() or not (source / "conf.py").is_file():
            raise FileNotFoundError(f"{name}: no Sphinx source at {source}")

        requirements = project.get("requirements")
        if requirements:
            if not isinstance(requirements, str):
                raise ValueError(f"{label} 'requirements' must be a path string")
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
            str(source),
            str(SITE / slug),
        )
        nav_title = project.get("nav_title", name.split(" - ", 1)[0])
        if not isinstance(nav_title, str) or not nav_title.strip():
            raise ValueError(f"{label} 'nav_title' must be a non-empty string")
        links.append((str(nav_title), f"{SITE_URL}/{slug}/"))

    project_tree = ".. toctree::\n   :caption: Projects\n   :maxdepth: 1\n   :hidden:\n\n"
    project_tree += "\n".join(
        f"   {escape(title)} <{escape(url)}>" for title, url in links
    )
    (WORK / "hub" / "projects.rst").write_text(project_tree + "\n", encoding="utf-8")

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
