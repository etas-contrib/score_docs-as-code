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

Doc-as-Code Tool Evaluation and Classification
==============================================

This page records the evaluation of the docs-as-code tool in the usage
contexts on which the project relies. It is the classification part of the
Tool Verification Report. The resulting qualification evidence and lifecycle
state are described in :doc:`qualification`.

Introduction
------------

Scope and purpose
~~~~~~~~~~~~~~~~~

The S-CORE Docs-as-Code tool (Bazel module ``score_docs_as_code``) builds HTML
documentation from RST/Markdown sources — process description, requirements, and
traceability — and validates content against the S-CORE metamodel.

Inputs and outputs
~~~~~~~~~~~~~~~~~~

* **Inputs:** RST/Markdown sources, Sphinx configuration (``conf.py``), the S-CORE
  metamodel (``metamodel.yaml``), Bazel build files, source-code links
  (``sourcelinks_json``) and test results (``testlinks``).
* **Outputs:** HTML documentation (``_build/``), needs/traceability data
  (``needs.json``), coverage/linkage statistics (``metrics.json``).

.. mermaid::

   graph LR
      src@{ shape: docs, label: "RST/Markdown sources (+ assets)" }
      code@{ shape: docs, label: "C++/Rust/Python sources" }
      srclinks@{ shape: doc, label: "sourcelinks" }
      cfg@{ shape: docs, label: "Config (conf.py, metamodel.yaml, Bazel)" }
      tests@{ shape: docs, label: "Test results" }
      dac@{ shape: subproc, label: "Doc-as-Code" }
      html@{ shape: docs, label: "HTML docs" }
      needs@{ shape: doc, label: "needs.json" }
      metrics@{ shape: docs, label: "metrics.json" }

      src --> dac
      code --> srclinks --> dac
      cfg --> dac
      tests --> dac
      dac --> html
      dac --> needs
      dac --> metrics

Available information
~~~~~~~~~~~~~~~~~~~~~
* Repository: https://github.com/eclipse-score/docs-as-code
* Documentation: https://eclipse-score.github.io/docs-as-code/v8.1.2/
* Bazel module name: ``score_docs_as_code``

Installation and integration
----------------------------

Installation
~~~~~~~~~~~~

The tool is consumed as a Bazel module. Declare the dependency in
``MODULE.bazel``::

    bazel_dep(name = "score_docs_as_code", version = "8.1.2")

and the S-CORE registry in ``.bazelrc``::

    common --registry=https://raw.githubusercontent.com/eclipse-score/bazel_registry/main/
    common --registry=https://bcr.bazel.build

Invoke the ``docs()`` macro from the root ``BUILD`` file::

    load("@score_docs_as_code//:docs.bzl", "docs")
    docs(
        project = "My Project",
        project_url = "https://github.com/eclipse-score/my-project",
        source_dir = "docs",
    )

For local development, ``bazel run //:ide_support`` creates a Python virtual
environment (``.venv_docs``) with all Sphinx extensions pre-installed for IDE
support (Esbonio). The macro's build targets (``//:docs``, ``//:docs_check``,
``//:docs_link_check``, ``//:traceability_gate``, ``//:live_preview``, ``//:ide_support``)
are documented in the `Build commands reference
<https://eclipse-score.github.io/docs-as-code/v8.1.2/reference/commands.html>`_.

Tool sources live in the ``docs-as-code`` repository under ``src/extensions/``
(Sphinx extensions) and ``docs.bzl`` (Bazel macros). The default metamodel is
bundled at ``@score_docs_as_code//src/extensions/score_metamodel:metamodel_yaml``
and may be overridden via the ``metamodel`` parameter. See the
`Bazel macros reference
<https://eclipse-score.github.io/docs-as-code/v8.1.2/reference/bazel_macros.html>`_
for macro parameters and the
`score_metamodel design
<https://eclipse-score.github.io/docs-as-code/v8.1.2/internals/extensions/metamodel.html>`_
for metamodel definition and validation checks.

Integration
~~~~~~~~~~~
The tool is the central documentation hub of the S-CORE Bazel toolchain, used
by all modules to build, check, and publish documentation.

Cross-module linking supports two modes:

- **External needs import:** reference another module's ``:needs_json_file`` target
  via the ``external_needs`` parameter of ``docs()`` to cross-reference need
  IDs across modules (e.g., ``:need:`gd_req__example_id```).
- **Bundle mounting:** mount another module's ``:docs_bundle`` target via the
  ``bundles`` parameter; the mounted sources join the consuming build, with
  placement controlled by ``mount_at`` (docname prefix) and ``attach_to``
  (toctree anchor). See `How to mount external sources
  <https://eclipse-score.github.io/docs-as-code/v8.1.2/how-to/bundles/index.html>`_.

Within a repository, Sphinx combines documentation sources (RST/Markdown),
needs JSON, source-code links (``sourcelinks_json``) and test metadata through
the S-CORE extensions (``score_metamodel``, ``score_metrics``, ``score_mounts``)
to produce HTML, ``needs.json`` and ``metrics.json``.


Environment
~~~~~~~~~~~
- **Operating system:** Linux — the S-CORE DevContainer (canonical,
  recommended), WSL2, or native.
- **Build system:** Bazel (``rules_python``, ``sphinxdocs``) fetches all
  toolchains and dependencies, including a remote JDK 17 for PlantUML diagrams
  when no local Java is present.

Safety evaluation
-----------------

Evaluation model
~~~~~~~~~~~~~~~~

The evaluation follows the structured SCORE Tool Management model:

.. mermaid::

   graph LR
      DT["doc_tool\nTool Verification Report"]
      UC["tool_usecase\nUsage context"]
      PM["potential_tool_malfunction\nIncorrect behaviour in that context"]
      STKH["stkh_req"]
      TR["tool_req"]

      UC -->|"belongs_to"| DT
      PM -->|"parent_needs"| UC
      UC -->|"realizes (optional)"| STKH
      UC -->|"realized_by"| TR
      PM -->|"violates"| STKH
      PM -->|"violates"| TR

      style DT fill:#F5F5F5
      style UC fill:#E1D5E7
      style PM fill:#F8CECC

``tool_usecase`` is a usage-context and grouping element. It does not add a
new requirements abstraction level. ``potential_tool_malfunction`` describes
incorrect tool behaviour in that context. Its body contains the human-readable
argumentation for the classification; the structured options record the
classification inputs:

* ``safety_affected`` is mandatory.
* ``detection_sufficient`` is required only for safety-relevant malfunctions.
* ``safety_measures`` describes mechanisms active during intended tool usage.
  It is required when ``detection_sufficient`` is ``YES``.
* A safety-relevant malfunction with ``detection_sufficient: NO`` violates at
  least one ``tool_req`` so it can be qualified.

Non-safety malfunctions omit ``detection_sufficient``. Qualification tests are
not safety measures and do not change this classification.

Use cases were derived from the process requirements
and the docs-as-code
`Tool Requirements <https://eclipse-score.github.io/docs-as-code/v8.1.2/internals/requirements/requirements.html>`_.

The facts below are shared by use cases and only referenced in each
Malfunctions cell.

.. _basis-ci:

Build/CI behavior
   Builds run with ``-W``; any warning trips CI. The
   safety-relevant danger is the *silent* failure — a missing warning
   or a wrong output published undetected.
   A loud CI abort is safe: no wrong output enters the baseline.

.. _pr_review:

PR Review
   Repository contents are the source of truth
   and every change is reviewed by a committer
   (:need:`rl__committer`, :need:`doc_concept__wp_inspections`).
   Still, for silent wrong outputs the gated CI stays green.

.. _basis-ti1:

Derived-view
   The rendered HTML output is a derived view;
   the authoritative safety artifacts are mostly the source-controlled work products.
   There are two exceptions, the architecture views (see M4) and backlinks (see M8).
   Rendering/preview defects affect reviewer convenience, not safety evidence.


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

      `Silent false-negative <basis-ci_>`_, too-permissive
      ``metamodel.yaml`` regex accepted with no guard, or a check bug skips a case.

      Impact on safety: yes.
      Impact safety measures available: yes: `PR review <pr_review_>`_.
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

      `Silent false-negative <basis-ci_>`_: Allow links which cannot be safe derivations.

      Impact on safety: yes.
      Impact safety measures available: yes: `PR review <pr_review_>`_.
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

      `Silent wrong-output <basis-ci_>`_: a coverage statistic computed wrong.

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

      `Silent wrong-output <basis-ci_>`_:
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

      `Silent wrong-output <basis-ci_>`_:
      Test references an outdated/missing requirement.

      Impact on safety: yes.
      Impact safety measures available: yes: `PR review <pr_review_>`_.
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

      `Silent wrong-output <basis-ci_>`_: ``aou_req`` items might be missing or wrong.

      Impact on safety: yes.
      Impact safety measures available: yes: `PR review <pr_review_>`_.
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

      `Silent wrong-output <basis-ci_>`_: a diagram misrepresents the architecture.

      Impact on safety: yes.
      Impact safety measures available: yes: `PR review <pr_review_>`_ includes architecture inspection.
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

      `Silent wrong-output <basis-ci_>`_: Generated backlinks are wrong or missing.

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

      Impact on safety: no: `Derived-view <basis-ti1_>`_.
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
     - yes: `PR review <pr_review_>`_.
     - yes
     - no

Result
------
The stored TVR values are derived from the owned graph:

* ``doc_tool.safety_affected`` is ``YES`` because at least one owned
  malfunction is safety affected.
* ``doc_tool.tcl`` is ``LOW`` because at least one owned safety-relevant
  malfunction has ``detection_sufficient: NO``.

The final Tool Confidence Level is therefore **LOW**, the worst case across all
use cases. This result is not changed by qualification. Qualification evidence
is handled in :doc:`qualification`, and a qualified or released report remains
``tcl: LOW``.

S-CORE Docs-as-Code requires qualification
for use in safety-related software development according to ISO 26262.
