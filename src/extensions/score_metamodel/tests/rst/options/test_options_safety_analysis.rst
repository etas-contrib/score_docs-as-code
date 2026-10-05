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
   :id: test_metadata__safety_analysis_options
   :partially_verifies_list: tool_req__docs_saf_attrs_sufficient
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the `sufficient` option of the safety-analysis types,
   the `violates` / `mitigated_by` link restrictions, the non-empty
   `content` check, and the security-analysis types (feat_sec_threat,
   feat_sec_ana).

.. Test if the `sufficient` option for Safety Analysis (FMEA and DFA) follows the pattern `^(yes|no)$`

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test_options__bad_1
   :sufficient: QM
   :expect: feat_saf_fmea__test_options__bad_1.sufficient (QM): does not follow pattern `^(yes|no)$`.



.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test_options__2
   :sufficient: yes
   :expect_not: does not follow pattern



.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test_options__3
   :sufficient: no
   :expect_not: does not follow pattern



.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test_options__bad_4
   :sufficient: QM
   :expect: comp_saf_fmea__test_options__bad_4.sufficient (QM): does not follow pattern `^(yes|no)$`.



.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test_options__5
   :sufficient: yes
   :expect_not: does not follow pattern



.. comp_saf_fmea:: This is a test
   :id: comp_saf_fmea__test_options__6
   :sufficient: no
   :expect_not: does not follow pattern



.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test_options__bad_7
   :sufficient: QM
   :expect: feat_saf_dfa__test_options__bad_7.sufficient (QM): does not follow pattern `^(yes|no)$`.



.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test_options__8
   :sufficient: yes
   :expect_not: does not follow pattern



.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test_options__9
   :sufficient: no
   :expect_not: does not follow pattern



.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test_options__bad_10
   :sufficient: QM
   :expect: feat_saf_dfa__test_options__bad_10.sufficient (QM): does not follow pattern `^(yes|no)$`.



.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test_options__11
   :sufficient: yes
   :expect_not: does not follow pattern



.. feat_saf_dfa:: This is a test
   :id: feat_saf_dfa__test_options__12
   :sufficient: no
   :expect_not: does not follow pattern



.. comp_saf_dfa:: This is a test
   :id: comp_saf_dfa__test_options__bad_13
   :sufficient: QM
   :expect: comp_saf_dfa__test_options__bad_13.sufficient (QM): does not follow pattern `^(yes|no)$`.



.. comp_saf_dfa:: This is a test
   :id: comp_saf_dfa__test_options__14
   :sufficient: yes
   :expect_not: does not follow pattern



.. comp_saf_dfa:: This is a test
   :id: comp_saf_dfa__test_options__15
   :sufficient: no
   :expect_not: does not follow pattern



.. Test that the `sufficient` option is case sensitive and does not accept values other than `yes` or `no`

.. feat_saf_fmea:: This is a test
   :id: feat_saf_fmea__test_options__bad_16
   :sufficient: yEs
   :expect: feat_saf_fmea__test_options__bad_16.sufficient (yEs): does not follow pattern `^(yes|no)$`.


..
   Support architecture views for the positive `violates` link tests below.

.. feat_arc_dyn:: This is a test
   :id: feat_arc_dyn__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern

.. feat_arc_sta:: This is a test
   :id: feat_arc_sta__test_good_1
   :status: valid
   :safety: QM
   :expect_not: does not follow pattern


.. comp_req:: Child requirement ASIL_B
   :id: comp_req__child__ASIL_B
   :safety: ASIL_B
   :status: valid



.. Negative Test: Linked to a non-allowed requirement type.

.. feat_saf_fmea:: Child requirement 25
   :id: feat_saf_fmea__child__25
   :status: valid
   :mitigated_by: comp_req__child__ASIL_B
   :expect: feat_saf_fmea__child__25: references 'comp_req__child__ASIL_B' as 'mitigated_by', but it must reference Feature Requirement (feat_req) or Assumption of Use Requirement (aou_req).



--- feat_saf_fmea violates begin ---

.. Negative Test: Linked to a non-allowed requirement type.

.. feat_saf_fmea:: Child requirement 26
   :id: feat_saf_fmea__child__26
   :violates: comp_req__child__ASIL_B
   :expect: feat_saf_fmea__child__26: references 'comp_req__child__ASIL_B' as 'violates', but it must reference Feature Sequence Diagram (feat_arc_dyn) or Feature & Feature Package Diagram (feat_arc_sta).

.. feat_saf_fmea can link either feat_arc_dyn or feat_arc_sta

.. Expect no errors related to "violates" field. We need to be generic for expect-not verifications.

.. feat_saf_fmea:: This requirement links a feat_arc_dyn
   :id: feat_saf_fmea__violate__dyn
   :violates: feat_arc_dyn__test_good_1
   :expect_not: violates


.. Expect no errors related to "violates" field. We need to be generic for expect-not verifications.

.. feat_saf_fmea:: This requirement links a feat_arc_sta
   :id: feat_saf_fmea__violate__sta
   :violates: feat_arc_sta__test_good_1
   :expect_not: violates

..
   Ensuring that non empty content is detected correctly


.. stkh_req:: This is a test
   :id: stkh_req__test_content
   :status: valid
   :safety: QM
   :expect_not: attribute: `content`

   Some content, to not trigger the warning


..
   This should not trigger, as 'std_wp' is not checked for content


.. std_wp:: This is a test
   :id: std_wp__test_content
   :expect_not: attribute: `content`



.. Security Analysis: feat_sec_threat



.. feat_sec_threat:: Missing threat_id
   :id: feat_sec_threat__test_options__bad_1
   :status: valid
   :expect: feat_sec_threat__test_options__bad_1: is missing required attribute: `threat_id`.

   Some content.




.. feat_sec_threat:: Invalid status
   :id: feat_sec_threat__test_options__bad_2
   :threat_id: MT_01_03
   :status: done
   :expect: feat_sec_threat__test_options__bad_2.status (done): does not follow pattern `^(valid|invalid)$`.

   Some content.




.. feat_sec_threat:: Valid threat
   :id: feat_sec_threat__test_options__ok_3
   :version: 1
   :threat_id: MT_01_03
   :status: valid
   :expect_not: feat_sec_threat__test_options__ok_3

   message timing is manipulated (Tampering)


.. Security Analysis: feat_sec_ana



.. feat_sec_ana:: Missing threat_scenario_id
   :id: feat_sec_ana__test_options__bad_4
   :status: invalid
   :sufficient: no
   :threat_effect: Unauthorized access to stored data.
   :expect: feat_sec_ana__test_options__bad_4: is missing required attribute: `threat_scenario_id`.

   Argument why mitigation is insufficient.




.. feat_sec_ana:: Invalid sufficient value
   :id: feat_sec_ana__test_options__bad_5
   :threat_scenario_id: SC_01_02
   :status: valid
   :sufficient: maybe
   :threat_effect: Unauthorized access to stored data.
   :expect: feat_sec_ana__test_options__bad_5.sufficient (maybe): does not follow pattern `^(yes|no)$`.

   Argument why mitigation is insufficient.




.. feat_sec_ana:: Invalid status value
   :id: feat_sec_ana__test_options__bad_6
   :threat_scenario_id: SC_01_02
   :status: done
   :sufficient: no
   :threat_effect: Unauthorized access to stored data.
   :expect: feat_sec_ana__test_options__bad_6.status (done): does not follow pattern `^(valid|invalid)$`.

   Argument why mitigation is insufficient.




.. feat_sec_ana:: Missing threat_effect
   :id: feat_sec_ana__test_options__bad_7
   :threat_scenario_id: SC_01_02
   :status: invalid
   :sufficient: no
   :expect: feat_sec_ana__test_options__bad_7: is missing required attribute: `threat_effect`.

   Argument why mitigation is insufficient.




.. feat_sec_ana:: Valid threat scenario
   :id: feat_sec_ana__test_options__ok_8
   :version: 1
   :threat_scenario_id: SC_01_02
   :status: valid
   :sufficient: yes
   :threat_effect: Unauthorized access to stored data.
   :expect_not: feat_sec_ana__test_options__ok_8

   Mitigation is sufficient because access controls are in place.




.. feat_sec_ana:: Valid threat scenario with optional mitigation_issue
   :id: feat_sec_ana__test_options__ok_9
   :version: 1
   :threat_scenario_id: SC_01_03
   :status: invalid
   :sufficient: no
   :threat_effect: Data integrity violation via tampering.
   :mitigation_issue: https://github.com/eclipse-score/score/issues/1
   :expect_not: feat_sec_ana__test_options__ok_9

   Mitigation not yet implemented.




.. feat_sec_ana:: Invalid mitigation_issue (pull request, not issue)
   :id: feat_sec_ana__test_options__bad_10
   :threat_scenario_id: SC_01_04
   :status: invalid
   :sufficient: no
   :threat_effect: Unauthorized data access.
   :mitigation_issue: https://github.com/eclipse-score/docs-as-code/pull/508
   :expect: feat_sec_ana__test_options__bad_10.mitigation_issue (https://github.com/eclipse-score/docs-as-code/pull/508): does not follow pattern

   Mitigation not yet implemented.




.. feat_sec_ana:: Missing argument content
   :id: feat_sec_ana__test_options__bad_11
   :threat_scenario_id: SC_01_04
   :status: invalid
   :sufficient: no
   :threat_effect: Unauthorized data access.
   :expect: feat_sec_ana__test_options__bad_11: is missing required attribute: `content`.
