from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
TEXT_SUFFIXES = {".html", ".md", ".py", ".toml", ".csv", ".js", ".mjs", ".txt"}


def tracked_text_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    return [REPO_ROOT / path for path in output.splitlines() if (REPO_ROOT / path).suffix in TEXT_SUFFIXES]


def test_tracked_text_files_do_not_contain_merge_conflict_markers():
    offenders: list[str] = []
    for path in tracked_text_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        if any(line.startswith(CONFLICT_MARKERS) for line in lines):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []


def test_web_page_embedded_javascript_has_valid_syntax(tmp_path: Path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not available to validate embedded JavaScript syntax.")

    html = (REPO_ROOT / "web" / "index.html").read_text(encoding="utf-8")
    script = html.split("<script>", 1)[1].split("</script>", 1)[0]
    script_file = tmp_path / "capacity_web_script.js"
    script_file.write_text(script, encoding="utf-8")

    subprocess.run([node, "--check", str(script_file)], check=True, cwd=REPO_ROOT)
