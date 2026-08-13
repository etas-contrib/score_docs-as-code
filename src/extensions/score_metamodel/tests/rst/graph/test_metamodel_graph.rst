..
   # *******************************************************************************
   # Copyright (c) 2025 Contributors to the Eclipse Foundation
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

.. test_metadata::
   :id: test_metadata__metamodel_graph_checks
   :version: 1
   :partially_verifies_list: tool_req__docs_safety_security_relation
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the safety/security classification consistency check across relations.


.. Setup: a QM and an ASIL_B stakeholder requirement, both valid.

.. stkh_req:: Parent requirement QM
   :id: stkh_req__graph__parent_qm
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: YES
   :rationale: Setup target for the derived_from tests.
   :valid_from: v0.1
   :status: valid



.. stkh_req:: Parent requirement ASIL_B
   :id: stkh_req__graph__parent_asil_b
   :version: 1
   :reqtype: Functional
   :safety: ASIL_B
   :security: YES
   :rationale: Setup target for the derived_from tests.
   :valid_from: v0.1
   :status: valid



.. Positive Test: matching safety (QM -> QM) via derived_from is not flagged.

.. feat_req:: Child requirement 1
   :id: feat_req__graph__child_1
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: YES
   :valid_from: v0.1
   :status: valid
   :derived_from: stkh_req__graph__parent_qm
   :expect_not: mismatch



.. Positive Test: matching safety (ASIL_B -> ASIL_B) via derived_from is not flagged.

.. feat_req:: Child requirement 2
   :id: feat_req__graph__child_2
   :version: 1
   :reqtype: Functional
   :safety: ASIL_B
   :security: YES
   :valid_from: v0.1
   :status: valid
   :derived_from: stkh_req__graph__parent_asil_b
   :expect_not: mismatch



.. Negative Test: ASIL_B source derived_from a QM target is flagged
   (source-owned relation, reverse direction previously unchecked).

.. feat_req:: Child requirement 3
   :id: feat_req__graph__child_3
   :version: 1
   :reqtype: Functional
   :safety: ASIL_B
   :security: YES
   :valid_from: v0.1
   :status: valid
   :derived_from: stkh_req__graph__parent_qm
   :expect: safety classification mismatch via `derived_from`



.. Negative Test: QM source derived_from an ASIL_B target is flagged
   (target-owned relation).

.. feat_req:: Child requirement 4
   :id: feat_req__graph__child_4
   :version: 1
   :reqtype: Functional
   :safety: QM
   :security: YES
   :valid_from: v0.1
   :status: valid
   :derived_from: stkh_req__graph__parent_asil_b
   :expect: safety classification mismatch via `derived_from`



.. Negative Test (dead link): target does not exist.
   This warning comes from sphinx-needs core dead-link detection, not from the
   score_metamodel graph checks, so it survives the rewrite.

.. feat_req:: Child requirement 5
   :id: feat_req__graph__child_5
   :version: 1
   :reqtype: Functional
   :safety: ASIL_B
   :security: YES
   :valid_from: v0.1
   :status: valid
   :derived_from: feat_req__graph__does_not_exist
   :expect: unknown outgoing link
