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
import subprocess
import sys
from pathlib import Path


def test_generate_sourcelinks_cli_basic(tmp_path: Path) -> None:
    """Test basic functionality of generate_sourcelinks_cli."""
    # Create a test source file with a traceability tag
    test_file = tmp_path / "test_source.py"
    test_file.write_text(
        """
# Some code here
# score:req:REQ_001
def some_function():
    pass
"""
    )

    output_file = tmp_path / "output.json"

    # Execute the script
    result = subprocess.run(
        [
            sys.executable,
            "scripts/generate_sourcelinks_cli.py",
            "--output",
            str(output_file),
            str(test_file),
        ],
        cwd="/home/zwa2lr/git/score/docs-as-code",
    )

    assert result.returncode == 0
    assert output_file.exists()

    # Check the output content
    with open(output_file) as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0

    # Verify schema of each entry
    for entry in data:
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

    # Verify specific content for our test case
    assert any(entry["need"] == "REQ_001" for entry in data)
    assert any("score:req:REQ_001" in entry["tag"] for entry in data)
