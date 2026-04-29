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

"""Tests for generate_sourcelinks_cli.py"""

import json
import sys
from pathlib import Path

import pytest

import scripts_bazel.generate_sourcelinks_cli

_MY_PATH = Path(__file__).parent


def test_generate_sourcelinks_cli_basic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test basic functionality of generate_sourcelinks_cli."""
    # Create a test source file with a traceability tag
    test_file = tmp_path / "test_source.py"
    test_file.write_text(
        """
# Some code here
# req-Id: tool_req__docs_arch_types
def some_function():
    pass
"""
    )

    output_file = tmp_path / "output.json"

    # Execute the script
    monkeypatch.setattr(
        sys,
        "argv",
        [
            _MY_PATH.parent / "generate_sourcelinks_cli.py",
            "--output",
            str(output_file),
            str(test_file),
        ],
    )
    result = scripts_bazel.generate_sourcelinks_cli.main()

    assert result == 0
    assert output_file.exists()

    # Check the output content
    with open(output_file) as f:
        data: list[dict[str, str | int]] = json.load(f)
    assert isinstance(data, list)
    # First element is the metadata dict; there must be at least one need entry after it
    assert len(data) > 1

    # Verify schema of each need entry (skip the first metadata element)
    for entry in data[1:]:
        assert "file" in entry
        assert "line" in entry
        assert "tag" in entry
        assert "need" in entry
        assert "full_line" in entry

        # Verify types
        assert isinstance(entry["file"], str)
        assert isinstance(entry["line"], int)
        assert isinstance(entry["tag"], str)
        assert isinstance(entry["need"], str)
        assert isinstance(entry["full_line"], str)

    assert any(entry["need"] == "tool_req__docs_arch_types" for entry in data[1:])
