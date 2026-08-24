#!/usr/bin/env python3
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
"""Generate an RST file with a list-table and Mermaid class diagrams.

The generated RST contains one overview diagram and one focused diagram per
need type.  The focused diagrams are embedded directly in the RST.

Usage:
    generate_metamodel_rst.py --rst-output FILE --mmd-output FILE [METAMODEL_YAML]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import ruamel.yaml


def _parse_yaml(path: Path) -> dict:
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    with Path(path).open(encoding="utf-8") as fh:
        return yaml.load(fh)  # type: ignore[no-any-return]


def _split_targets(targets: str) -> list[str]:
    """Split a comma-separated target spec, ignoring the ``ANY`` wildcard."""
    if targets == "ANY":
        return []
    return [t.strip() for t in targets.split(",") if t.strip()]


def _incoming_mandatory_links(types: dict) -> dict[str, list[str]]:
    """Map each type to the source types that point at it via mandatory links."""
    incoming: dict[str, list[str]] = {name: [] for name in types}
    for source, ty in types.items():
        for targets in ty.get("mandatory_links", {}).values():
            for target in _split_targets(targets):
                if target in incoming and source not in incoming[target]:
                    incoming[target].append(source)
    return {name: sorted(sources) for name, sources in incoming.items()}


def _build_table(types: dict) -> list[str]:
    incoming = _incoming_mandatory_links(types)
    lines: list[str] = []
    lines.append(".. list-table:: Need Types")
    lines.append("   :header-rows: 1")
    lines.append("")
    lines.append("   * - Type")
    lines.append("     - Title")
    lines.append("     - Mandatory Options")
    lines.append("     - Links")
    lines.append("     - Incoming Mandatory Links")
    for name, ty in sorted(types.items()):
        title = ty.get("title", name)
        mandatory = (
            ", ".join(sorted(ty.get("mandatory_options", {}).keys())) or "\u2014"
        )
        optional_links = ty.get("optional_links", {})
        mandatory_links = ty.get("mandatory_links", {})
        link_strs = [
            f"**{n}**" if n in mandatory_links else n
            for n in sorted(set(optional_links) | set(mandatory_links))
        ]
        links = ", ".join(link_strs) or "\u2014"
        inc = ", ".join(incoming.get(name, [])) or "\u2014"
        lines.append("   * - " + name)
        lines.append("     - " + title)
        lines.append("     - " + mandatory)
        lines.append("     - " + links)
        lines.append("     - " + inc)
    return lines


def _class_declarations(types: dict) -> list[str]:
    """Declare every type, listing mandatory options as class members."""
    lines: list[str] = []
    for name in sorted(types):
        mandatory_opts = sorted(types[name].get("mandatory_options", {}).keys())
        if mandatory_opts:
            lines.append(f"class {name} {{")
            lines.extend(f"  +{opt}" for opt in mandatory_opts)
            lines.append("}")
        else:
            lines.append(f"class {name}")
    return lines


def _link_edges(types: dict, focal_name: str | None = None) -> list[str]:
    """Edges for all (mandatory + optional) links between known types."""
    lines: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for name, ty in sorted(types.items()):
        links = list(ty.get("mandatory_links", {}).items()) + list(
            ty.get("optional_links", {}).items()
        )
        for link_name, targets in sorted(links):
            for target in _split_targets(targets):
                if target not in types:
                    continue
                # A focused diagram should show only links touching its root;
                # links between two neighbours would add unrelated detail.
                if (
                    focal_name is not None
                    and name != focal_name
                    and target != focal_name
                ):
                    continue
                key = (name, target, link_name)
                if key not in seen:
                    seen.add(key)
                    # Keep every edge in source-to-target form.  Together with
                    # the BT direction this places the target above its source.
                    lines.append(f"{name} --> {target} : {link_name}")
    return lines


def _direct_dependencies(types: dict, name: str) -> set[str]:
    """Return the types directly linked to ``name`` in either direction."""
    dependencies = {name}
    # Include incoming links as well as outgoing links.  Otherwise a type that
    # is only referenced by other types would get an unhelpful one-node graph.
    for source, ty in types.items():
        links = list(ty.get("mandatory_links", {}).values()) + list(
            ty.get("optional_links", {}).values()
        )
        for targets in links:
            for target in _split_targets(targets):
                if target not in types:
                    continue
                if source == name:
                    dependencies.add(target)
                if target == name:
                    dependencies.add(source)
    return dependencies


def _node_styles(types: dict) -> list[str]:
    """Color nodes per the ``color`` option in metamodel.yaml.

    Dark text and a visible border keep pastel-filled nodes readable
    in both light and dark mermaid themes.
    """
    lines: list[str] = []
    for name, ty in sorted(types.items()):
        color = ty.get("color")
        if color:
            lines.append(f"style {name} fill:{color},stroke:#666,color:#000")
    return lines


def _build_mermaid(types: dict) -> list[str]:
    return _class_declarations(types) + _link_edges(types) + _node_styles(types)


def _build_focused_mermaid(types: dict, name: str) -> list[str]:
    """Build a Mermaid diagram containing one type and its direct neighbours."""
    included_names = _direct_dependencies(types, name)
    focused_types = {
        type_name: types[type_name]
        for type_name in sorted(included_names)
        if type_name in types
    }
    # Passing only these types to the renderer keeps unrelated nodes out of the
    # per-type image; the focal_name filter below also keeps unrelated edges out.
    lines = _class_declarations(focused_types) + _link_edges(
        focused_types, focal_name=name
    )
    lines.extend(
        line
        for line in _node_styles(focused_types)
        if not line.startswith(f"style {name} ")
    )

    # Make the type the visual focal point.  This is appended after the normal
    # styles so that the root style wins for types that already have a color.
    root_color = types[name].get("color", "#FFFFFF")
    lines.append(
        f"style {name} fill:{root_color},stroke:#000,stroke-width:3px,color:#000"
    )
    return lines


def _mermaid_document(types: dict, focal_name: str | None = None) -> list[str]:
    """Build a complete Mermaid document, optionally focused on one type."""
    diagram_lines = (
        _build_mermaid(types)
        if focal_name is None
        else _build_focused_mermaid(types, focal_name)
    )
    return [
        "---",
        "config:",
        "  layout: elk",
        "---",
        "classDiagram",
        # Dependencies point from the type defining the link to its target;
        # bottom-to-top therefore places targets above their sources.
        "  direction BT",
    ] + diagram_lines


def _effective_options(
    name: str, ty: dict, base_options: dict
) -> tuple[dict[str, str], dict[str, str]]:
    """Return the options a type receives after applying metamodel defaults."""
    # Shared options live outside each type in the YAML, but the details page
    # should describe the effective configuration users actually have to meet.
    mandatory = dict(base_options.get("mandatory_options", {}))
    mandatory.update(ty.get("mandatory_options", {}))
    optional = dict(base_options.get("optional_options", {}))
    optional.update(ty.get("optional_options", {}))

    prefix = ty.get("prefix", f"{name}__")
    mandatory.setdefault("id", f"^{prefix}[0-9a-z_]+$")
    return mandatory, optional


def _append_typed_mapping_section(
    lines: list[str],
    heading: str,
    mandatory_values: dict[str, str],
    optional_values: dict[str, str],
    value_title: str,
) -> None:
    """Append one table that distinguishes mandatory and optional values."""
    if not mandatory_values and not optional_values:
        return

    # A single table avoids repeating a prominent heading for each value kind.
    lines.extend(
        [
            heading,
            '"' * len(heading),
            "",
            ".. list-table::",
            "   :header-rows: 1",
            "",
            "   * - Type",
            f"     - {value_title}",
            "     - Definition",
        ]
    )
    for value_type, values in (
        ("Mandatory", mandatory_values),
        ("Optional", optional_values),
    ):
        for key, value in sorted(values.items()):
            lines.append(f"   * - {value_type}")
            lines.append(f"     - ``{key}``")
            lines.append(f"     - ``{value}``")
    lines.append("")


def _build_type_details(types: dict, base_options: dict) -> list[str]:
    """Build the per-type details and their focused diagrams."""
    incoming = _incoming_mandatory_links(types)
    lines = ["Need Type Details", "-----------------", ""]

    for name in sorted(types):
        ty = types[name]
        mandatory_options, optional_options = _effective_options(name, ty, base_options)
        title = ty.get("title", name)
        lines.extend([name, "~" * len(name), "", f"**Title:** {title}"])
        lines.append(f"**Prefix:** ``{ty.get('prefix', f'{name}__')}``")
        if "style" in ty:
            lines.append(f"**Style:** ``{ty['style']}``")

        lines.append("")
        _append_typed_mapping_section(
            lines,
            "Options",
            mandatory_options,
            optional_options,
            "Option",
        )
        _append_typed_mapping_section(
            lines,
            "Links",
            ty.get("mandatory_links", {}),
            ty.get("optional_links", {}),
            "Link",
        )

        if incoming.get(name):
            lines.extend(
                [
                    "Incoming Mandatory Links",
                    '"' * len("Incoming Mandatory Links"),
                    "",
                    ", ".join(f"``{source}``" for source in incoming[name]),
                    "",
                ]
            )

        lines.extend(
            [
                ".. mermaid::",
                f"   :caption: Direct dependencies of ``{name}``",
                "",
            ]
        )
        # Inline diagrams keep the generated assets self-contained.  The type
        # names therefore come directly from metamodel.yaml and need no second
        # list of declared output files in BUILD.
        lines.extend(f"   {line}" for line in _mermaid_document(types, name))
        lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate RST from metamodel.yaml")
    parser.add_argument("--rst-output", type=Path, required=True)
    parser.add_argument("--mmd-output", type=Path, required=True)
    parser.add_argument("metamodel", nargs="?", default=None)
    args = parser.parse_args()

    meta_path = (
        Path(args.metamodel)
        if args.metamodel
        else Path(__file__).parent / "metamodel.yaml"
    )
    if not meta_path.is_file():
        print(f"Error: metamodel.yaml not found at {meta_path}", file=sys.stderr)
        return 1

    try:
        data = _parse_yaml(meta_path)
    except Exception as exc:
        print(f"Error parsing YAML: {exc}", file=sys.stderr)
        return 1

    types = data.get("needs_types", {})
    if not types:
        print(
            "Error: 'needs_types' section not found in metamodel.yaml", file=sys.stderr
        )
        return 1

    table = _build_table(types)
    args.mmd_output.write_text(
        "\n".join(_mermaid_document(types)) + "\n", encoding="utf-8"
    )

    output = "\n".join(
        [
            "..",
            "   # (generated \u2014 do not edit)",
            "   # SPDX-License-Identifier: Apache-2.0",
            "",
            ".. _metamodel-types-visualization:",
            "",
            "Metamodel Types Visualization",
            "==============================",
            "",
            f".. mermaid:: {args.mmd_output.name}",
            "",
            "Need Types",
            "----------",
            "",
        ]
        + table
        + ["", ""]
        + _build_type_details(types, data.get("needs_types_base_options", {}))
    )

    args.rst_output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
