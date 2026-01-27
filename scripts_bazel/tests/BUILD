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

load("@aspect_rules_py//py:defs.bzl", "py_test")
load("@pip_process//:requirements.bzl", "all_requirements")

py_test(
    name = "generate_sourcelinks_cli_test",
    srcs = ["generate_sourcelinks_cli_test.py"],
    deps = [
        "//scripts_bazel:generate_sourcelinks",
        "//src/extensions/score_source_code_linker",
    ] + all_requirements,
)

py_test(
    name = "merge_sourcelinks_test",
    srcs = ["merge_sourcelinks_test.py"],
    deps = [
        "//scripts_bazel:merge_sourcelinks",
    ] + all_requirements,
)
