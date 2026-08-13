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

.. test_metadata::
   :id: test_metadata__safety_security_relation
   :partially_verifies_list: tool_req__docs_safety_security_relation
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the generalized safety/security classification consistency check
   across relations (source-owned and target-owned directions).


.. Setup: a QM feature used as belongs_to target for the component below.

.. feat:: Belongs-to target feature
   :id: feat__target_feat
   :version: 1
   :security: YES
   :safety: QM
   :status: valid



.. Negative Test (safety, source-owned): an ASIL feature includes a QM interface.
   `includes` is source-owned, so the ASIL source + QM target mismatch is flagged.

.. feat:: Feature with safety mismatch via includes
   :id: feat__asil_includes_qm
   :version: 1
   :security: YES
   :safety: ASIL_B
   :status: valid
   :includes: logic_arc_int__graph__qm_iface
   :expect: safety classification mismatch via `includes`



.. Setup: the QM interface targeted above.

.. logic_arc_int:: QM interface target
   :id: logic_arc_int__graph__qm_iface
   :version: 1
   :security: YES
   :safety: QM
   :status: valid



.. Negative Test (security, source-owned): a YES component implements a NO interface.
   `implements` is source-owned; the security mismatch is flagged.
   Both ends are QM so no safety flag is expected, only the security one.

.. comp:: Component with security mismatch via implements
   :id: comp__yes_implements_no
   :version: 1
   :security: YES
   :safety: QM
   :status: valid
   :belongs_to: feat__target_feat
   :implements: logic_arc_int__graph__no_iface
   :expect: security classification mismatch via `implements`



.. Setup: the NO interface targeted above.

.. logic_arc_int:: NO interface target
   :id: logic_arc_int__graph__no_iface
   :version: 1
   :security: NO
   :safety: QM
   :status: valid



.. Positive Test (matching): an ASIL feature includes an ASIL interface.
   Matching classifications are not flagged.

.. feat:: Feature with matching includes
   :id: feat__asil_includes_asil
   :version: 1
   :security: YES
   :safety: ASIL_B
   :status: valid
   :includes: logic_arc_int__graph__asil_iface
   :expect_not: mismatch



.. Setup: the ASIL interface targeted above.

.. logic_arc_int:: ASIL interface target
   :id: logic_arc_int__graph__asil_iface
   :version: 1
   :security: YES
   :safety: ASIL_B
   :status: valid
