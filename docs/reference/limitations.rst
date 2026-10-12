..
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

Intentional Limitations
=======================

Some checks are intentionally limited to informational output, or are deferred
until the relevant process concepts and models are available.

.. list-table:: Quality control use cases at a glance
   :header-rows: 1
   :widths: 1 1 1

   * - Tool Requirements
     - Limitation
     - When to fix?
   * - :need:`tool_req__docs_req_link_satisfies_allowed`
     - Only INFO, not WARN
     - After next process_description release
   * - :need:`tool_req__arch_linkage_safety`
     - Loosened for compatibility
     - Unknown
   * - :need:`tool_req__arch_consistency_interf`
     - Only INFO, not WARN
     - docs_as_code v9 release?
   * - :need:`tool_req__docs_req_attr_testcov`
     - unclear?
     - Once concept is clarified
