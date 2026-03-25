# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
import os
from collections.abc import Callable, Generator
from contextlib import suppress
from pathlib import Path

import pytest
from score_any_folder import _extract_mapping_from_conf
from sphinx.testing.util import SphinxTestApp


def _make_app(srcdir: Path, outdir: Path) -> SphinxTestApp:
    original_cwd = None
    with suppress(FileNotFoundError):
        original_cwd = os.getcwd()
    os.chdir(srcdir)
    try:
        return SphinxTestApp(
            freshenv=True,
            srcdir=srcdir,
            confdir=srcdir,
            outdir=outdir,
            buildername="html",
        )
    finally:
        if original_cwd is not None:
            with suppress(FileNotFoundError, OSError):
                os.chdir(original_cwd)


@pytest.fixture
def docs_dir(tmp_path: Path) -> Path:
    d = tmp_path / "docs"
    d.mkdir()
    return d


@pytest.fixture
def make_sphinx_app(
    docs_dir: Path, tmp_path: Path
) -> Generator[Callable[[dict[str, str]], SphinxTestApp], None, None]:
    """Factory: writes conf + index, returns a SphinxTestApp, cleans up on teardown."""
    apps: list[SphinxTestApp] = []

    def _factory(mapping: dict[str, str]) -> SphinxTestApp:
        (docs_dir / "conf.py").write_text(
            'extensions = ["score_any_folder"]\n'
            f"score_any_folder_mapping = {mapping!r}\n"
        )
        (docs_dir / "index.rst").write_text("Root\n====\n")
        app = _make_app(docs_dir, tmp_path / "out")
        apps.append(app)
        return app

    yield _factory

    for app in apps:
        app.cleanup()


# ---------------------------------------------------------------------------
# _extract_mapping_from_conf
# ---------------------------------------------------------------------------


def test_extract_mapping_returns_dict(tmp_path: Path) -> None:
    conf = tmp_path / "conf.py"
    conf.write_text('score_any_folder_mapping = {"../src": "src"}\n')
    assert _extract_mapping_from_conf(conf) == {"../src": "src"}


def test_extract_mapping_missing_key_returns_empty(tmp_path: Path) -> None:
    conf = tmp_path / "conf.py"
    conf.write_text("project = 'test'\n")
    assert _extract_mapping_from_conf(conf) == {}


def test_extract_mapping_non_literal_value_returns_empty(tmp_path: Path) -> None:
    conf = tmp_path / "conf.py"
    conf.write_text("score_any_folder_mapping = dict(src='src')\n")
    assert _extract_mapping_from_conf(conf) == {}


def test_extract_mapping_syntax_error_returns_empty(tmp_path: Path) -> None:
    conf = tmp_path / "conf.py"
    conf.write_text("score_any_folder_mapping = {this is not valid python\n")
    assert _extract_mapping_from_conf(conf) == {}


def test_extract_mapping_multiple_assignments_returns_first(tmp_path: Path) -> None:
    conf = tmp_path / "conf.py"
    conf.write_text(
        'score_any_folder_mapping = {"../a": "a"}\n'
        'score_any_folder_mapping = {"../b": "b"}\n'
    )
    assert _extract_mapping_from_conf(conf) == {"../a": "a"}


# ---------------------------------------------------------------------------
# Primary symlink behaviour
# ---------------------------------------------------------------------------


def test_symlink_exposes_files_at_target_path(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """Files in the source directory are readable via the symlinked target path."""
    src_docs = tmp_path / "src" / "module_docs"
    src_docs.mkdir(parents=True)
    content = "Remote Page\n===========\n\nContent here.\n"
    (src_docs / "page.rst").write_text(content)

    make_sphinx_app({"../src/module_docs": "module"})

    assert (docs_dir / "module" / "page.rst").read_text() == content


def test_symlink_is_idempotent(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """Build cleanup removes temporary links and a second build still succeeds."""
    src_docs = tmp_path / "external"
    src_docs.mkdir()

    make_sphinx_app({"../external": "notes"}).build()
    link = docs_dir / "notes"
    assert not link.exists()

    make_sphinx_app({"../external": "notes"}).build()

    assert not link.exists()


def test_stale_symlink_is_replaced(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """A symlink pointing to a stale target is replaced with the correct one."""
    correct_src = tmp_path / "correct"
    correct_src.mkdir()
    wrong_target = tmp_path / "wrong"
    wrong_target.mkdir()
    (docs_dir / "module").symlink_to(wrong_target)

    make_sphinx_app({"../correct": "module"})

    assert (docs_dir / "module").resolve() == correct_src.resolve()


def test_existing_non_symlink_logs_error_and_skips(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """A real directory at the target path is left untouched and an error is logged."""
    (tmp_path / "external").mkdir()
    real_dir = docs_dir / "module"
    real_dir.mkdir()

    app: SphinxTestApp = make_sphinx_app({"../external": "module"})

    assert real_dir.is_dir() and not real_dir.is_symlink()
    assert "not a symlink" in app.warning.getvalue()


def test_empty_mapping_is_a_no_op(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp], docs_dir: Path
) -> None:
    """An empty mapping produces no symlinks and no errors."""
    make_sphinx_app({}).build()

    assert [p for p in docs_dir.iterdir() if p.is_symlink()] == []


def test_multiple_mappings(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """Multiple mapping entries each produce their own symlink."""
    for name in ("alpha", "beta"):
        (tmp_path / name).mkdir()

    make_sphinx_app({"../alpha": "alpha", "../beta": "beta"})

    for name in ("alpha", "beta"):
        link = docs_dir / name
        assert link.is_symlink(), f"symlink for {name!r} was not created"
        assert link.resolve() == (tmp_path / name).resolve()


def test_target_in_subfolder(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """A target path with intermediate directories creates the parent dirs."""
    src_docs = tmp_path / "external"
    src_docs.mkdir()

    make_sphinx_app({"../external": "foo/other"})

    link = docs_dir / "foo" / "other"
    assert link.is_symlink()
    assert link.resolve() == src_docs.resolve()


# ---------------------------------------------------------------------------
# Auto-discovery of module conf.py files (combo build support)
# ---------------------------------------------------------------------------


def test_autodiscovery_applies_module_mapping(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """A conf.py found in a subdirectory has its mapping applied automatically."""
    # Simulate a sphinx_collections mount at docs/_collections/module/
    module_docs = docs_dir / "_collections" / "module"
    module_docs.mkdir(parents=True)
    containers = tmp_path / "module_repo" / "containers" / "docs"
    containers.mkdir(parents=True)
    (containers / "page.rst").write_text("Container Page\n==============\n")
    (module_docs / "conf.py").write_text(
        'score_any_folder_mapping = {"../../../module_repo/containers/docs":'
        ' "component/containers"}\n'
    )

    make_sphinx_app({})

    link = module_docs / "component" / "containers"
    assert link.is_symlink()
    assert link.resolve() == containers.resolve()
    assert (link / "page.rst").read_text() == "Container Page\n==============\n"


def test_autodiscovery_cleans_up_secondary_symlinks(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """Secondary symlinks from auto-discovered modules are removed on build-finished."""
    module_docs = docs_dir / "_collections" / "module"
    module_docs.mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    (module_docs / "conf.py").write_text(
        'score_any_folder_mapping = {"../../../external": "ext"}\n'
    )

    make_sphinx_app({}).build()

    assert not (module_docs / "ext").exists()


def test_autodiscovery_ignores_conf_without_mapping(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
) -> None:
    """A subdirectory conf.py with no score_any_folder_mapping produces no symlinks."""
    module_docs = docs_dir / "_collections" / "module"
    module_docs.mkdir(parents=True)
    (module_docs / "conf.py").write_text("project = 'test'\n")

    make_sphinx_app({}).build()

    assert [p for p in module_docs.iterdir() if p.is_symlink()] == []


def test_autodiscovery_nested_conf(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """Auto-discovery works for conf.py files nested more than one level deep."""
    nested_docs = docs_dir / "_collections" / "org" / "module" / "docs"
    nested_docs.mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    (nested_docs / "conf.py").write_text(
        'score_any_folder_mapping = {"../../../../../external": "ext"}\n'
    )

    make_sphinx_app({})

    assert (nested_docs / "ext").is_symlink()
    assert (nested_docs / "ext").resolve() == external.resolve()
