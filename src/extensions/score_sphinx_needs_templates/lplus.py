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
"""L+ report materialization.

L+ records a report placeholder during the normal parallel read.  Once worker
environments have been merged, it renders the selected Jinja template against
the complete NeedsView and materializes the resulting RST fragment in the
cached doctree.  The only Sphinx-private operation is the version-pinned local
ToC refresh.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, cast

from docutils import nodes
from docutils.parsers.rst import Parser, directives
from docutils.utils import new_document
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from sphinx import version_info as sphinx_version
from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.util.docutils import SphinxDirective
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.need_item import NeedItem, NeedLink
from sphinx_needs.nodes import Need

_DECLARATIONS = "_score_lplus_reports"
_FINGERPRINTS = "_score_lplus_report_fingerprints"
_REVERSE_DEPS = "_score_lplus_reverse_dependencies"
_EXTENSION_VERSION = "lplus-2"
_SUPPORTED_SPHINX_MAJOR = 9


class LPlusReportPlaceholder(nodes.General, nodes.Element):
    """A node which exists only until the merged Need model is available."""


def _env_map(env: Any, name: str) -> dict[str, Any]:
    value = getattr(env, name, None)
    if not isinstance(value, dict):
        value = {}
        setattr(env, name, value)
    return value


def _split_inputs(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[,\n]", value) if item.strip()]


def _declaration(
    *, report_id: str, docname: str, template: str, external_inputs: Iterable[str]
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "docname": docname,
        "template": template,
        "external_inputs": sorted(set(external_inputs)),
        "version": _EXTENSION_VERSION,
    }


def _record_declaration(env: Any, declaration: dict[str, Any]) -> None:
    declarations = _env_map(env, _DECLARATIONS)
    report_id = declaration["report_id"]
    previous = declarations.get(report_id)
    if previous is not None and previous != declaration:
        raise SphinxError(
            f"L+ report {report_id!r} is declared more than once with different configuration"
        )
    declarations[report_id] = declaration


class LPlusReportDirective(SphinxDirective):
    """Declare a report template which owns an L+ placeholder."""

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "id": directives.unchanged_required,
        "template": directives.unchanged,
        "external-inputs": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        report_id = str(self.options.get("id", "")).strip()
        if not report_id:
            raise SphinxError("score_lplus_report requires an :id: option")
        template = str(self.options.get("template", "mod_ver_report_tiny")).strip()
        declaration = _declaration(
            report_id=report_id,
            docname=self.env.docname,
            template=template,
            external_inputs=_split_inputs(self.options.get("external-inputs")),
        )
        _record_declaration(self.env, declaration)
        return [
            LPlusReportPlaceholder(
                "",
                report_id=report_id,
                template=template,
                source_docname=self.env.docname,
            )
        ]


def _need_id(value: NeedLink | str) -> str:
    if isinstance(value, str):
        try:
            return str(NeedLink.parse_address(value).id)
        except (AttributeError, TypeError, ValueError):
            return value.split("[", 1)[0]
    return str(value.id)


def _need_links(need: NeedItem, field: str) -> list[NeedLink]:
    try:
        return list(need.get_links(field, as_str=False))
    except KeyError:
        return []


def _link_targets(view: Mapping[str, NeedItem], need: NeedItem) -> Iterable[NeedItem]:
    """Yield existing outgoing targets in the Need's declared order."""
    for _field, links in need.iter_links_items(as_str=False):
        for link in links:
            target = view.get(_need_id(link))
            if target is not None:
                yield target


def _incoming_dependents(
    view: Mapping[str, NeedItem], root_ids: set[str]
) -> Iterable[NeedItem]:
    for candidate in view.values():
        if any(
            _need_id(link) in root_ids
            for _field, links in candidate.iter_links_items(as_str=False)
            for link in links
        ):
            yield candidate


def _report_graph(
    view: Mapping[str, NeedItem], report: NeedItem
) -> tuple[list[NeedItem], list[NeedItem]]:
    """Return the ordered component outline and the report dependency closure."""
    module: NeedItem | None = None
    for link in _need_links(report, "belongs_to"):
        candidate = view.get(_need_id(link))
        if candidate is not None:
            module = candidate
            break
    if module is None:
        raise SphinxError(
            f"L+ report {report['id']}: active belongs_to target was not found"
        )

    components: list[NeedItem] = []
    for link in _need_links(module, "includes"):
        component = view.get(_need_id(link))
        if component is None:
            raise SphinxError(
                f"L+ report {report['id']}: module {module['id']} links to missing "
                f"component {_need_id(link)} through includes"
            )
        components.append(component)

    roots: list[NeedItem] = [report, module, *components]
    for field in ("satisfied_by", "contains", "covers", "evidence", "realizes"):
        roots.extend(
            target
            for link in _need_links(report, field)
            if (target := view.get(_need_id(link))) is not None
        )

    closure: dict[str, NeedItem] = {}
    pending = list(roots)
    while pending:
        current = pending.pop(0)
        current_id = str(current["id"])
        if current_id in closure:
            continue
        closure[current_id] = current
        pending.extend(_link_targets(view, current))

    for candidate in _incoming_dependents(view, set(closure)):
        closure[str(candidate["id"])] = candidate

    return components, list(closure.values())


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        return [_jsonable(item) for item in value]
    return (
        value
        if value is None or isinstance(value, str | int | float | bool)
        else str(value)
    )


def _fingerprint(
    declaration: Mapping[str, Any], needs: Iterable[NeedItem], template_fingerprint: str
) -> str:
    payload = {
        "declaration": dict(declaration),
        "template": template_fingerprint,
        "needs": sorted(
            (_jsonable(dict(need.items())) for need in needs),
            key=lambda item: str(item.get("id", "")),
        ),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _template_path(app: Sphinx, template: str) -> Path:
    name = template if template.endswith(".need") else f"{template}.need"
    path = Path(str(app.config.needs_template_folder)) / name
    if not path.is_file():
        raise SphinxError(f"L+ report template {name!r} does not exist at {path}")
    return path


def _template_fingerprint(app: Sphinx, template: str) -> str:
    try:
        content = _template_path(app, template).read_bytes()
    except SphinxError:
        content = b"<missing>"
    return hashlib.sha256(content).hexdigest()


def _template_context(report: NeedItem, view: Mapping[str, NeedItem]) -> dict[str, Any]:
    context = {str(key): value for key, value in report.items()}
    for field in (
        "belongs_to",
        "satisfied_by",
        "contains",
        "covers",
        "evidence",
        "realizes",
    ):
        if field in context:
            context[field] = [_need_id(link) for link in _need_links(report, field)]

    def linked(need_id: str, field: str) -> list[NeedItem]:
        source_id = _need_id(need_id)
        source = view.get(source_id)
        if source is None:
            raise SphinxError(
                f"L+ report {report['id']}: linked_needs source {source_id!r} was not found"
            )
        result: list[NeedItem] = []
        for link in _need_links(source, field):
            target_id = _need_id(link)
            target = view.get(target_id)
            if target is None:
                raise SphinxError(
                    f"L+ report {report['id']}: {source_id}.{field} links to "
                    f"missing Need {target_id!r}"
                )
            result.append(target)
        return result

    context.update(
        report=report,
        linked_needs=linked,
        report_need=report,
    )
    return context


def _render_template(
    app: Sphinx,
    declaration: Mapping[str, Any],
    report: NeedItem,
    view: Mapping[str, NeedItem],
) -> tuple[str, Path]:
    template = str(declaration["template"])
    template_path = _template_path(app, template)
    environment = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,
    )
    rendered = environment.get_template(template_path.name).render(
        **_template_context(report, view)
    )
    return rendered, template_path


def _parse_template(
    app: Sphinx,
    source_document: nodes.document,
    docname: str,
    rendered: str,
    template_path: Path,
) -> list[nodes.Node]:
    """Parse rendered RST as a fragment with the active Sphinx environment."""
    settings = copy.copy(source_document.settings)
    settings.env = app.env
    settings.docname = docname
    settings.source = str(template_path)

    generated_document = new_document(str(template_path), settings=settings)
    Parser().parse(rendered, generated_document)
    from sphinx_needs.directives.needpie import Needpie
    from sphinx_needs.directives.needtable import Needtable

    # The normal Needtable directive gets a target from the surrounding
    # source-reader machinery.  A fragment parsed after env-updated has no
    # reader-owned target, while sphinx-needs' write transform requires one.
    # Keep this compatibility detail local to the fragment parser.
    prefix = f"needtable-{re.sub(r'[^a-zA-Z0-9]+', '-', docname).strip('-')}"
    for serial, table in enumerate(generated_document.findall(Needtable), start=1):
        if not table.get("ids"):
            table["ids"] = [f"{prefix}-lplus-{serial}"]
    for serial, pie in enumerate(generated_document.findall(Needpie), start=1):
        if not pie.get("ids"):
            pie["ids"] = [f"{prefix}-lplus-pie-{serial}"]
    return list(generated_document.children)


class _EmptyLinkedNeeds:
    """Pickleable placeholder for the incomplete read-phase model."""

    def __call__(self, *_args: Any, **_kwargs: Any) -> list[NeedItem]:
        return []


_empty_linked_needs = _EmptyLinkedNeeds()


def _materialize_report(
    app: Sphinx,
    declaration: dict[str, Any],
    view: Mapping[str, NeedItem],
) -> str:
    docname = str(declaration["docname"])
    report_id = str(declaration["report_id"])
    report = view.get(report_id)
    if report is None:
        raise SphinxError(
            f"L+ report {report_id!r} is not present in the resolved Need model"
        )

    try:
        doctree = app.env._write_doc_doctree_cache[docname]
    except KeyError:
        doctree = app.env.get_doctree(docname)

    placeholders = [
        node
        for node in doctree.findall(LPlusReportPlaceholder)
        if node.get("report_id") == report_id
    ]
    if not placeholders:
        raise SphinxError(
            f"L+ report {report_id!r} has no placeholder in document {docname!r}"
        )
    if len(placeholders) != 1:
        raise SphinxError(
            f"L+ report {report_id!r} has {len(placeholders)} placeholders"
        )

    rendered, template_path = _render_template(app, declaration, report, view)
    replacement = _parse_template(app, doctree, docname, rendered, template_path)
    placeholders[0].parent.replace(placeholders[0], replacement)
    _register_standard_labels(app, doctree, docname)
    _TocCompatibilityAdapter.refresh(app, doctree, docname)
    app.env._write_doc_doctree_cache[docname] = doctree

    reverse = _env_map(app.env, _REVERSE_DEPS)
    for report_docs in reverse.values():
        if isinstance(report_docs, set):
            report_docs.discard(docname)
    for need in _report_graph(view, report)[1]:
        source_docname = need.get("docname")
        reverse.setdefault(str(need["id"]), set()).add(docname)
        if (
            isinstance(source_docname, str)
            and source_docname
            and source_docname != docname
        ):
            app.env.dependencies.setdefault(docname, set()).add(
                app.env.doc2path(source_docname)
            )
    for external_input in declaration.get("external_inputs", []):
        reverse.setdefault(f"external:{external_input}", set()).add(docname)
        app.env.dependencies.setdefault(docname, set()).add(
            app.env.srcdir / str(external_input)
        )
    app.env.dependencies.setdefault(docname, set()).add(cast(Any, template_path))
    reverse.setdefault(f"template:{template_path}", set()).add(docname)
    reverse.setdefault(f"config:{report_id}", set()).add(docname)
    return _fingerprint(
        declaration,
        _report_graph(view, report)[1],
        _template_fingerprint(app, str(declaration["template"])),
    )


class _TocCompatibilityAdapter:
    """Refresh one local ToC using the collector version we support."""

    @staticmethod
    def refresh(app: Sphinx, document: nodes.document, docname: str) -> None:
        if sphinx_version[0] != _SUPPORTED_SPHINX_MAJOR:
            raise SphinxError(
                f"L+ local ToC adapter supports only Sphinx 9.x; got {sphinx_version}"
            )
        from sphinx.environment.collectors.toctree import TocTreeCollector

        previous_docname = app.env.current_document.docname
        app.env.current_document.docname = docname
        try:
            TocTreeCollector().process_doc(app, document)
        finally:
            app.env.current_document.docname = previous_docname


def _register_standard_labels(
    app: Sphinx, document: nodes.document, docname: str
) -> None:
    standard = app.env.domains.standard_domain
    standard.clear_doc(docname)
    standard.process_doc(app.env, docname, document)


def _ensure_declaration_for_need(app: Sphinx, doctree: nodes.document) -> None:
    """Make the existing mod_ver_report syntax use the L+ placeholder."""
    declarations = _env_map(app.env, _DECLARATIONS)
    needs = SphinxNeedsData(app.env).get_needs_mutable()
    for need_node in list(doctree.findall(Need)):
        report_id = str(need_node.get("refid", ""))
        need = needs.get(report_id)
        if need is None or need.get("type") != "mod_ver_report":
            continue

        declaration = declarations.get(report_id)
        if declaration is None:
            declaration = _declaration(
                report_id=report_id,
                docname=app.env.docname,
                template=str(need.get("template") or "mod_ver_report_tiny"),
                external_inputs=(),
            )
            _record_declaration(app.env, declaration)

        # The standard Need remains in the document for metadata/layout, but
        # its read-phase template body must not be rendered a second time.
        need_node.children.clear()

        if not any(
            isinstance(node, LPlusReportPlaceholder)
            and node.get("report_id") == report_id
            for node in doctree.findall(LPlusReportPlaceholder)
        ):
            need_node.parent.insert(
                need_node.parent.index(need_node) + 1,
                LPlusReportPlaceholder(
                    "",
                    report_id=report_id,
                    template=declaration["template"],
                ),
            )


def _on_doctree_read(app: Sphinx, doctree: nodes.document) -> None:
    _ensure_declaration_for_need(app, doctree)


def _on_purge_doc(app: Sphinx, env: Any, docname: str) -> None:
    declarations = _env_map(env, _DECLARATIONS)
    removed = [
        report_id
        for report_id, item in declarations.items()
        if item.get("docname") == docname
    ]
    for report_id in removed:
        declarations.pop(report_id, None)
        _env_map(env, _FINGERPRINTS).pop(report_id, None)
    for key, docnames in list(_env_map(env, _REVERSE_DEPS).items()):
        if isinstance(docnames, set):
            docnames.discard(docname)
            if not docnames:
                _env_map(env, _REVERSE_DEPS).pop(key, None)


def _on_merge_info(app: Sphinx, env: Any, docnames: Iterable[str], other: Any) -> None:
    other_declarations = getattr(other, _DECLARATIONS, {})
    if isinstance(other_declarations, dict):
        allowed = set(docnames)
        for _report_id, declaration in other_declarations.items():
            if declaration.get("docname") in allowed:
                _record_declaration(env, dict(declaration))

    reverse = _env_map(env, _REVERSE_DEPS)
    other_reverse = getattr(other, _REVERSE_DEPS, {})
    if isinstance(other_reverse, dict):
        allowed = set(docnames)
        for need_id, report_docs in other_reverse.items():
            selected = (
                set(report_docs) & allowed if isinstance(report_docs, set) else set()
            )
            if selected:
                reverse.setdefault(need_id, set()).update(selected)


def _on_env_updated(app: Sphinx, env: Any) -> list[str]:
    declarations = _env_map(env, _DECLARATIONS)
    if not declarations:
        return []

    view = SphinxNeedsData(env).get_needs_view()
    fingerprints = _env_map(env, _FINGERPRINTS)
    changed: list[str] = []
    for report_id in sorted(declarations):
        declaration = declarations[report_id]
        report = view.get(report_id)
        if report is None:
            raise SphinxError(
                f"L+ report {report_id!r} is not present in the resolved Need model"
            )
        _components, graph = _report_graph(view, report)
        fingerprint = _fingerprint(
            declaration,
            graph,
            _template_fingerprint(app, str(declaration["template"])),
        )
        if fingerprints.get(report_id) == fingerprint:
            continue
        docname = str(declaration["docname"])
        result = _materialize_report(app, declaration, view)
        fingerprints[report_id] = result
        changed.append(docname)
    return sorted(set(changed))


def setup_lplus(app: Sphinx) -> None:
    app.add_node(LPlusReportPlaceholder)
    app.add_directive("score_lplus_report", LPlusReportDirective)
    app.config.needs_render_context.setdefault("linked_needs", _empty_linked_needs)
    app.connect("doctree-read", _on_doctree_read, priority=600)
    app.connect("env-purge-doc", _on_purge_doc, priority=-100)
    app.connect("env-merge-info", _on_merge_info, priority=600)
    app.connect("env-updated", _on_env_updated, priority=700)
