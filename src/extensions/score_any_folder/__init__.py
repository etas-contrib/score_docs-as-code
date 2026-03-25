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
"""Sphinx extension that creates symlinks from arbitrary locations into the
documentation source directory, allowing sphinx-build to include source
files that live outside ``docs/``.

Configuration in ``conf.py``::

    score_any_folder_mapping = {
        "../src/my_module/docs": "my_module",
    }

Each entry is a ``source: target`` pair where:

* ``source`` – path to the directory to expose, relative to ``confdir``
  (the directory containing ``conf.py``).
* ``target`` – path of the symlink to create, relative to ``confdir``.

The extension creates the symlinks on ``builder-inited``,
before Sphinx starts reading any documents.
Existing correct symlinks are left in place (idempotent);
a symlink pointing to the wrong target is replaced.

Symlinks created by this extension are removed again on ``build-finished``.
Misconfigured pairs (absolute paths, non-symlink path at the target location)
are logged as errors and skipped.

Combo builds
------------

When a combo build mounts external modules via ``sphinx_collections``,
those modules may have their own ``score_any_folder_mapping`` in their
``conf.py``.  This extension automatically discovers those files by scanning
``confdir`` subdirectories after the primary symlink pass and applies their
mappings with paths resolved relative to each module's directory.

No extra configuration is required.  The handler is registered at event
priority 600 (above the default 500) to ensure it runs after
``sphinx_collections`` has mounted its collections.
"""

import ast
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util.logging import getLogger

logger = getLogger(__name__)

_APP_ATTRIBUTE = "_score_any_folder_created_links"


def setup(app: Sphinx) -> dict[str, str | bool]:
    app.add_config_value("score_any_folder_mapping", default={}, rebuild="env")
    # Priority 600 > default 500: run after sphinx_collections has mounted modules.
    app.connect("builder-inited", _create_symlinks, priority=600)
    app.connect("build-finished", _cleanup_symlinks)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _extract_mapping_from_conf(conf_path: Path) -> dict[str, str]:
    """Safely extract ``score_any_folder_mapping`` from a ``conf.py`` file.

    Uses ``ast.literal_eval`` so no arbitrary code is executed.
    Returns an empty dict if the key is absent or cannot be parsed.
    """
    try:
        tree = ast.parse(conf_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "score_any_folder_mapping"
                ):
                    return ast.literal_eval(node.value)
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "score_any_folder: could not extract mapping from %s: %s",
            conf_path,
            exc,
        )
    return {}


def _symlink_pairs(confdir: Path, mapping: dict[str, str]) -> list[tuple[Path, Path]]:
    """Return ``(resolved_source, link_path)`` pairs from *mapping*.

    Entries with absolute paths are logged as errors and skipped.
    """
    pairs = []
    for source_rel, target_rel in mapping.items():
        if Path(source_rel).is_absolute():
            logger.error(
                "score_any_folder: source path must be relative, got: %r; skipping",
                source_rel,
            )
            continue
        if Path(target_rel).is_absolute():
            logger.error(
                "score_any_folder: target path must be relative, got: %r; skipping",
                target_rel,
            )
            continue
        source = (confdir / source_rel).resolve()
        link = confdir / target_rel
        pairs.append((source, link))
    return pairs


def _maybe_create_symlink(source: Path, link: Path, created_links: set[Path]) -> None:
    """Create a symlink at *link* pointing to *source*, if needed.

    Handles the idempotent / stale-symlink / existing-path cases and logs
    errors without raising.  Successfully created links are added to
    *created_links* for later cleanup.
    """
    if link.is_symlink():
        if link.resolve() == source:
            logger.debug("score_any_folder: symlink already correct: %s", link)
            return
        logger.info("score_any_folder: replacing stale symlink %s -> %s", link, source)
        link.unlink()
    elif link.exists():
        logger.error(
            "score_any_folder: target path already exists and is not a symlink: "
            "%s; skipping",
            link,
        )
        return

    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(source)
    except OSError as exc:
        logger.error(
            "score_any_folder: failed to create symlink %s -> %s: %s",
            link,
            source,
            exc,
        )
        return
    created_links.add(link)
    logger.debug("score_any_folder: created symlink %s -> %s", link, source)


def _create_symlinks(app: Sphinx) -> None:
    created_links: set[Path] = set()
    confdir = Path(app.confdir)

    # Primary pass — mappings defined in the main conf.py.
    for source, link in _symlink_pairs(confdir, app.config.score_any_folder_mapping):
        _maybe_create_symlink(source, link, created_links)

    # Secondary pass — auto-discover conf.py files in subdirectories.
    # Picks up modules mounted by sphinx_collections (or any other mechanism).
    # Running at priority 600 ensures sphinx_collections has already mounted
    # its collections before we scan.
    for conf_py in sorted(confdir.rglob("conf.py")):
        if conf_py.parent == confdir:
            continue  # skip the main conf.py
        module_mapping = _extract_mapping_from_conf(conf_py)
        if not module_mapping:
            continue
        for source, link in _symlink_pairs(conf_py.parent, module_mapping):
            _maybe_create_symlink(source, link, created_links)

    setattr(app, _APP_ATTRIBUTE, created_links)


def _cleanup_symlinks(app: Sphinx, exception: Exception | None) -> None:
    del exception

    created_links: set[Path] = getattr(app, _APP_ATTRIBUTE, set())
    for link in created_links:
        if not link.is_symlink():
            continue
        link.unlink()
        logger.debug("score_any_folder: removed temporary symlink %s", link)
