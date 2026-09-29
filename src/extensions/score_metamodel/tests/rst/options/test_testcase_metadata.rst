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
   :id: test_metadata__testcase_metadata
   :fully_verifies_list:
      tool_req__docs_test_metadata_mandatory_1,
      tool_req__docs_test_metadata_mandatory_2,
      tool_req__docs_test_metadata_link_levels
   :test_type: requirements_based
   :derivation_technique: requirements_based

   Tests the Testcase metadata checks:
   - `test_type` and `derivation_technique` are mandatory (mandatory_1)
   - the description (`content`) must not be empty (mandatory_2)
   - `fully_verifies` / `partially_verifies` links must match the
     `test_level` (link_levels)


.. The requirement needs below are the link targets of the testcase needs.

.. feat_req:: Target Feature Requirement
   :id: feat_req__tc_metadata__target
   :version: 1

   A feature requirement used as a valid link target for feature
   integration test cases.

.. comp_req:: Target Component Requirement
   :id: comp_req__tc_metadata__target
   :version: 1

   A component requirement used as a valid link target for component
   integration and unit test cases.


.. Positive: A feature integration test case with all mandatory metadata
.. and a feature requirement target.

.. testcase:: Feature Integration Test Case (valid)
   :id: testcase__tc_metadata__fit_ok
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :test_level: feature_integration_test
   :fully_verifies: feat_req__tc_metadata__target
   :expect_not: is missing required attribute, does not follow pattern, may only link to

   Runs the target feature requirement.

.. Negative: `test_type` is missing.

.. testcase:: Feature Integration Test Case (missing test_type)
   :id: testcase__tc_metadata__fit_no_test_type
   :version: 1
   :derivation_technique: requirements-analysis
   :test_level: feature_integration_test
   :fully_verifies: feat_req__tc_metadata__target
   :expect: testcase__tc_metadata__fit_no_test_type: is missing required attribute: `test_type`.

   Runs the target feature requirement.

.. Negative: `derivation_technique` is missing.

.. testcase:: Feature Integration Test Case (missing derivation_technique)
   :id: testcase__tc_metadata__fit_no_derivation
   :version: 1
   :test_type: requirements-based
   :test_level: feature_integration_test
   :fully_verifies: feat_req__tc_metadata__target
   :expect: testcase__tc_metadata__fit_no_derivation: is missing required attribute: `derivation_technique`.

   Runs the target feature requirement.

.. Negative: the description (`content`) is missing.

.. testcase:: Feature Integration Test Case (missing content)
   :id: testcase__tc_metadata__fit_no_content
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :test_level: feature_integration_test
   :fully_verifies: feat_req__tc_metadata__target
   :expect: testcase__tc_metadata__fit_no_content: is missing required attribute: `content`.

.. Negative: a feature integration test must not link to a component requirement.

.. testcase:: Feature Integration Test Case (comp_req target)
   :id: testcase__tc_metadata__fit_cross
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :test_level: feature_integration_test
   :fully_verifies: comp_req__tc_metadata__target
   :expect: testcase__tc_metadata__fit_cross: fully_verifies links to `comp_req__tc_metadata__target` (comp_req), but a `feature_integration_test` test case may only link to feat_req.

   Runs the target component requirement.

.. Positive: A component integration test case with a component requirement target.

.. testcase:: Component Integration Test Case (valid)
   :id: testcase__tc_metadata__cit_ok
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :test_level: component_integration_test
   :partially_verifies: comp_req__tc_metadata__target
   :expect_not: is missing required attribute, does not follow pattern, may only link to

   Runs the target component requirement.

.. Negative: a component integration test must not link to a feature requirement.

.. testcase:: Component Integration Test Case (feat_req target)
   :id: testcase__tc_metadata__cit_cross
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :test_level: component_integration_test
   :fully_verifies: feat_req__tc_metadata__target
   :expect: testcase__tc_metadata__cit_cross: fully_verifies links to `feat_req__tc_metadata__target` (feat_req), but a `component_integration_test` test case may only link to comp_req.

   Runs the target feature requirement.

.. Positive: A unit test case with a component requirement target.

.. testcase:: Unit Test Case (valid)
   :id: testcase__tc_metadata__unit_ok
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :test_level: unit_test
   :fully_verifies: comp_req__tc_metadata__target
   :expect_not: is missing required attribute, does not follow pattern, may only link to

   Runs the target component requirement.

.. Negative: a unit test must not link to a feature requirement.

.. testcase:: Unit Test Case (feat_req target)
   :id: testcase__tc_metadata__unit_cross
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :test_level: unit_test
   :partially_verifies: feat_req__tc_metadata__target
   :expect: testcase__tc_metadata__unit_cross: partially_verifies links to `feat_req__tc_metadata__target` (feat_req), but a `unit_test` test case may only link to comp_req.

   Runs the target feature requirement.

.. Positive: Without a `test_level` no link level is enforced.

.. testcase:: Test Case without test_level
   :id: testcase__tc_metadata__no_level
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :fully_verifies: feat_req__tc_metadata__target
   :expect_not: is missing required attribute, does not follow pattern, may only link to

   Runs the target feature requirement.

.. Negative: `test_level` must be one of the allowed values.

.. testcase:: Test Case with invalid test_level
   :id: testcase__tc_metadata__bad_level
   :version: 1
   :test_type: requirements-based
   :derivation_technique: requirements-analysis
   :test_level: integration_test
   :expect: testcase__tc_metadata__bad_level.test_level (integration_test): does not follow pattern `^(feature_integration_test|component_integration_test|unit_test)$`.

   Runs the target feature requirement.
