# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Serialize Bazel-derived mount metadata for ``needs-config-writer``."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from sphinx.config import Config

from src.helper_lib import find_git_root, get_runfiles_dir


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _relative_path(path: Path, root: Path) -> str | None:
    """Return a lexical path relative to ``root`` when it is below that root."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return None


def _git_toml_path(path: Path, git_root: Path | None) -> str | None:
    """Map a workspace path while leaving nested runfiles for special handling."""
    if git_root is None:
        return None
    relative_path = _relative_path(path, git_root)
    if relative_path is None:
        return None
    # A runfiles tree may itself live below the workspace. Let its dedicated
    # conversion preserve the stable bazel-bin/external spelling instead.
    if any(part.endswith(".runfiles") for part in Path(relative_path).parts):
        return None
    return relative_path


def _runfiles_toml_path(path: Path, runfiles_dir: Path) -> str | None:
    """Map a lexical runfiles path to the stable TOML spelling."""
    relative_path = _relative_path(path, runfiles_dir)
    if relative_path is None:
        return None
    relative_parts = Path(relative_path).parts
    if relative_parts and relative_parts[0] == "_main":
        return str(Path(*relative_parts[1:]))
    return "bazel-bin/external/" + relative_path


def _toml_path(path: Path) -> str:
    """Derive a stable TOML path without following Bazel runfile symlinks."""
    # ``bazel-bin`` and external runfiles are often symlinks into Bazel's
    # output or repository cache. Keep the lexical path first so the generated
    # TOML remains portable across machines and Bazel invocations.
    lexical_path = path.absolute()
    git_root = find_git_root()
    lexical_git_path = _git_toml_path(lexical_path, git_root)
    if lexical_git_path is not None:
        return lexical_git_path

    runfiles_dir = get_runfiles_dir()
    lexical_runfiles_path = _runfiles_toml_path(lexical_path, runfiles_dir)
    if lexical_runfiles_path is not None:
        return lexical_runfiles_path

    # Existing canonical mount entries may already contain a resolved path.
    # Retain the previous fallback behavior for those callers.
    resolved_path = path.resolve()
    resolved_git_path = _relative_path(resolved_path, git_root) if git_root else None
    if resolved_git_path is not None:
        return resolved_git_path
    resolved_runfiles_path = _runfiles_toml_path(resolved_path, runfiles_dir)
    if resolved_runfiles_path is not None:
        return resolved_runfiles_path
    return str(resolved_path)


def _toml_dir(entry: dict[str, Any]) -> str:
    """Derive a stable TOML directory from a resolved mount entry."""
    return _toml_path(Path(entry["dir"]))


def materialize_mounts(entries: list[dict[str, Any]]) -> Path | None:
    """Write resolved mounts as a temporary, Git-root-relative TOML merge file."""
    if not entries:
        return None
    lines: list[str] = []
    for entry in entries:
        source_files = entry.get("files", [])
        lines.extend(
            [
                "[[mounts]]",
            ]
        )
        if source_files:
            # Preserve explicit source mounts as a file allowlist in the
            # generated TOML instead of widening them back to a directory.
            files = ", ".join(
                _toml_string(_toml_path(Path(source_file)))
                for source_file in source_files
            )
            lines.append(f"files = [{files}]")
        else:
            lines.append(f"dir = {_toml_string(_toml_dir(entry))}")
        lines.append(f"mount_at = {_toml_string(entry['mount_at'])}")
        if entry.get("attach_to"):
            lines.append(f"attach_to = {_toml_string(entry['attach_to'])}")
        if entry.get("entry_doc", "index") != "index":
            lines.append(f"entry_doc = {_toml_string(entry['entry_doc'])}")
        lines.append("")
    outdir = Path(tempfile.mkdtemp(prefix="score_sync_toml_"))
    fragment = outdir / "score_mounts.toml"
    fragment.write_text("\n".join(lines), encoding="utf-8")
    return fragment


def register_mounts(config: Config) -> None:
    """Merge configured mount entries into the generated ``ubproject.toml``."""
    fragment = materialize_mounts(config.mounts)
    if fragment is not None:
        config.needscfg_merge_toml_files.append(str(fragment))
