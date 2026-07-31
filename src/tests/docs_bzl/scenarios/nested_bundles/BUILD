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

load("//:bzl/mount_rules.bzl", "create_mounts_manifest")
load("//:docs.bzl", "docs", "docs_bundle")
load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("//:score_pytest.bzl", "score_pytest")

docs_bundle(
    name = "child",
    source_dir = "child",
    entry_doc = "landing",
    code_targets = [
        ":example_python",
        ":example_executable",
    ],
    tests = [
        ":example_test_one",
        ":example_test_two",
    ],
)

py_binary(
    name = "example_python",
    srcs = ["child/example.py"],
    main = "child/example.py",
)

cc_library(
    name = "example_library",
    srcs = ["child/example.cc"],
)

cc_binary(
    name = "example_executable",
    srcs = ["child/example_main.cc"],
    deps = [":example_library"],
)

score_pytest(
    name = "example_test_one",
    srcs = ["child/test_one.py"],
)

score_pytest(
    name = "example_test_two",
    srcs = ["child/test_two.py"],
)

# The child is nested below the parent bundle before the parent itself is
# mounted into the synthetic host tree below.
docs_bundle(
    name = "parent",
    source_dir = "parent",
    bundles = [{
        "bundle": ":child",
        "mount_at": "child",
    }],
)

# An aggregator deliberately has no source_dir. It only propagates its child
# and must preserve the declaration order in the generated manifest.
docs_bundle(
    name = "ordered_aggregate",
    bundles = [
        {"bundle": ":other", "mount_at": "first"},
        {"bundle": ":child", "mount_at": "second"},
    ],
)

docs_bundle(
    name = "other",
    source_dir = "other",
)

create_mounts_manifest(
    name = "ordered_aggregate_manifest",
    bundle = ":ordered_aggregate",
)

# A complete docs() invocation is the synthetic host project driven by the
# pytest integration test in //src/tests/docs_bzl.
docs(
    source_dir = "host_docs",
    test_sources = ["src/tests/docs_bzl/scenarios/nested_bundles"],
    bundles = [{
        "bundle": ":parent",
        "mount_at": "concepts/example_bundle",
    }],
)
