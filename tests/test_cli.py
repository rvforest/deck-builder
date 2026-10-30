import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from deck_builder.cli import app

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "rectangle.toml"
runner = CliRunner()


def test_validate_has_no_file_side_effects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["validate", str(EXAMPLE)])
    assert result.exit_code == 0, result.output
    assert "Valid deck:" in result.stdout
    assert not list(tmp_path.iterdir())


def test_cli_exports_example(tmp_path: Path) -> None:
    output = tmp_path / "build"
    result = subprocess.run(
        [sys.executable, "-m", "deck_builder", "export", str(EXAMPLE), "--output", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (output / "deck.scad").is_file()
    assert (output / "top.dxf").is_file()
    assert (output / "assembly.json").is_file()


@pytest.mark.parametrize(
    "contents",
    [
        "[broken",
        '[deck.footprint]\ntype = "polygon"',
        '[deck.footprint]\nwidth = "144"\nlength = 192',
    ],
)
def test_invalid_config_does_not_create_output(
    tmp_path: Path,
    contents: str,
) -> None:
    config = tmp_path / "invalid.toml"
    config.write_text(contents)
    output = tmp_path / "output"
    result = runner.invoke(app, ["export", str(config), "--output", str(output)])
    assert result.exit_code == 2
    assert "deck-builder:" in result.stderr
    assert not output.exists()


def test_missing_config_is_a_clean_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", str(tmp_path / "missing.toml")])
    assert result.exit_code == 2
    assert "deck-builder:" in result.stderr


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.stdout
    assert "export" in result.stdout


def test_import_has_no_file_side_effects(tmp_path: Path) -> None:
    # Run outside the repository so incidental writes cannot be hidden by gitignore.
    result = subprocess.run(
        [sys.executable, "-c", "import deck_builder; import deck_builder.cli"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    assert result.returncode == 0, result.stderr
    assert not list(tmp_path.iterdir())
