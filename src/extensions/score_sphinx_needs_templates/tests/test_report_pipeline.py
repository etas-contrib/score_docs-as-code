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
"""Contract tests for the graph traversal used by L+."""

from score_sphinx_needs_templates.lplus import _report_graph


class _Link:
    def __init__(self, target: str) -> None:
        self.id = target


class _Need:
    def __init__(self, need_id: str, title: str, links: dict[str, list[str]]) -> None:
        self.values = {"id": need_id, "title": title, "type": "test"}
        self.links = {
            field: [_Link(target) for target in targets]
            for field, targets in links.items()
        }

    def __getitem__(self, key: str) -> object:
        return self.values[key]

    def get(self, key: str, default: object = None) -> object:
        return self.values.get(key, default)

    def get_links(self, field: str, *, as_str: bool = True) -> list[_Link]:
        del as_str
        return self.links.get(field, [])

    def iter_links_items(self, *, as_str: bool = True):
        del as_str
        return ((field, links) for field, links in self.links.items())


def test_lplus_graph_preserves_include_order_and_excludes_unrelated_needs() -> None:
    report = _Need("report", "Report", {"belongs_to": ["module"]})
    module = _Need("module", "Module", {"includes": ["second", "first"]})
    second = _Need("second", "Second", {"belongs_to": ["feature"]})
    first = _Need("first", "First", {"belongs_to": ["feature"]})
    feature = _Need("feature", "Feature", {})
    unrelated = _Need("unrelated", "Unrelated", {})
    view = {
        need["id"]: need for need in [report, module, second, first, feature, unrelated]
    }

    components, graph = _report_graph(view, report)  # type: ignore[arg-type]

    assert [need["id"] for need in components] == ["second", "first"]
    assert {need["id"] for need in graph} == {
        "report",
        "module",
        "second",
        "first",
        "feature",
    }
