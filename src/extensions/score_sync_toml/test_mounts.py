# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
from pathlib import Path
from typing import Any, cast

import pytest
from sphinx.application import Sphinx

from src.extensions import score_sync_toml
from src.extensions.score_sync_toml import _mounts
from src.extensions.score_sync_toml._mounts import materialize_mounts


def test_materialize_mounts_serializes_structured_entries():
    fragment = materialize_mounts(
        [
            {
                "dir": 'docs/with "quotes"',
                "mount_at": "guide",
                "attach_to": "index",
                "entry_doc": "start",
            }
        ]
    )

    assert fragment is not None
    assert fragment.read_text(encoding="utf-8") == (
        "[[mounts]]\n"
        'dir = "docs/with \\"quotes\\""\n'
        'mount_at = "guide"\n'
        'attach_to = "index"\n'
        'entry_doc = "start"\n'
    )


def test_materialize_mounts_omits_default_fields():
    fragment = materialize_mounts(
        [{"dir": "docs", "mount_at": "guide", "attach_to": None, "entry_doc": "index"}]
    )

    assert fragment is not None
    assert (
        fragment.read_text(encoding="utf-8")
        == '[[mounts]]\ndir = "docs"\nmount_at = "guide"\n'
    )


def test_materialize_mounts_maps_external_runfiles_path_to_bazel_bin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runfiles_dir = tmp_path / "runfiles"
    walk_dir = runfiles_dir / "score_process_description+" / "process"
    walk_dir.mkdir(parents=True)
    monkeypatch.setattr(_mounts, "find_git_root", lambda: None)
    monkeypatch.setattr(_mounts, "get_runfiles_dir", lambda: runfiles_dir)

    fragment = materialize_mounts(
        [
            {
                "dir": str(walk_dir),
                "mount_at": "process",
            }
        ]
    )

    assert fragment is not None
    assert fragment.read_text(encoding="utf-8") == (
        '[[mounts]]\ndir = "bazel-bin/external/score_process_description+/process"\nmount_at = "process"\n'
    )


def test_materialize_mounts_preserves_explicit_source_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Serialize explicit mounts as files instead of widening them to dirs."""
    git_root = tmp_path / "workspace"
    git_root.mkdir()
    monkeypatch.setattr(_mounts, "find_git_root", lambda: git_root)

    fragment = materialize_mounts(
        [
            {
                "files": [
                    str(git_root / "generated" / "index.rst"),
                    str(git_root / "generated" / "guide.rst"),
                ],
                "mount_at": "generated",
            }
        ]
    )

    assert fragment is not None
    assert fragment.read_text(encoding="utf-8") == (
        "[[mounts]]\n"
        'files = ["generated/index.rst", "generated/guide.rst"]\n'
        'mount_at = "generated"\n'
    )


def test_materialize_mounts_keeps_bazel_bin_path_before_resolving_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep generated file mounts workspace-relative despite output symlinks."""
    git_root = tmp_path / "workspace"
    git_root.mkdir()
    canonical_file = tmp_path / "bazel-cache" / "generated" / "index.rst"
    canonical_file.parent.mkdir(parents=True)
    canonical_file.write_text("Generated", encoding="utf-8")
    bazel_file = git_root / "bazel-bin" / "pkg" / "index.rst"
    bazel_file.parent.mkdir(parents=True)
    bazel_file.symlink_to(canonical_file)
    monkeypatch.setattr(_mounts, "find_git_root", lambda: git_root)

    fragment = materialize_mounts(
        [{"files": [str(bazel_file)], "mount_at": "generated"}]
    )

    assert fragment is not None
    assert fragment.read_text(encoding="utf-8") == (
        '[[mounts]]\nfiles = ["bazel-bin/pkg/index.rst"]\nmount_at = "generated"\n'
    )


def test_materialize_mounts_maps_external_runfile_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep external file mounts in their stable bazel-bin spelling."""
    git_root = tmp_path / "workspace"
    runfiles_dir = git_root / "bazel-bin" / "docs.runfiles"
    external_file = runfiles_dir / "external_repo+" / "docs" / "index.rst"
    external_file.parent.mkdir(parents=True)
    canonical_file = tmp_path / "repository-cache" / "external_repo+" / "index.rst"
    canonical_file.parent.mkdir(parents=True)
    canonical_file.write_text("External", encoding="utf-8")
    external_file.symlink_to(canonical_file)
    monkeypatch.setattr(_mounts, "find_git_root", lambda: git_root)
    monkeypatch.setattr(_mounts, "get_runfiles_dir", lambda: runfiles_dir)

    fragment = materialize_mounts(
        [{"files": [str(external_file)], "mount_at": "external"}]
    )

    assert fragment is not None
    assert fragment.read_text(encoding="utf-8") == (
        "[[mounts]]\n"
        'files = ["bazel-bin/external/external_repo+/docs/index.rst"]\n'
        'mount_at = "external"\n'
    )


def test_setup_skips_toml_sync_without_git_worktree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ConfigWithoutTomlSync:
        suppress_warnings: list[str] = []

        @property
        def _raw_config(self) -> Any:
            raise AssertionError(
                "setup must not configure TOML sync without a Git worktree"
            )

    class AppWithoutGitWorktree:
        config = ConfigWithoutTomlSync()

        def connect(self, *args: Any, **kwargs: Any) -> None:
            raise AssertionError(
                "setup must not register TOML sync without a Git worktree"
            )

    monkeypatch.setattr(score_sync_toml, "find_git_root", lambda: None)

    metadata = score_sync_toml.setup(cast(Sphinx, AppWithoutGitWorktree()))

    assert metadata == {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
    assert AppWithoutGitWorktree.config.suppress_warnings == [
        "needs_config_writer.unsupported_type",
        "needs_config_writer.path_conversion",
    ]
