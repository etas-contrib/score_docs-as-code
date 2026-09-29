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
   :id: test_metadata__arch_link_safety_to_req
   :fully_verifies_list: tool_req__docs_arch_link_safety_to_req[version==2]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests that architecture elements (feat_arc_sta, logic_arc_int, comp_arc_sta,
   real_arc_int, comp) with safety != QM are linked via ``fulfils`` to at least
   one requirement with the exact same safety value.  For each architecture type:
   - a safety element linked to a same-safety requirement builds without a warning
   - a safety element without a same-safety fulfils link triggers a warning
   - a QM element is exempt from the check


.. Setup: link targets used by the tests below.

.. feat:: Supporting feature
   :id: feat__saf2req
   :security: NO
   :safety: QM
   :status: valid


.. comp:: Supporting component
   :id: comp__saf2req
   :security: NO
   :safety: QM
   :status: valid
   :belongs_to: feat__saf2req


.. logic_arc_int:: Includes target for static feature views
   :id: logic_arc_int__saf2req__target
   :security: NO
   :safety: QM
   :status: valid


.. feat_req:: ASIL_B feature requirement
   :id: feat_req__saf2req__asil
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__saf2req

   ASIL_B feature requirement.


.. feat_req:: QM feature requirement
   :id: feat_req__saf2req__qm
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :valid_from: v1.0
   :satisfied_by: feat__saf2req

   QM feature requirement.


.. comp_req:: ASIL_B component requirement
   :id: comp_req__saf2req__asil
   :reqtype: Functional
   :security: NO
   :safety: ASIL_B
   :status: valid
   :satisfied_by: comp__saf2req

   ASIL_B component requirement.


.. comp_req:: QM component requirement
   :id: comp_req__saf2req__qm
   :reqtype: Functional
   :security: NO
   :safety: QM
   :status: valid
   :satisfied_by: comp__saf2req

   QM component requirement.


.. aou_req:: ASIL_B assumption of use
   :id: aou_req__saf2req__asil
   :reqtype: Non-Functional
   :security: NO
   :safety: ASIL_B
   :status: valid

   ASIL_B assumption of use.


.. Positive: safety (ASIL_B) logic interface fulfils an ASIL_B feature requirement.

.. logic_arc_int:: Safety logic interface with matching requirement
   :id: logic_arc_int__saf2req__good
   :security: NO
   :safety: ASIL_B
   :status: valid
   :fulfils: feat_req__saf2req__asil
   :expect_not: no fulfils link


.. Negative: safety logic interface without any fulfils link.

.. logic_arc_int:: Safety logic interface without requirement
   :id: logic_arc_int__saf2req__missing
   :security: NO
   :safety: ASIL_B
   :status: valid
   :expect: no fulfils link to a requirement with the same safety value


.. Negative: safety logic interface fulfilling only a QM requirement.

.. logic_arc_int:: Safety logic interface with QM requirement only
   :id: logic_arc_int__saf2req__bad_target
   :security: NO
   :safety: ASIL_B
   :status: valid
   :fulfils: feat_req__saf2req__qm
   :expect: no fulfils link to a requirement with the same safety value


.. Exempt: QM logic interface is not selected by the check.

.. logic_arc_int:: QM logic interface
   :id: logic_arc_int__saf2req__qm
   :security: NO
   :safety: QM
   :status: valid
   :expect_not: no fulfils link


.. Positive: safety feature static view fulfils an ASIL_B feature requirement.

.. feat_arc_sta:: Safety feature static view with matching requirement
   :id: feat_arc_sta__saf2req__good
   :security: NO
   :safety: ASIL_B
   :status: valid
   :includes: logic_arc_int__saf2req__target
   :belongs_to: feat__saf2req
   :fulfils: feat_req__saf2req__asil
   :expect_not: no fulfils link


.. Negative: safety feature static view without any fulfils link.

.. feat_arc_sta:: Safety feature static view without requirement
   :id: feat_arc_sta__saf2req__missing
   :security: NO
   :safety: ASIL_B
   :status: valid
   :includes: logic_arc_int__saf2req__target
   :belongs_to: feat__saf2req
   :expect: no fulfils link to a requirement with the same safety value


.. Positive: safety component static view fulfils an ASIL_B component requirement.

.. comp_arc_sta:: Safety component static view with matching requirement
   :id: comp_arc_sta__saf2req__good
   :security: NO
   :safety: ASIL_B
   :status: valid
   :belongs_to: comp__saf2req
   :fulfils: comp_req__saf2req__asil
   :expect_not: no fulfils link


.. Negative: safety component static view without any fulfils link.

.. comp_arc_sta:: Safety component static view without requirement
   :id: comp_arc_sta__saf2req__missing
   :security: NO
   :safety: ASIL_B
   :status: valid
   :belongs_to: comp__saf2req
   :expect: no fulfils link to a requirement with the same safety value


.. Positive: safety interface fulfils an ASIL_B component requirement.

.. real_arc_int:: Safety interface with matching requirement
   :id: real_arc_int__saf2req__good
   :security: NO
   :safety: ASIL_B
   :status: valid
   :language: cpp
   :fulfils: comp_req__saf2req__asil
   :expect_not: no fulfils link


.. Negative: safety interface without any fulfils link.

.. real_arc_int:: Safety interface without requirement
   :id: real_arc_int__saf2req__missing
   :security: NO
   :safety: ASIL_B
   :status: valid
   :language: cpp
   :expect: no fulfils link to a requirement with the same safety value


.. Positive: safety component fulfils an ASIL_B assumption of use.

.. comp:: Safety component with matching assumption of use
   :id: comp__saf2req__good
   :security: NO
   :safety: ASIL_B
   :status: valid
   :belongs_to: feat__saf2req
   :fulfils: aou_req__saf2req__asil
   :expect_not: no fulfils link


.. Negative: safety component without any fulfils link.

.. comp:: Safety component without requirement
   :id: comp__saf2req__missing
   :security: NO
   :safety: ASIL_B
   :status: valid
   :belongs_to: feat__saf2req
   :expect: no fulfils link to a requirement with the same safety value
