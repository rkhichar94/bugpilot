import tempfile
from pathlib import Path

import pytest

from tools.repo_tools import list_files, read_file, search_in_files, write_file


@pytest.fixture
def tmp_repo(tmp_path):
    (tmp_path / "src" / "main" / "java").mkdir(parents=True)
    (tmp_path / "src" / "main" / "java" / "App.java").write_text(
        "public class App {\n    public static void main(String[] args) {}\n}\n"
    )
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]\n")
    return str(tmp_path)


def test_read_file(tmp_repo):
    content = read_file(tmp_repo, "src/main/java/App.java")
    assert "public class App" in content


def test_read_file_missing(tmp_repo):
    result = read_file(tmp_repo, "does/not/exist.java")
    assert "ERROR" in result


def test_write_file(tmp_repo):
    result = write_file(tmp_repo, "src/Foo.java", "public class Foo {}")
    assert "OK" in result
    assert Path(tmp_repo, "src", "Foo.java").read_text() == "public class Foo {}"


def test_write_file_creates_dirs(tmp_repo):
    write_file(tmp_repo, "new/deep/Dir.java", "class Dir {}")
    assert Path(tmp_repo, "new", "deep", "Dir.java").exists()


def test_list_files_all(tmp_repo):
    files = list_files(tmp_repo)
    java_files = [f for f in files if f.endswith(".java")]
    assert len(java_files) >= 1
    # .git internals should not appear
    assert all(".git" not in f for f in files)


def test_list_files_extension(tmp_repo):
    files = list_files(tmp_repo, extension=".java")
    assert all(f.endswith(".java") for f in files)


def test_search_in_files(tmp_repo):
    results = search_in_files(tmp_repo, "public class")
    assert any("App.java" in r for r in results)


def test_search_in_files_no_match(tmp_repo):
    results = search_in_files(tmp_repo, "zzz_no_match_zzz")
    assert results == []
