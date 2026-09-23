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

Doc-as-Code Tool Verification Report
====================================

This page is the authoritative Tool Verification Report for the S-CORE Docs-as-Code tool. It records the classification of intended usage, potential malfunctions, safety impact and detection, together with qualification evidence and lifecycle state.

Tool under evaluation
---------------------

The S-CORE Docs-as-Code tool (Bazel module ``score_docs_as_code``) builds HTML
documentation and traceability data from RST/Markdown sources. It evaluates
those sources with the S-CORE extensions and metamodel, and produces the
generated documentation, ``needs.json`` and ``metrics.json`` used by the
downstream process.

Report record
-------------

.. doc_tool:: Doc-as-Code
   :id: doc_tool__score_docs_as_code
   :status: evaluated
   :version: 3
   :tool_version: v8.1.2
   :security_affected: YES
   :realizes: wp__tool_verification_report[version==1]
   :post_template: tool_qualification_report

Details
-------


.. tool_usecase:: Build/CI behavior
   :id: tool_usecase__docs_as_code__build_ci
   :belongs_to: doc_tool__score_docs_as_code
   :realized_by:
      tool_req__docs_doc_types,
      tool_req__docs_common_attr_safety_link_check,
      tool_req__docs_test_linkage_metrics,
      tool_req__docs_test_link_testcase,
      tool_req__docs_req_link_covers_aou
   :version: 1

   Builds run with ``-W``; any warning trips CI. The
   safety-relevant danger is the *silent* failure — a missing warning
   or a wrong output published undetected.
   A loud CI abort is safe: no wrong output enters the baseline.

   .. potential_tool_malfunction:: Document metamodel enforcement
      :id: potential_tool_malfunction__docs_as_code__m1
      :safety_affected: YES
      :detection_sufficient: NO
      :safety_measures: PR review
      :violates:
         tool_req__docs_doc_types,
         tool_req__docs_doc_generic_mandatory,
         tool_req__docs_common_attr_id,
         tool_req__docs_common_attr_id_scheme,
         tool_req__docs_common_attr_status,
         tool_req__docs_common_attr_description,
         tool_req__docs_common_attr_title,
         tool_req__docs_common_attr_desc_wording,
         tool_req__docs_common_attr_security,
         tool_req__docs_common_attr_safety,
         tool_req__docs_common_attr_version,
         tool_req__docs_common_attr_suspicious,
         tool_req__docs_req_attr_rationale,
         tool_req__docs_req_attr_reqtype,
         tool_req__docs_req_attr_testcov,
         tool_req__docs_req_attr_validity_correctness,
         tool_req__docs_req_attr_validity_consistency,
         tool_req__arch_linkage_safety,
         tool_req__arch_consistency_interf,
         tool_req__docs_tvr_safety,
         tool_req__docs_tvr_security,
         tool_req__docs_tvr_status,
         tool_req__docs_tvr_version,
         tool_req__docs_tvr_confidence_level,
         tool_req__docs_saf_attrs_mitigated_by,
         tool_req__docs_saf_attrs_mitigation_issue,
         tool_req__docs_saf_attrs_sufficient,
         tool_req__docs_saf_attrs_sufficient_check,
         tool_req__docs_saf_attrs_content,
         tool_req__docs_saf_attrs_violates,
         tool_req__docs_saf_attr_fmea_fault_id,
         tool_req__docs_saf_attr_fmea_failure_effect
      :version: 1

      **Document metamodel enforcement** — enforce document types, mandatory attributes (id, status, security, safety, realizes), etc.
      See, for example, :need:`gd_req__doc_attr_status`, :need:`gd_req__req_attr_uid`, :need:`gd_req__req_attr_safety`, :need:`gd_req__arch_attr_safety`, :need:`gd_req__req_check_mandatory`.

      **Silent false-negative**: too-permissive
      ``metamodel.yaml`` regex accepted with no guard, or a check bug skips a case.

      Impact on safety: yes.
      Impact safety measures available: yes: PR review.
      Impact safety detection sufficient: no: Qualify metamodel enforcement.
      Further additional safety measure required: yes (qualification).
      Confidence (automatic calculation): low.

   .. potential_tool_malfunction:: Safety-critical linking enforcement
      :id: potential_tool_malfunction__docs_as_code__m2
      :safety_affected: YES
      :detection_sufficient: NO
      :safety_measures: PR review
      :violates:
         tool_req__docs_common_attr_safety_link_check,
         tool_req__docs_req_arch_link_safety_to_arch,
         tool_req__docs_req_link_satisfies_allowed,
         tool_req__docs_req_link_covers_aou,
         tool_req__docs_arch_link_fulfils,
         tool_req__docs_arch_link_fulfils_aou,
         tool_req__docs_arch_link_aou_check,
         tool_req__docs_arch_link_safety_to_req,
         tool_req__docs_arch_link_security
      :version: 1

      **Safety-critical linking enforcement**.
      See :need:`gd_req__req_linkage_safety`.

      **Silent false-negative**: allow links which cannot be safe derivations.

      Impact on safety: yes.
      Impact safety measures available: yes: PR review.
      Impact safety detection sufficient: no: Qualify graph checks.
      Further additional safety measure required: yes (qualification).

      The clearest gap is ``satisfied_by`` (and arguably ``covers``), which carry the same "target at least as safe" obligation as the checked ``fulfils``/``implements`` yet are unconstrained.

      Confidence (automatic calculation): low.

   .. potential_tool_malfunction:: Requirements coverage statistics
      :id: potential_tool_malfunction__docs_as_code__m3
      :safety_affected: YES
      :detection_sufficient: NO
      :violates:
         tool_req__docs_test_linkage_metrics,
         tool_req__docs_verification_report_need
      :version: 1

      **Requirements coverage statistics** — count, per requirement type, the requirements carrying a ``testlink``, compute link-coverage percentages.
      See :need:`gd_req__verification_reporting`.

      **Silent wrong-output**: a coverage statistic computed wrong.

      Impact on safety: yes.
      Impact safety measures available: no.
      Impact safety detection sufficient: no: Qualify coverage statistics.
      Further additional safety measure required: yes (qualification).
      Confidence (automatic calculation): low.

   .. potential_tool_malfunction:: Test linkage
      :id: potential_tool_malfunction__docs_as_code__m5
      :safety_affected: YES
      :detection_sufficient: NO
      :violates:
         tool_req__docs_test_link_testcase,
         tool_req__docs_test_linkage_metrics,
         tool_req__docs_verification_report_need,
         tool_req__docs_test_metadata_mandatory_1,
         tool_req__docs_test_metadata_mandatory_2,
         tool_req__docs_test_metadata_link_levels
      :version: 1

      **Test linkage** — for each ``testcase`` need, resolve its ``partially_verifies``/``fully_verifies`` references against the needs set.
      See :need:`gd_req__req_attr_testlink`, :need:`gd_req__verification_reporting`.

      **Silent wrong-output**:
      Safety case believes the requirement is tested where it is not.

      Impact on safety: yes.
      Impact safety measures available: no.
      Impact safety detection sufficient: no: Qualify linkage statistics.
      Further additional safety measure required: yes (qualification).
      Confidence (automatic calculation): low.

   .. potential_tool_malfunction:: Test reference check
      :id: potential_tool_malfunction__docs_as_code__m6
      :safety_affected: YES
      :detection_sufficient: NO
      :safety_measures: PR review
      :violates: tool_req__docs_test_link_testcase
      :version: 1

      **Test reference check**.
      See :need:`gd_req__req_attr_testlink`.

      **Silent wrong-output**:
      Test references an outdated/missing requirement.

      Impact on safety: yes.
      Impact safety measures available: yes: PR review.
      Impact safety detection sufficient: no: Qualify test reference check.
      Further additional safety measure required: yes (qualification).
      Confidence (automatic calculation): low.

   .. potential_tool_malfunction:: Listing assumptions of use
      :id: potential_tool_malfunction__docs_as_code__m7
      :safety_affected: YES
      :detection_sufficient: NO
      :safety_measures: PR review
      :violates:
         tool_req__docs_req_types,
         tool_req__docs_req_link_covers_aou,
         tool_req__docs_arch_link_fulfils_aou
      :version: 1

      **Listing assumptions of use** — safety manuals use ``needtable`` to communicate safety-critical assumptions of use to users.
      See :need:`gd_guidl__saf_man`, :need:`wp__platform_safety_manual`.

      **Silent wrong-output**: ``aou_req`` items might be missing or wrong.

      Impact on safety: yes.
      Impact safety measures available: yes: PR review.
      Impact safety detection sufficient: no: Qualify ``needtable``.
      Further additional safety measure required: yes: qualification.
      Confidence (automatic calculation): low.

.. tool_usecase:: PR Review
   :id: tool_usecase__docs_as_code__pr_review
   :belongs_to: doc_tool__score_docs_as_code
   :realized_by: tool_req__docs_doc_types
   :version: 1

   Repository contents are the source of truth
   and every change is reviewed by a committer
   (:need:`rl__committer`, :need:`doc_concept__wp_inspections`).
   Still, for silent wrong outputs the gated CI stays green.

.. tool_usecase:: Derived-view
   :id: tool_usecase__docs_as_code__derived_view
   :belongs_to: doc_tool__score_docs_as_code
   :realized_by:
      tool_req__docs_arch_views,
      tool_req__docs_verification_report_need,
      tool_req__docs_req_link_satisfies_allowed
   :version: 1

   The rendered HTML output is a derived view;
   the authoritative safety artifacts are mostly the source-controlled work products.
   There are two exceptions, the architecture views (see M4) and backlinks (see M8).
   Rendering/preview defects affect reviewer convenience, not safety evidence.

   .. potential_tool_malfunction:: Architecture visualization
      :id: potential_tool_malfunction__docs_as_code__m4
      :safety_affected: YES
      :detection_sufficient: YES
      :safety_measures: PR review includes architecture inspection
      :violates: tool_req__docs_arch_views
      :version: 1

      **Architecture visualization** — generate architecture diagrams.
      See :need:`gd_req__arch_viewpoints`.

      **Silent wrong-output**: a diagram misrepresents the architecture.

      Impact on safety: yes.
      Impact safety measures available: yes: PR review includes architecture inspection.
      Impact safety detection sufficient: yes.
      Further additional safety measure required: no.
      Confidence (automatic calculation): high.

   .. potential_tool_malfunction:: Backlinks
      :id: potential_tool_malfunction__docs_as_code__m8
      :safety_affected: YES
      :detection_sufficient: NO
      :violates: tool_req__docs_req_link_satisfies_allowed
      :version: 1

      **Backlinks** — for bi-directional traceability, generate correct backlinks for links between Needs items.
      See :need:`doc_concept__general_traceability`.

      **Silent wrong-output**: generated backlinks are wrong or missing.

      Impact on safety: yes.
      Impact safety measures available: no.
      Impact safety detection sufficient: no: Qualify backlinks in HTML.
      Further additional safety measure required: yes (qualification).
      Confidence (automatic calculation): low.

   .. potential_tool_malfunction:: Documentation generation
      :id: potential_tool_malfunction__docs_as_code__m9
      :safety_affected: NO
      :violates: tool_req__docs_doc_types
      :version: 1

      **Documentation generation** — apart from the aspects **not covered by previous malfunctions**.
      See :need:`gd_req__doc_attributes_manual`, :need:`gd_req__doc_attr_status`.

      Incomplete, outdated, or mis-rendered HTML.

      Impact on safety: no: rendered-view defects affect reviewer convenience,
      not safety evidence.
      Impact safety measures available: no.
      Impact safety detection sufficient: not applicable for a non-safety malfunction.
      Further additional safety measure required: no.
      Confidence (automatic calculation): high.

Security evaluation
-------------------
The threat model reduces to a single class: **source tampering**. The tool has
no runtime attack surface — it is a build-time Sphinx extension reading
source-controlled inputs and writing generated output.

.. list-table:: S-CORE Docs-as-Code security evaluation
   :header-rows: 1
   :widths: 1 2 8 2 6 4 2

   * - Threat identification
     - Use case description
     - Threats
     - Impact on security?
     - Impact security measures available?
     - Impact security detection sufficient?
     - Further additional security measure required?
   * - T1
     - | **Source tampering** — applies to all tool use cases.
       | See :need:`gd_req__req_attr_security`, :need:`gd_req__arch_attr_security`, :need:`gd_req__req_linkage`,
       | :need:`gd_req__req_traceability`, :need:`gd_req__arch_linkage_security_trace`.
     - | An attacker with write access tampers with sources, configuration, or
       | extension code to weaken/disable security checks or inject misleading
       | content into published output.
     - yes
     - yes: PR review.
     - yes
     - no
