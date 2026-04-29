..
   Copyright (c) 2026 Contributors to the Eclipse Foundation

   See the NOTICE file(s) distributed with this work for additional
   information regarding copyright ownership.

   This program and the accompanying materials are made available under the
   terms of the Apache License Version 2.0 which is available at
   https://www.apache.org/licenses/LICENSE-2.0

   SPDX-License-Identifier: Apache-2.0

Requirements
============

.. tool_req:: Supports extra_docs in docs() macro
   :id: tool_req__docs_extra_docs
   :implemented: YES
   :tags: Architecture
   :version: 1

   The ``docs()`` Bazel macro shall accept an ``extra_docs`` parameter
   containing a list of ``sphinx_docs_library`` targets.
   Their files shall be merged into the Sphinx source tree at the paths
   determined by each library's ``strip_prefix`` and ``prefix`` attributes.
