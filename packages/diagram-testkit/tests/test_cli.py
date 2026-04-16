import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "diagram_testkit", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_lint_bad_fixture_exits_1():
    bad_svgs = list(FIXTURES_DIR.glob("architecture-arrow-*.svg"))
    assert bad_svgs, "No arrow-crossing fixture found"
    result = _run_cli("lint", str(bad_svgs[0]))
    assert result.returncode == 1
    assert "FAIL" in result.stdout


def test_cli_lint_matplotlib_fixture_exits_1():
    mpl_svgs = list(FIXTURES_DIR.glob("matplotlib-*.svg"))
    assert mpl_svgs
    result = _run_cli("lint", str(mpl_svgs[0]))
    assert result.returncode == 1
    assert "FAIL" in result.stdout


def test_cli_lint_format_override():
    svgs = list(FIXTURES_DIR.glob("architecture-*.svg"))
    assert svgs
    result = _run_cli("lint", "--format", "graphviz", str(svgs[0]))
    assert result.returncode in (0, 1)


def test_cli_lint_nonexistent_file_exits_1():
    result = _run_cli("lint", "/nonexistent/file.svg")
    assert result.returncode == 1
    assert "File not found" in result.stdout


def test_cli_no_command_exits_1():
    result = _run_cli()
    assert result.returncode == 1


def test_cli_lint_chart_labels_overlap():
    fixture = FIXTURES_DIR / "svgwrite-chart-labels-overlap.svg"
    assert fixture.exists()
    result = _run_cli("lint", str(fixture))
    assert result.returncode == 1
    assert "Text overlap" in result.stdout
    assert "99% VaR" in result.stdout


def test_cli_lint_runs_file_based_checks():
    """Verify CLI runs file-based checks (text_overflows_rect, line_crosses_text)."""
    fixture = FIXTURES_DIR / "svgwrite-text-overflows-rect.svg"
    assert fixture.exists()
    result = _run_cli("lint", str(fixture))
    assert result.returncode == 1
    assert "overflows" in result.stdout
