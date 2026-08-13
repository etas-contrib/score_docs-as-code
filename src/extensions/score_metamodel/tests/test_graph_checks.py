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

from __future__ import annotations

from typing import Any

import pytest

# Adjust this import path if your project layout differs.
import score_metamodel.checks.graph_checks as graph_checks
from score_metamodel.tests import fake_check_logger, need as test_need
from sphinx_needs.config import NeedType
from sphinx_needs.need_item import NeedItem, NeedLink


class DummyNeedsView:
    """Minimal NeedsView-like test double."""

    def __init__(self, needs: list[dict[str, Any]]) -> None:
        """Create a view over needs represented as dict-like structures."""
        self._needs = needs

    def values(self) -> list[dict[str, Any]]:
        """Return all needs."""
        return self._needs

    def filter_is_external(self, is_external: bool) -> DummyNeedsView:
        """Filter needs by their is_external flag."""
        return DummyNeedsView(
            [n for n in self._needs if n.get("is_external", False) == is_external]
        )


def test_eval_need_check_invalid_check_parts_raises_value_error() -> None:
    """Raise error when a check does not contain exactly three parts."""
    log = fake_check_logger()
    need = test_need(status="valid")

    with pytest.raises(ValueError, match="Invalid check defined"):
        graph_checks.eval_need_check(need, "status==valid", log)


def test_eval_need_check_unknown_operator_raises_value_error() -> None:
    """Raise error when an unsupported binary operator is used."""
    log = fake_check_logger()
    need = test_need(status="valid")

    with pytest.raises(ValueError, match="Binary Operator not defined"):
        graph_checks.eval_need_check(need, "status <> valid", log)


def test_eval_need_check_missing_attribute_logs_and_returns_false() -> None:
    """Return False and log warning when referenced attribute is not present."""
    log = fake_check_logger()
    need = test_need(status="valid")

    result = graph_checks.eval_need_check(need, "priority == high", log)

    assert result is False
    log.assert_warning("Attribute not defined: priority")

    result2 = graph_checks.eval_need_condition(need, {"not": ["status == valid"]}, log)

    assert result2 is False
    # assert "Attribute not defined: priority" in msg


def test_eval_need_condition_invalid_type_raises_value_error() -> None:
    """Raise error for condition values that are neither string nor dict."""
    log = fake_check_logger()
    need = test_need(status="valid")

    with pytest.raises(ValueError, match="Invalid condition type"):
        graph_checks.eval_need_condition(need, 123, log)  # type: ignore[arg-type]


def test_eval_need_condition_not_with_wrong_operand_count_raises_value_error() -> None:
    """Raise error when 'not' does not receive exactly one operand."""
    log = fake_check_logger()
    need = test_need(status="valid")

    with pytest.raises(ValueError, match="requires exactly one operand"):
        graph_checks.eval_need_condition(
            need,
            {"not": ["status == valid", "status != invalid"]},
            log,
        )


def test_eval_need_condition_and_or_xor_branches() -> None:
    """Evaluate logical combination branches and, or and xor."""
    log = fake_check_logger()
    need = test_need(status="valid", kind="req")

    and_result = graph_checks.eval_need_condition(
        need,
        {"and": ["status == valid", "kind == req"]},
        log,
    )
    or_result = graph_checks.eval_need_condition(
        need,
        {"or": ["status == invalid", "kind == req"]},
        log,
    )
    xor_result = graph_checks.eval_need_condition(
        need,
        {"xor": ["status == valid", "kind == req"]},
        log,
    )

    assert and_result is True
    assert or_result is True
    assert xor_result is False

    with pytest.raises(ValueError, match="Unsupported condition operator: blah"):
        graph_checks.eval_need_condition(
            need,
            {"blah": ["status == valid", "kind == req"]},
            log,
        )


def test_filter_needs_by_criteria_invalid() -> None:
    """Raise error when include/exclude selector key is invalid."""
    log = fake_check_logger()
    test_need()
    needs_types = [NeedType({"title": "testtype", "prefix": "t", "directive": "req"})]
    needs = [test_need(id="N1", type="testtype", status="valid")]

    with pytest.raises(ValueError, match="Invalid need selection"):
        graph_checks.filter_needs_by_criteria(
            needs_types,
            needs,
            {"invalid": "req", "condition": "status == valid"},
            log,
        )

    with pytest.raises(ValueError, match="Invalid selection"):
        graph_checks.filter_needs_by_criteria(
            needs_types,
            needs,
            {"exclude": "req"},
            log,
        )
    with pytest.raises(
        ValueError, match="Invalid need selection: both include and exclude are set"
    ):
        graph_checks.filter_needs_by_criteria(
            needs_types,
            needs,
            {"include": "req", "exclude": "req"},
            log,
        )


def test_filter_needs_by_criteria_unknown_type_logs_warning() -> None:
    """Log warning when selected pattern contains unknown need type."""
    log = fake_check_logger()
    needs_types = [NeedType({"title": "testtype", "prefix": "t", "directive": "req"})]
    needs = [test_need(id="N1", type="whasxd", status="valid")]

    selected = graph_checks.filter_needs_by_criteria(
        needs_types,
        needs,
        {"include": "unknown", "condition": "status == valid"},
        log,
    )
    assert selected == []
    assert log.warnings == 1
    log.assert_warning(
        "Unknown need type `unknown` in graph check.", expect_location=False
    )


# ---------------------------------------------------------------------------
# check_safety_security_relation
#
# These tests are written FIRST (TDD). The function does not exist yet, so
# each test fails at call-time with AttributeError — that is the expected
# failure. Once implemented, they should pass.
# ---------------------------------------------------------------------------


class NeedItemView:
    """Minimal NeedsView-like test double backed by real NeedItem objects."""

    def __init__(self, needs: list[NeedItem]) -> None:
        self._needs = needs

    def values(self) -> list[NeedItem]:
        return self._needs

    def filter_is_external(self, is_external: bool) -> NeedItemView:
        return NeedItemView(
            [n for n in self._needs if n.get("is_external", False) == is_external]
        )


def _link(need_item: NeedItem, **links: list[str]) -> NeedItem:
    """Set ``_links`` on a need built by ``test_need`` (the helper's ``links``
    kwarg is re-wrapped and unusable, so assign the real structure directly)."""
    need_item._links = {  # type: ignore[attr-defined]
        relation: [NeedLink(id=target_id) for target_id in target_ids]
        for relation, target_ids in links.items()
    }
    return need_item


def _run_safety_security_relation(needs: list[NeedItem]):
    """Run the new check against a list of NeedItems and return the logger."""
    log = fake_check_logger()
    graph_checks.check_safety_security_relation(  # type: ignore[attr-defined]
        app=None,  # type: ignore[arg-type]
        all_needs=NeedItemView(needs),
        log=log,
    )
    return log


def test_safety_security_asil_source_to_qm_target_via_includes_flags() -> None:
    """ASIL source including a QM target is flagged (source-owned relation)."""
    target = test_need(id="tgt", type="comp", status="valid", safety="QM")
    source = _link(
        test_need(
            id="src",
            type="feat",
            status="valid",
            safety="ASIL_B",
        ),
        includes=["tgt"],
    )
    log = _run_safety_security_relation([source, target])
    log.assert_warning("safety classification mismatch via `includes`")


def test_safety_security_qm_source_to_asil_target_via_derived_from_flags() -> None:
    """QM source derived-from an ASIL target is flagged (target-owned, reverse)."""
    target = test_need(id="parent", type="stkh_req", status="valid", safety="ASIL_B")
    source = _link(
        test_need(
            id="child",
            type="feat_req",
            status="valid",
            safety="QM",
        ),
        derived_from=["parent"],
    )
    log = _run_safety_security_relation([source, target])
    log.assert_warning("safety classification mismatch via `derived_from`")


def test_safety_security_matching_classifications_no_flag() -> None:
    """Matching safety classifications across a relation are not flagged."""
    target = test_need(id="parent", type="stkh_req", status="valid", safety="ASIL_B")
    source = _link(
        test_need(
            id="child",
            type="feat_req",
            status="valid",
            safety="ASIL_B",
        ),
        derived_from=["parent"],
    )
    log = _run_safety_security_relation([source, target])
    log.assert_no_warnings()


def test_safety_security_invalid_source_ignored() -> None:
    """An invalid source is not checked even if it links a mismatched target."""
    target = test_need(id="parent", type="stkh_req", status="valid", safety="ASIL_B")
    source = _link(
        test_need(
            id="child",
            type="feat_req",
            status="invalid",
            safety="QM",
        ),
        derived_from=["parent"],
    )
    log = _run_safety_security_relation([source, target])
    log.assert_no_warnings()


def test_safety_security_target_lacking_safety_no_flag() -> None:
    """A target without a safety attribute is not flagged (no false positive)."""
    target = test_need(id="tc", type="testcase", status="valid")
    source = _link(
        test_need(
            id="src",
            type="feat",
            status="valid",
            safety="ASIL_B",
        ),
        includes=["tc"],
    )
    log = _run_safety_security_relation([source, target])
    log.assert_no_warnings()


def test_safety_security_security_mismatch_flags() -> None:
    """A security YES/NO mismatch across a relation is flagged."""
    target = test_need(id="iface", type="logic_arc_int", status="valid", security="NO")
    source = _link(
        test_need(
            id="comp",
            type="comp",
            status="valid",
            security="YES",
        ),
        implements=["iface"],
    )
    log = _run_safety_security_relation([source, target])
    log.assert_warning("security classification mismatch via `implements`")


def test_safety_security_not_checked_relation_no_flag() -> None:
    """A mismatch via a "Not checked" relation (e.g. fully_verifies) is NOT flagged.

    The requirement carves out a "Not checked" group (traceability/evidence
    links). A naive check-all implementation would flag this; the correct
    implementation must skip it.
    """
    target = test_need(id="verified", type="feat_req", status="valid", safety="QM")
    source = _link(
        test_need(
            id="tm",
            type="test_metadata",
            status="valid",
            safety="ASIL_B",
        ),
        fully_verifies=["verified"],
    )
    log = _run_safety_security_relation([source, target])
    log.assert_no_warnings()
