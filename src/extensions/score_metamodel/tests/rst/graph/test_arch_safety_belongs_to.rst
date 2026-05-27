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

#CHECK: check_metamodel_graph

.. feat:: QM Feature Parent
   :id: feat__test__qm_parent
   :safety: QM
   :security: NO
   :status: valid

.. feat:: Safety Feature Parent
   :id: feat__test__asil_parent
   :safety: ASIL_B
   :security: NO
   :status: valid

.. comp:: QM Component Parent
   :id: comp__test__qm_parent
   :safety: QM
   :security: NO
   :status: valid
   :belongs_to: feat__test__qm_parent

.. comp:: Safety Component Parent
   :id: comp__test__asil_parent
   :safety: ASIL_B
   :security: NO
   :status: valid
   :belongs_to: feat__test__asil_parent


.. Negative Test: Safety feat_arc_sta belongs_to a QM feat — should warn.
#EXPECT: feat_arc_sta__test__safety_to_qm: Parent need `feat__test__qm_parent` does not fulfill condition `safety != QM`.

.. feat_arc_sta:: Safety view with QM parent
   :id: feat_arc_sta__test__safety_to_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :belongs_to: feat__test__qm_parent


.. Positive Test: Safety feat_arc_sta belongs_to a safety feat — should not warn.
#EXPECT-NOT: Safety architecture views must belong to safety architecture elements

.. feat_arc_sta:: Safety view with safety parent
   :id: feat_arc_sta__test__safety_to_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :belongs_to: feat__test__asil_parent


.. Positive Test: QM feat_arc_sta — check does not apply to QM elements.
#EXPECT-NOT: Safety architecture views must belong to safety architecture elements

.. feat_arc_sta:: QM view with QM parent
   :id: feat_arc_sta__test__qm_to_qm
   :safety: QM
   :security: NO
   :status: valid
   :belongs_to: feat__test__qm_parent


.. Negative Test: Safety comp_arc_sta belongs_to a QM comp — should warn.
#EXPECT: comp_arc_sta__test__safety_to_qm: Parent need `comp__test__qm_parent` does not fulfill condition `safety != QM`.

.. comp_arc_sta:: Safety component view with QM parent
   :id: comp_arc_sta__test__safety_to_qm
   :safety: ASIL_B
   :security: NO
   :status: valid
   :belongs_to: comp__test__qm_parent


.. Positive Test: Safety comp_arc_sta belongs_to a safety comp — should not warn.
#EXPECT-NOT: Safety architecture views must belong to safety architecture elements

.. comp_arc_sta:: Safety component view with safety parent
   :id: comp_arc_sta__test__safety_to_asil
   :safety: ASIL_B
   :security: NO
   :status: valid
   :belongs_to: comp__test__asil_parent
