# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
"""Sphinx extension that rewrites materialized Bazel paths to original workspace paths.

Reads _sourcemap.json from app.srcdir on builder-inited.
No-op when the file is absent (direct Sphinx invocation without Bazel).
"""

import json
import logging
import os

from sphinx.application import Sphinx


class _SourceMapFilter(logging.Filter):
    """Rewrites materialized Bazel paths in Sphinx warning locations.

    Uses a prefix-based approach: strips the tree_root prefix from the
    location, looks up the remainder in the source map, and replaces
    with the workspace path.
    """

    def __init__(self, tree_root: str, rel_map: dict[str, str]) -> None:
        super().__init__()
        self._prefixes = self._build_prefixes(tree_root, rel_map)

    @staticmethod
    def _build_prefixes(
        tree_root: str, rel_map: dict[str, str]
    ) -> list[tuple[str, str]]:
        """Build (materialized_abs_path, workspace_relative_path) pairs."""
        result = []
        for rel_materialized, rel_original in rel_map.items():
            mat = os.path.join(tree_root, rel_materialized)
            result.append((mat, rel_original))
        result.sort(key=lambda p: len(p[0]), reverse=True)
        return result

    def filter(self, record: logging.LogRecord) -> bool:
        loc = getattr(record, "location", None)
        if isinstance(loc, str):
            for mat, orig in self._prefixes:
                if mat in loc:
                    record.location = loc.replace(mat, orig)
                    break
        return True


def _on_builder_inited(app: Sphinx) -> None:
    tree_root = str(os.path.dirname(app.srcdir))
    sourcemap_path = os.path.join(tree_root, "_sourcemap.json")
    if not os.path.isfile(sourcemap_path):
        return

    with open(sourcemap_path, encoding="utf-8") as f:
        rel_map: dict[str, str] = json.load(f)

    real_tree_root = os.path.realpath(tree_root)

    sphinx_filter = _SourceMapFilter(tree_root, rel_map)

    # Append to each handler's filter chain so our rewrite runs after Sphinx's
    # WarningLogRecordTranslator, which converts node/tuple locations to strings.
    for handler in logging.getLogger("sphinx").handlers:
        handler.addFilter(sphinx_filter)
        # Also handle the realpath variant for Sphinx code paths that resolve symlinks.
        if real_tree_root != tree_root:
            handler.addFilter(_SourceMapFilter(real_tree_root, rel_map))


def setup(app: Sphinx) -> dict[str, object]:
    app.connect("builder-inited", _on_builder_inited)
    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
