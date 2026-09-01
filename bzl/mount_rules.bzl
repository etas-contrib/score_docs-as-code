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
"""
Conversion of documentation bundles from Bazel into mount metadata.

The manifest records both the directories to mount and the exact documentation
files owned by each source bundle. The latter is needed because a source bundle
can live below another Bazel package, which is visible on disk but deliberately
excluded from the parent package's ``native.glob``.
"""

load("@score_docs_as_code//:bzl/bundle_rules.bzl", "DocsBundleInfo")

def _source_includes(entry):
    """Return direct bundle files as Sphinx include patterns.

    ``sphinx-mounts`` applies these patterns relative to the mounted directory.
    Include every file selected by the Bazel source glob: Sphinx will still
    parse only files matching the consumer's ``source_suffix`` while assets
    remain available to directives such as ``image`` and ``literalinclude``.
    """
    source_root = entry.runtime_path.rstrip("/")
    if source_root.endswith("/."):
        source_root = source_root[:-2]
    if source_root == ".":
        source_root = ""
    source_prefix = source_root + "/" if source_root else ""
    includes = []
    for source_file in entry.source_files:
        # ``source_files`` is populated by the ``source_dir``-scoped Bazel glob
        # and preserved unchanged when an entry is rebased. This conversion
        # therefore does not need to validate the source root again.
        includes.append("/" + source_file.short_path[len(source_prefix):])
    if includes:
        return sorted(includes)

    # An empty allowlist disables filtering in sphinx-mounts. Use an impossible
    # path so an empty source entry cannot accidentally discover nearby docs.
    return ["/__score_docs_as_code_no_direct_sources__"]

def _entry_json(entry):
    """Serialize one source or data entry for the mounts manifest."""
    return {
        "src_root": entry.src_root,
        "runtime_path": entry.runtime_path,
        "mount_at": entry.mount_at,
        "attach_to": entry.attach_to,
        "entry_doc": entry.entry_doc,
        "external": entry.external,
        "repository": entry.repository,
        "include": _source_includes(entry) if entry.src_root else [],
        "data": [f.path for f in entry.data.to_list()],
    }

def _mounts_manifest_impl(ctx):
    """Generate the canonical Sphinx mount manifest."""
    bundle_info = ctx.attr.bundle[DocsBundleInfo]
    entries = bundle_info.entries
    primary_entry = None
    if ctx.attr.primary_bundle:
        primary_entry = ctx.attr.primary_bundle[DocsBundleInfo].own_source_entry

    json_mounts = []
    for entry in entries:
        json_mounts.append(_entry_json(entry))

    out = ctx.actions.declare_file(ctx.label.name + ".json")
    manifest = {"mounts": json_mounts}
    if primary_entry != None:
        manifest["primary_source"] = _entry_json(primary_entry)
    ctx.actions.write(out, json.encode(manifest))
    return [DefaultInfo(files = depset([out]))]

_create_mounts_manifest = rule(
    implementation = _mounts_manifest_impl,
    attrs = {
        "bundle": attr.label(providers = [DocsBundleInfo]),
        "primary_bundle": attr.label(
            default = None,
            providers = [DocsBundleInfo],
            doc = "Optional host bundle whose direct sources define the primary-source allowlist.",
        ),
    },
    doc = "Writes a Sphinx mount manifest from reusable documentation bundles.",
)

def create_mounts_manifest(name, bundle, primary_bundle = None):
    """Create a Sphinx mount manifest from reusable documentation bundles.

    Args:
      name: Manifest target name.
      bundle: Bundle whose composed entries become ``mounts`` entries.
      primary_bundle: Optional host bundle. Its own source entry is emitted as
        ``primary_source`` so the runtime can exclude source files that are
        physically below the host directory but outside the host package's
        Bazel glob.
    """
    _create_mounts_manifest(
        name = name,
        bundle = bundle,
        primary_bundle = primary_bundle,
    )
    return ":" + name
