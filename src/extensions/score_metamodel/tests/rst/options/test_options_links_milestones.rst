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
   :id: test_metadata__links_and_milestones
   :partially_verifies_list: tool_req__docs_req_types[version==1]
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the required options and links of the requirement types
   (std_wp/stkh_req/feat_req), the `mod` maturity option,
   the `fulfils` link and the milestone (`valid_from` / `valid_until`)
   value checks.


..
   Required option: `status` is missing

.. std_wp:: This is a test
   :id: std_wp__test__abcd
   :expect: std_wp__test__abcd: is missing required attribute: `status`.



.. All required options are present

.. std_wp:: This is a test
   :id: std_wp__test_options__abce
   :status: active
   :version: 1
   :expect_not: attribute



.. Required link `derived_from` refers to wrong requirement type

.. feat_req:: Child requirement
   :id: feat_req__abce
   :derived_from: std_wp__test_options__abce
   :expect: feat_req__abce: references 'std_wp__test_options__abce' as 'derived_from', but it must reference Stakeholder Requirement (stkh_req).



.. All required links are present

.. feat_req:: Child requirement
   :id: feat_req__abcg
   :derived_from: stkh_req__abcd
   :satisfied_by: feat__abcg
   :expect_not: feat_req__abcg: is missing required link

.. stkh_req:: Parent requirement
   :id: stkh_req__abcd



.. Test if the optional `maturity` option for `mod` follows the pattern `^(preview|experimental|release)$`

.. mod:: Test Module Maturity Bad
   :id: mod__test_options__maturity_bad
   :maturity: stable
   :expect: mod__test_options__maturity_bad.maturity (stable): does not follow pattern `^(preview|experimental|release)$`.



.. mod:: Test Module Maturity Good
   :id: mod__test_options__maturity_good
   :maturity: preview
   :expect_not: does not follow pattern

.. comp_req:: Child requirement ASIL_B
   :id: comp_req__child__ASIL_B
   :safety: ASIL_B
   :status: valid


.. Positive Test: fulfils is optional for static views, an unlinked feat_arc_sta is accepted.

.. feat_arc_sta:: Static view without fulfils
   :id: feat_arc_sta__fulfils__optional
   :status: valid
   :safety: ASIL_B
   :security: YES
   :expect_not: is missing required link: `fulfils`


.. Negative Test: when fulfils is present, its target type is still restricted.

.. feat_arc_sta:: Static view with invalid fulfils target
   :id: feat_arc_sta__fulfils__bad_target
   :status: valid
   :safety: ASIL_B
   :security: YES
   :fulfils: comp_req__child__ASIL_B
   :expect: feat_arc_sta__fulfils__bad_target: references 'comp_req__child__ASIL_B' as 'fulfils', but it must reference Feature Requirement (feat_req) or Assumption of Use Requirement (aou_req).
.. Tests if the attribute `safety` follows the pattern `^(QM|ASIL_B)$`

.. document:: This is a test document
   :id: doc__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern


.. document:: This is a test document
   :id: doc__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern


.. Tests if the attribute `status` follows the pattern `^(valid|draft|invalid)$`

.. document:: This is a test document
   :id: doc__test_good_3
   :status: draft
   :safety: QM
   :expect_not: does not follow pattern



.. document:: This is a test document
   :id: doc__test_bad_status_1
   :status: active
   :safety: QM
   :expect: doc__test_bad_status_1.status (active): does not follow pattern `^(valid|draft|invalid)$`.,
      doc__test_bad_status_1: is missing required attribute: `security`.,
      doc__test_bad_status_1: is missing required link: `realizes`.




.. stkh_req:: This is a test
   :id: stkh_req__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern




.. stkh_req:: This is a test
   :id: stkh_req__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. feat_req:: This is a test
   :id: feat_req__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern




.. feat_req:: This is a test
   :id: feat_req__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. comp_req:: This is a test
   :id: comp_req__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern




.. comp_req:: This is a test
   :id: comp_req__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. tool_req:: This is a test
   :id: tool_req__test_good_1
   :status: valid
   :safety: QM
   :satisfies: comp_req__test_good_1
   :expect_not: does not follow pattern





.. tool_req:: This is a test
   :id: tool_req__test_good_2
   :status: valid
   :safety: ASIL_B
   :satisfies: comp_req__test_good_2
   :expect_not: does not follow pattern




.. aou_req:: This is a test
   :id: aou_req__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern




.. aou_req:: This is a test
   :id: aou_req__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. feat_arc_sta:: This is a test
   :id: feat_arc_sta__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern



.. feat_arc_sta:: This is a test
   :id: feat_arc_sta__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. feat_arc_dyn:: This is a test
   :id: feat_arc_dyn__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern





.. feat_arc_dyn:: This is a test
   :id: feat_arc_dyn__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. logic_arc_int:: This is a test
   :id: logic_arc_int__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern





.. logic_arc_int:: This is a test
   :id: logic_arc_int__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. logic_arc_int_op:: This is a test
   :id: logic_arc_int_op__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern




.. logic_arc_int_op:: This is a test
   :id: logic_arc_int_op__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. comp_arc_sta:: This is a test
   :id: comp_arc_sta__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern




.. comp_arc_sta:: This is a test
   :id: comp_arc_sta__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. comp_arc_dyn:: This is a test
   :id: comp_arc_dyn__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern




.. comp_arc_dyn:: This is a test
   :id: comp_arc_dyn__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern





.. real_arc_int:: This is a test
   :id: real_arc_int__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern




.. real_arc_int:: This is a test
   :id: real_arc_int__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern




.. real_arc_int_op:: This is a test
   :id: real_arc_int_op__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern



.. real_arc_int_op:: This is a test
   :id: real_arc_int_op__test_good_2
   :status: valid
   :safety: ASIL_B
   :expect_not: does not follow pattern



.. feat_req:: milestone must be a version
   :id: feat_req__random_id3
   :valid_from: 2035-03
   :expect: feat_req__random_id3.valid_from (2035-03): does not follow pattern




.. feat_req:: milestone must be a version
   :id: feat_req__random_id4
   :valid_until: 2035-03
   :expect: feat_req__random_id4.valid_until (2035-03): does not follow pattern


