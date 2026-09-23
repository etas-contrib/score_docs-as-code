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

Doc-as-Code Tool Qualification
==============================

This page is the qualification part of the Tool Verification Report. The
classification of intended usage, potential malfunctions, safety impact and
detection is maintained in :doc:`classification`. The two pages remain
separate because they answer different questions in the SCORE workflow:

* **Classification:** can intended tool usage fail, and is that failure
  sufficiently detected or prevented during intended usage?
* **Qualification:** does the concrete tool version satisfy the
  ``tool_req`` needs on which the project relies?

The complete workflow and authoring guidance are documented in
:doc:`../../how-to/perform_tool_verification`.

Tool Verification Report
------------------------

The report owns its evaluation through ``belongs_to`` links from
``tool_usecase`` needs. The post-template follows that graph and renders the
evaluation and qualification views below automatically.

.. doc_tool:: Doc-as-Code
   :id: doc_tool__score_docs_as_code
   :status: evaluated
   :version: 3
   :tool_version: v8.1.2
   :tcl: LOW
   :safety_affected: YES
   :security_affected: YES
   :realizes: wp__tool_verification_report[version==1]
   :tags: tool_management, tools_documentation
   :post_template: tool_qualification_report

Qualification basis
-------------------

The classification page contains the owned use cases and malfunctions. The
qualification scope is derived from this graph:

.. mermaid::

   graph LR
      DT["doc_tool"]
      UC["owned tool_usecase"]
      PM["LOW potential_tool_malfunction"]
      TR["tool_req requiring qualification"]
      TC["testcase"]

      DT -->|"belongs_to backlink"| UC
      UC -->|"parent_needs backlink"| PM
      PM -->|"violates"| TR
      TC -->|"fully_verifies / partially_verifies"| TR

Qualification is required when a malfunction is safety affected and has
``detection_sufficient: NO``. Such a malfunction must violate at least one
``tool_req``. Stakeholder requirements may be linked as additional context,
but a stakeholder requirement alone cannot be qualified by tool evidence.

Evidence interpretation
-----------------------

Qualification reuses the existing SCORE testcase and requirement coverage
model. A relevant ``tool_req`` is completely qualified when at least one
``testcase``:

* has ``result: passed``; and
* links to the requirement through ``fully_verifies``.

``partially_verifies`` remains useful traceability evidence, but it does not
complete qualification by itself. The report template renders every relevant
tool requirement, its testcase links and the recorded result. It also keeps
requirements without verification links visible so missing evidence cannot be
mistaken for completed qualification.

Qualification is not a safety measure. A passed qualification testcase does
not change ``detection_sufficient`` and does not change the derived TCL.

Requirements and test evidence
------------------------------

Tool requirements are defined in the docs-as-code internal requirements
documentation. Each ``tool_req`` represents behaviour on which the project
relies, such as mandatory attribute enforcement, linkage rules, graph checks,
test linkage or report generation.

Testcase results and metadata are published in
`Tooling Verification <https://eclipse-score.github.io/docs-as-code/v8.1.2/internals/requirements/tooling_verification.html>`_.
The existing requirement coverage view and ``metrics.json`` remain the source
for verification links and testcase results; qualification does not introduce
a second test type or a parallel qualification-test framework.

External and self-developed tools use the same qualification flow. External
tools are typically validated as black boxes against the requirements our
project relies on. Self-developed tools should reuse suitable development
requirements and tests whenever those tests provide evidence for the concrete
tool version.

Lifecycle state
---------------

The report status records workflow progress rather than an arbitrary label:

.. list-table:: Tool Verification Report status
   :header-rows: 1
   :widths: 18 62

   * - Status
     - Meaning in this model
   * - ``draft``
     - Work in progress; evaluation data may be incomplete.
   * - ``evaluated``
     - Owned use cases and structurally valid malfunctions are present, and the
       stored safety relevance and TCL match the derived graph values.
   * - ``qualified``
     - The report has ``tcl: LOW`` and every qualification-relevant
       ``tool_req`` has successful full-verification evidence.
   * - ``released``
     - Evaluation is consistent; LOW reports also meet the qualification
       evidence rule. HIGH reports do not acquire a qualification requirement
       merely because they are released.
   * - ``rejected``
     - Review outcome; it does not claim that qualification was completed.

Qualification does not reclassify the tool. These are valid final states:

.. code-block:: text

   tcl: LOW
   status: qualified

   tcl: LOW
   status: released

The TCL remains LOW because the underlying safety-relevant malfunction still
has insufficient detection. Only a change to the intended usage or its safety
and detection measures can change that classification.

Generated report views
----------------------

The ``tool_qualification_report`` post-template automatically generates:

* a complete evaluation table with use case, malfunction, violated
  requirements, safety impact, safety measures and detection sufficiency;
* the derived safety relevance, tool confidence and qualification-required
  summary; and
* for LOW reports, the qualification matrix and testcase evidence for each
  relevant ``tool_req``.

This avoids duplicating the graph manually in a separate qualification table.
The structured Needs remain authoritative; the rendered tables are derived
views.

Current report state
--------------------

The report above is intentionally ``status: evaluated``. Its classification
derives ``tcl: LOW`` and therefore requires qualification evidence before it
can progress to ``qualified`` or ``released``. The generated qualification
view shows the current evidence state for each relevant requirement.
