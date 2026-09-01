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
"""Tests for the primary-source filtering helpers."""

from pathlib import Path

from src.extensions.score_mounts import _unowned_source_paths


def test_unowned_source_paths_only_returns_unselected_documents(
    tmp_path: Path,
) -> None:
    """Nested package documents are found while assets are left available."""
    (tmp_path / "index.rst").write_text("Index", encoding="utf-8")
    (tmp_path / "nested.rst").write_text("Nested", encoding="utf-8")
    (tmp_path / "diagram.svg").write_text("<svg />", encoding="utf-8")

    assert _unowned_source_paths(
        tmp_path,
        selected_paths={"index.rst"},
        suffixes=(".rst", ".md"),
    ) == ["nested.rst"]
