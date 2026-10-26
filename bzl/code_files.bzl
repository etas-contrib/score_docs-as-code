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
"""Collect implementation files for component bundles and source links."""

# Internal implementation-file collection shared by bundle metadata and source
# links. Keep this module independent of bundle composition: the private file
# target is an input to source-link generation, which is itself a bundle input.
# Depending on the composed bundle here would introduce a dependency cycle.
#
# The aspect retains target labels alongside declared files. Component boundaries
# apply to the declaring target, not the package of an individual file, because
# a library may explicitly declare headers or filegroups from another package.

CodeTargetSourcesInfo = provider(
    doc = "Source files collected from an implementation target and its dependencies.",
    fields = {
        "kind": "Bazel rule kind of the selected code target.",
        "direct_sources": "Resolved source/header files declared by this target.",
        "targets": "Depset of target labels and their direct source/header files.",
    },
)

def _source_files_from_attributes(ctx):
    """Return files explicitly declared through source or header attributes."""
    # DefaultInfo resolves filegroups and generator outputs at the attribute
    # boundary. We inspect the consuming library's declarations, so generator
    # inputs and the library's compiled outputs do not enter the file list.
    source_files = []
    for attribute_name in ["srcs", "hdrs", "textual_hdrs"]:
        if not hasattr(ctx.rule.attr, attribute_name):
            continue
        for source in getattr(ctx.rule.attr, attribute_name):
            if type(source) == "File":
                source_files.append(source)
            else:
                source_files.extend(source[DefaultInfo].files.to_list())
    return source_files

def _collect_code_target_sources_impl(target, ctx):
    """Collect source files from an implementation target and its ``deps`` tree."""
    direct_sources = _source_files_from_attributes(ctx)
    dependencies = getattr(ctx.rule.attr, "deps", [])
    return [CodeTargetSourcesInfo(
        # The aspect follows dependencies to collect source files, but the
        # manifest needs the kind of the target explicitly selected by the
        # bundle rather than the kinds of those transitive dependencies.
        kind = ctx.rule.kind,
        direct_sources = direct_sources,
        # Keep the declaring target's label beside its files: file ownership
        # alone cannot express libraries that explicitly use sibling-package
        # filegroups. A flat depset lets each bundle apply its own boundary.
        targets = depset(
            direct = [struct(label = ctx.label, files = tuple(direct_sources))],
            transitive = [dependency[CodeTargetSourcesInfo].targets for dependency in dependencies],
        ),
    )]

collect_code_target_sources = aspect(
    implementation = _collect_code_target_sources_impl,
    attr_aspects = ["deps"],
    provides = [CodeTargetSourcesInfo],
    doc = "Collects sources recursively through standard implementation dependencies.",
)

def _bundle_code_files_impl(ctx):
    """Resolve the implementation artifacts owned by this bundle.

    Explicitly selected targets always contribute their declarations. Transitive
    dependencies are filtered by the bundle's repository and BUILD package,
    including subpackages. Local targets reached through foreign dependencies
    remain eligible; the flat collection does not prune dependency branches.
    Nested documentation bundles keep their own component file lists.
    """
    selected = [target[CodeTargetSourcesInfo] for target in ctx.attr.code_targets]
    files = []

    # Merge dependency records before filtering so shared targets are visited
    # once even when multiple implementation entry points depend on them.
    targets = depset(transitive = [info.targets for info in selected])
    package = ctx.label.package
    for target in targets.to_list():
        label = target.label
        if label.workspace_name == ctx.label.workspace_name and (
            not package or label.package == package or label.package.startswith(package + "/")
        ):
            files.extend(target.files)

    # Explicit selection includes a target's own declarations even when its
    # label is outside the component boundary.
    for info in selected:
        files.extend(info.direct_sources)
    return [DefaultInfo(files = depset(files))]

_bundle_code_files = rule(
    implementation = _bundle_code_files_impl,
    attrs = {
        "code_targets": attr.label_list(aspects = [collect_code_target_sources]),
    },
    doc = "Collects component implementation artifacts within the bundle package boundary.",
)

def collect_bundle_code_files(name, code_targets):
    """Declare the private file set shared by sourcelinks and internal consumers.

    The target lives in the bundle's BUILD package, so its own label provides
    the component boundary. It is independent of the composed bundle provider
    to avoid a cycle through the source-link cache used by that provider.
    """
    _bundle_code_files(
        name = name,
        code_targets = code_targets,
        visibility = ["//visibility:private"],
    )
    return ":" + name
