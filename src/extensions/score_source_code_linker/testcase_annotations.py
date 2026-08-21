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
"""Decorate rendered GitHub testcase links with their execution result.

Testcase needs are external needs. Their ``external_url`` is therefore also
the URL used by the ``testlink`` metadata rendered on requirements. The same
URL is used for incoming ``fully_verified_by``/``partially_verified_by`` links.
This hook matches both forms to the testcase need and appends a coloured result
annotation to the rendered reference.
"""

from __future__ import annotations

from html import escape
from typing import Any

from docutils import nodes
from sphinx_needs.data import SphinxNeedsData

# Use a consistent colour for each common testcase result.
RESULT_COLORS = {
    "passed": "#37a12d",
    "failed": "#ca2828",
    "skipped": "#f0a500",
    "disabled": "#888888",
}
_FALLBACK_COLOR = "#666666"
_ANNOTATED_ATTR = "score_source_code_linker_testcase_result_annotated"


def _resolved_target_need_id(ref: nodes.reference) -> str | None:
    """Return the need ID a resolved reference points to, if available."""
    refid = ref.get("refid")
    if refid:
        return refid

    refuri = ref.get("refuri")
    if refuri and "#" in refuri:
        return refuri.rsplit("#", 1)[-1]

    return None


def _testcases_by_external_url(needs: Any) -> dict[str, dict[str, Any]]:
    """Index testcase needs by the URL used for their rendered GitHub link."""
    return {
        external_url: need
        for need in needs.values()
        if need.get("type") == "testcase" and (external_url := need.get("external_url"))
    }


def _testcase_for_reference(
    ref: nodes.reference,
    needs: Any,
    testcases_by_url: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Resolve a reference either by need ID or by its external GitHub URL."""
    target_id = _resolved_target_need_id(ref)
    if target_id:
        target_need = needs.get(target_id)
        if target_need is not None and target_need.get("type") == "testcase":
            return target_need

    refuri = ref.get("refuri")
    if refuri:
        return testcases_by_url.get(refuri)

    return None


def annotate_testcase_results(app, doctree, docname):
    """Append a coloured result annotation to rendered testcase references.

    The handler runs after sphinx-needs' own ``doctree-resolved`` handlers.
    It therefore sees both regular resolved references and the external
    references generated for GitHub ``testlink`` metadata.
    """
    needs = SphinxNeedsData(app.env).get_needs_view()
    testcases_by_url = _testcases_by_external_url(needs)

    for ref in list(doctree.findall(nodes.reference)):
        if ref.get(_ANNOTATED_ATTR):
            continue

        testneed = _testcase_for_reference(ref, needs, testcases_by_url)
        if testneed is None:
            continue

        result = testneed.get("result")
        if not result:
            # A missing result is not a status and must not render as ``()``.
            continue

        result_text = str(result)
        color = RESULT_COLORS.get(result_text, _FALLBACK_COLOR)
        status_html = (
            f'<span style="color:{color};font-weight:bold"> '
            f"({escape(result_text, quote=True)})</span>"
        )
        ref.append(nodes.raw("", status_html, format="html"))
        ref[_ANNOTATED_ATTR] = True
