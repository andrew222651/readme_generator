r"""
Command-line tool for generating README.md files from module docstrings in
Python packages.
"""

import ast
import sys
from pathlib import Path

import typer


app = typer.Typer(name="readme_generator")


def extract_docstring(file_path: Path) -> str:
    tree = ast.parse(file_path.read_text(), filename=str(file_path))
    return ast.get_docstring(tree) or ""


def generate_readme_content(directory: Path) -> str:
    init_file = directory / "__init__.py"

    readme_content = "<!-- Auto-generated file -->\n\n"
    readme_content += "# [`__init__.py`](__init__.py)\n\n"
    readme_content += extract_docstring(init_file) + "\n\n"

    children = sorted(directory.iterdir(), key=lambda p: p.name)
    for item in children:
        if item.is_dir() and (item / "__init__.py").is_file():
            readme_content += f"## [`{item.name}`]({item.name})\n\n"
            readme_content += extract_docstring(item / "__init__.py") + "\n\n"
    for item in children:
        if (
            item.is_file()
            and item.suffix == ".py"
            and item.name != "__init__.py"
        ):
            readme_content += f"## [`{item.name}`]({item.name})\n\n"
            readme_content += extract_docstring(item) + "\n\n"

    return readme_content


def process_directory(directory: Path, do_update: bool = True) -> bool:
    readme_content = generate_readme_content(directory)
    readme_file = directory / "README.md"

    if do_update:
        readme_file.write_text(readme_content, encoding="utf-8")
    else:
        # Checking if README.md matches generated content
        if (
            not readme_file.exists()
            or readme_file.read_text() != readme_content
        ):
            return False
    return True


@app.command()
def update(package_root: Path):
    if package_root.is_dir() and (package_root / "__init__.py").is_file():
        process_directory(package_root, do_update=True)
        for subdir in package_root.iterdir():
            update(subdir)


@app.command()
def check(package_root: Path):
    if package_root.is_dir() and (package_root / "__init__.py").is_file():
        if not process_directory(package_root, do_update=False):
            typer.echo(
                f"README.md in {package_root} is missing or out of date.",
                file=sys.stderr,
            )
            raise typer.Exit(code=1)
        for subdir in package_root.iterdir():
            check(subdir)


def cli() -> int:
    app()
    return 0


if __name__ == "__main__":
    exit(cli())
