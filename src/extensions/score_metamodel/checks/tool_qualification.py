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
"""Validation for the structured SCORE tool-management workflow.

The metamodel declares the data shape.  This module validates the conditional
meaning of that data and derives the TVR safety/TCL values from the owned
use-case and malfunction graph.
"""

from collections.abc import Iterable
from typing import Any, cast

from score_metamodel import CheckLogger, graph_check, local_check
from sphinx.application import Sphinx
from sphinx_needs.data import NeedsView
from sphinx_needs.need_item import NeedItem


def _link_values(need: NeedItem, link_name: str) -> list[str]:
    """Return an outgoing link field as plain IDs."""
    try:
        link_values = cast(list[str], need.get_links(link_name, as_str=True))
        return [str(item) for item in link_values]
    except KeyError:
        # The unit-test NeedItem helper exposes link fields through get(), while
        # collected Sphinx-Needs items expose them through get_links.
        pass
    value = need.get(link_name, [])
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in cast(list[Any], value)]
    return [str(value)]


def _base_id(need_id: str) -> str:
    """Remove an optional Sphinx-Needs version filter from a link ID."""
    return need_id.split("[", 1)[0]


def _need_index(needs: Iterable[NeedItem]) -> dict[str, NeedItem]:
    """Index Needs by both their exact and unqualified IDs."""
    index: dict[str, NeedItem] = {}
    for need in needs:
        index[need["id"]] = need
        index.setdefault(_base_id(need["id"]), need)
    return index


def _linked_targets(
    source: NeedItem, link_name: str, index: dict[str, NeedItem]
) -> list[NeedItem]:
    """Resolve outgoing links from a Need, ignoring unknown targets."""
    targets: list[NeedItem] = []
    for target_id in _link_values(source, link_name):
        target = index.get(target_id) or index.get(_base_id(target_id))
        if target is not None:
            targets.append(target)
    return targets


def _owned_usecases(
    doc_tool: NeedItem, all_needs: Iterable[NeedItem]
) -> list[NeedItem]:
    """Return use cases explicitly owned by a Tool Verification Report."""
    return [
        need
        for need in all_needs
        if need["type"] == "tool_usecase"
        and doc_tool["id"]
        in {_base_id(link) for link in _link_values(need, "belongs_to")}
    ]


def _malfunctions_for_usecase(
    usecase: NeedItem, all_needs: Iterable[NeedItem]
) -> list[NeedItem]:
    """Return malfunctions whose explicit parent is the given use case."""
    usecase_id = _base_id(usecase["id"])
    return [
        need
        for need in all_needs
        if need["type"] == "potential_tool_malfunction"
        and usecase_id
        in {_base_id(link) for link in _link_values(need, "parent_needs")}
    ]


def _malfunctions_for_report(
    doc_tool: NeedItem, all_needs: Iterable[NeedItem]
) -> list[NeedItem]:
    """Return all malfunctions belonging to a Tool Verification Report."""
    usecases = _owned_usecases(doc_tool, all_needs)
    found: list[NeedItem] = []
    found_ids: set[str] = set()
    for usecase in usecases:
        for malfunction in _malfunctions_for_usecase(usecase, all_needs):
            if malfunction["id"] not in found_ids:
                found.append(malfunction)
                found_ids.add(malfunction["id"])
    return found


def _is_present(value: Any) -> bool:
    """Treat non-empty strings and non-empty collections as present."""
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def derive_tvr_values(malfunctions: Iterable[NeedItem]) -> tuple[str, str]:
    """Derive TVR safety relevance and TCL from malfunction evaluations."""
    malfunction_list = list(malfunctions)
    safety_affected = (
        "YES"
        if any(need.get("safety_affected") == "YES" for need in malfunction_list)
        else "NO"
    )
    tcl = (
        "LOW"
        if any(
            need.get("safety_affected") == "YES"
            and need.get("detection_sufficient") == "NO"
            for need in malfunction_list
        )
        else "HIGH"
    )
    return safety_affected, tcl


def _qualification_requirements(
    malfunctions: Iterable[NeedItem], index: dict[str, NeedItem]
) -> list[NeedItem]:
    """Return unique tool requirements violated by LOW-confidence malfunctions."""
    requirements: list[NeedItem] = []
    requirement_ids: set[str] = set()
    for malfunction in malfunctions:
        if not (
            malfunction.get("safety_affected") == "YES"
            and malfunction.get("detection_sufficient") == "NO"
        ):
            continue
        for requirement in _linked_targets(malfunction, "violates", index):
            if (
                requirement["type"] == "tool_req"
                and requirement["id"] not in requirement_ids
            ):
                requirements.append(requirement)
                requirement_ids.add(requirement["id"])
    return requirements


def _successful_full_testcase(
    requirement: NeedItem, all_needs: Iterable[NeedItem]
) -> bool:
    """Return whether a passed testcase fully verifies the requirement.

    Existing SCORE coverage distinguishes full and partial verification.  A
    qualification claim needs complete evidence for the tool requirement, so
    partial links alone do not satisfy this workflow check.
    """
    requirement_id = _base_id(requirement["id"])
    for testcase in all_needs:
        if testcase["type"] != "testcase" or testcase.get("result") != "passed":
            continue
        fully_verified = {
            _base_id(link) for link in _link_values(testcase, "fully_verifies")
        }
        if requirement_id in fully_verified:
            return True
    return False


def _check_low_malfunction_links(
    needs: Iterable[NeedItem], index: dict[str, NeedItem], log: CheckLogger
) -> None:
    """Require qualification targets for every LOW-confidence malfunction."""
    for malfunction in (
        need for need in needs if need["type"] == "potential_tool_malfunction"
    ):
        is_low = (
            malfunction.get("safety_affected") == "YES"
            and malfunction.get("detection_sufficient") == "NO"
        )
        if not is_low:
            continue

        has_tool_requirement = any(
            target["type"] == "tool_req"
            for target in _linked_targets(malfunction, "violates", index)
        )
        if not has_tool_requirement:
            log.warning_for_need(
                malfunction,
                "LOW-confidence malfunctions must violate at least one `tool_req` "
                "so that qualification evidence can be produced.",
                category="tool-qualification",
            )


def _validate_report_values(
    doc_tool: NeedItem,
    malfunctions: list[NeedItem],
    log: CheckLogger,
) -> str:
    """Validate the stored TVR summary against its owned malfunctions."""
    expected_safety, expected_tcl = derive_tvr_values(malfunctions)
    if doc_tool.get("safety_affected") != expected_safety:
        log.warning_for_need(
            doc_tool,
            f"`safety_affected` is {doc_tool.get('safety_affected')!r}, but "
            f"the owned malfunction graph derives {expected_safety!r}.",
            category="tool-qualification",
        )
    if doc_tool.get("tcl") != expected_tcl:
        log.warning_for_need(
            doc_tool,
            f"`tcl` is {doc_tool.get('tcl')!r}, but the owned malfunction "
            f"graph derives {expected_tcl!r}.",
            category="tool-qualification",
        )
    return expected_tcl


def _validate_report_status(
    doc_tool: NeedItem,
    status: Any,
    expected_tcl: str,
    malfunctions: list[NeedItem],
    index: dict[str, NeedItem],
    needs: list[NeedItem],
    log: CheckLogger,
) -> None:
    """Validate qualification and release requirements for a TVR status."""
    if status not in ("qualified", "released"):
        return
    if status == "qualified" and expected_tcl != "LOW":
        log.warning_for_need(
            doc_tool,
            f"`status: {status}` is only valid for a TVR with `tcl: LOW`; "
            "HIGH-confidence reports do not require qualification.",
            category="tool-qualification",
        )
        return
    if expected_tcl != "LOW":
        # A HIGH-confidence report can progress directly from evaluated to
        # released. Qualification is only a workflow state for LOW TCL.
        return

    requirements = _qualification_requirements(malfunctions, index)
    for requirement in requirements:
        if _successful_full_testcase(requirement, needs):
            continue
        log.warning_for_need(
            doc_tool,
            f"qualification evidence is incomplete: `{requirement['id']}` "
            "needs a passed testcase with a `fully_verifies` link.",
            category="tool-qualification",
        )


@local_check
def check_tool_malfunction_evaluation(
    _: Sphinx, need: NeedItem, log: CheckLogger
) -> None:
    """Validate conditional malfunction options.

    Detection is only meaningful for a safety-relevant malfunction.  For a
    safety-relevant malfunction, a positive detection claim also needs the
    free-text safety measure that explains what detects or prevents it.
    """
    if need["type"] != "potential_tool_malfunction":
        return

    safety_affected = need.get("safety_affected")
    detection_sufficient = need.get("detection_sufficient")
    safety_measures = need.get("safety_measures")

    if safety_affected == "YES" and detection_sufficient not in ("YES", "NO"):
        log.warning_for_need(
            need,
            "safety-relevant malfunctions must define `detection_sufficient` "
            "as YES or NO.",
            category="tool-qualification",
        )
    elif (
        safety_affected == "YES"
        and detection_sufficient == "YES"
        and not _is_present(safety_measures)
    ):
        log.warning_for_need(
            need,
            "`detection_sufficient: YES` requires a non-empty `safety_measures` value.",
            category="tool-qualification",
        )
    elif safety_affected == "NO" and _is_present(detection_sufficient):
        log.warning_for_need(
            need,
            "non-safety malfunctions must not define `detection_sufficient`.",
            category="tool-qualification",
        )


@graph_check
def check_tool_qualification_workflow(
    _: Sphinx, all_needs: NeedsView, log: CheckLogger
) -> None:
    """Validate ownership, qualification prerequisites, and TVR workflow states."""
    needs = list(all_needs.values())
    index = _need_index(needs)

    _check_low_malfunction_links(needs, index, log)

    for doc_tool in (need for need in needs if need["type"] == "doc_tool"):
        status = doc_tool.get("status")
        if status in ("draft", "rejected"):
            continue

        usecases = _owned_usecases(doc_tool, needs)
        if not usecases:
            # Existing SCORE repositories may still contain legacy doc_tool
            # reports whose requirements are modeled directly on the report.
            # The structured workflow is opt-in through its post-template; do
            # not make those reports fail merely because this extension now
            # knows about tool_usecase ownership.
            if not doc_tool.get("post_template"):
                continue
            log.warning_for_need(
                doc_tool,
                "non-draft Tool Verification Reports must own at least one "
                "`tool_usecase` through `belongs_to`.",
                category="tool-qualification",
            )
            continue

        malfunctions = _malfunctions_for_report(doc_tool, needs)
        expected_tcl = _validate_report_values(doc_tool, malfunctions, log)
        _validate_report_status(
            doc_tool,
            status,
            expected_tcl,
            malfunctions,
            index,
            needs,
            log,
        )
