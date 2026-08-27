# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Sphinx-Needs templates and the L+ report materializer.

Ordinary Need templates continue to be handled by Sphinx-Needs during the
read phase. L+ report declarations are collected as placeholders and their
graph-driven sections are inserted after parallel environments are merged.
"""

from pathlib import Path


def _needs_template_folder() -> Path:
    template_folder = Path(__file__).parents[2] / "needs_templates"
    if not template_folder.is_dir():
        raise FileNotFoundError(
            f"Sphinx-Needs template folder does not exist: {template_folder}"
        )
    return template_folder


def setup(app):  # type: ignore[no-untyped-def]
    from src.helper_lib import config_setdefault

    app.setup_extension("sphinx_needs")
    config_setdefault(
        app.config, "needs_template_folder", str(_needs_template_folder())
    )
    from .lplus import setup_lplus

    setup_lplus(app)
    return {
        "version": "3.0.0",
        "env_version": 300,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
