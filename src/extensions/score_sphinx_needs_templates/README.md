<!-- ----------------------------------------------------------------------------
  Copyright (c) 2026 Contributors to the Eclipse Foundation

  See the NOTICE file(s) distributed with this work for additional
  information regarding copyright ownership.

  This program and the accompanying materials are made available under the
  terms of the Apache License Version 2.0 which is available at
  https://www.apache.org/licenses/LICENSE-2.0

  SPDX-License-Identifier: Apache-2.0
----------------------------------------------------------------------------- -->

# `score_sphinx_needs_templates`

This extension contains the runtime support for the repository's Sphinx-Needs
`.need` templates. It is loaded by `score_sphinx_bundle` immediately after
`sphinx_needs`.

## Features

The extension provides:

* the shared `src/needs_templates` directory as the Sphinx-Needs template
  directory;
* the L+ report placeholder and materializer for graph-driven verification
  reports.

## L+ reports

An ordinary `mod_ver_report` Need remains the source of the report metadata.
The companion directive records only the report ID and template identity:

```rst
.. score_lplus_report::
   :id: mod_vrep__example
   :template: mod_ver_report_tiny
```

During parallel reading this creates only a pickleable placeholder and a
persisted declaration. At `env-updated`, after worker environments have been
merged, L+ obtains the resolved read-only `NeedsView`, renders the selected
Jinja template against it, parses that controlled RST fragment, and replaces
the placeholder with its ordinary section, Need-reference, and Sphinx-Needs
nodes. A small Sphinx-9 ToC adapter rebuilds the local page navigation from
those real sections. Graph fingerprints and environment dependencies drive
incremental invalidation.

## L+ implementation plan

L+ materializes a graph-driven report in an existing document after parallel
Need collection has completed, then refreshes that document's local ToC. It is
the proposed one-Sphinx-build replacement for the current G reread workaround.
The decision record and constraints are tracked in [Issue #764](https://github.com/eclipse-score/docs-as-code/issues/764).

## Goal and boundaries

The Baselibs report must derive its outline from the complete, resolved Need
graph while retaining the existing `docs()` topology and parallel document
reading. It must not call `builder.read_doc()`, `env.clear_doc()`, or re-enter
Sphinx's reader lifecycle.

L+ is a compatibility-adapter experiment, not a claim that late-generated
content automatically has every property of ordinary source RST. In
particular, it must prove the required local ToC, anchors, Need references, and
non-HTML output before G is removed. A cross-document `:ref:` to a
late-generated heading is an explicit acceptance test, not an assumption.

Out of scope:

* a second Sphinx/Bazel manifest pipeline (A/B);
* an HTML-only navigation menu;
* expanding G's reread/`env.tocs` patch with more report features; and
* a generic graph compiler or an upstream API proposal beyond recording the
  gaps found by the prototype.

## Target design

```text
normal parallel read
        |
        v
report placeholder + persisted dependency declaration
        |
        v
worker-environment merge
        |
        v
env-updated: resolved NeedsView -> materialize existing report Doctree
        |
        v
compatibility adapter: refresh this document's local ToC
        |
        v
normal write/post-transform phase
```

The read-phase directive records only stable report identity and configuration.
It does not traverse the graph or render dynamic headings. At `env-updated`,
the materializer obtains the resolved, read-only `NeedsView`, renders the
selected controlled Jinja template against that model, parses its RST fragment,
and replaces the placeholder with Docutils nodes for targets, sections, titles,
and report content. It does not re-enter the source reader.

The materializer owns an environment-persisted reverse dependency map. It maps
traversed Need IDs, relevant link/config fingerprints, and external inputs to
the report document. It must be deterministic, merge safely across workers,
and mark affected report documents for writing on incremental builds.

The only Sphinx-private surface is the local-ToC refresh. Put it in one small
adapter with an explicit supported-Sphinx-version matrix. The materializer must
never append rubric-derived entries to `env.tocs` directly.

## Delivery steps

1. Establish a fixture and baseline

   Create an isolated documentation fixture with two linked components in
   non-alphabetical link order, an external feature, a backlink-dependent
   element, and a `needextend`. Capture G's intended HTML, anchors, and
   navigation as the behavioural baseline; do not copy its lifecycle code.

2. Add the read-phase placeholder

   Introduce a dedicated report directive/node that creates no dynamic
   sections. Persist report ID, document name, template/config fingerprint,
   and declared external inputs in environment-owned data. Implement purge and
   worker-environment merge handlers for that data only.

3. Build the resolved-model materializer

   On `env-updated`, obtain `get_needs_view(app)` through a narrow model
   adapter. Traverse the report graph in declared order, fail with report/link
   context for an absent target, calculate reverse dependencies, render the
   selected controlled Jinja template, and replace the placeholder exactly
   once with its parsed Docutils/Sphinx-Needs nodes. Do not call
   `builder.read_doc()` or invoke a general source parser.

4. Implement the ToC compatibility adapter

   Regenerate the report document's section ToC from the materialized section
   hierarchy and persist the Sphinx-version-specific collector state. Handle
   target collisions and nested headings. The adapter must be idempotent on
   clean and incremental builds and expose no general-purpose mutation API.

5. Verify source and builder semantics

   Test a `:ref:` from another document to a generated component heading, a
   Need reference within generated content, nested local navigation, and one
   non-HTML builder. If an external `:ref:` needs unsupported late
   label/domain registration, record the missing contract and fail the L+ gate
   instead of adding unbounded private patches.

6. Exercise invalidation and concurrency

   Run clean and incremental builds with `-j 1` and parallel reading. Change a
   transitive Need, an unrelated Need, the report template/configuration, and
   an external Need input. Verify deterministic report/navigation output and
   that only the appropriate report output is refreshed.

7. Decide and migrate

   Promote L+ only when every acceptance criterion below passes on the pinned
   Sphinx/Sphinx-Needs versions. Then remove G's reread, module-global model
   state, rubric-ID generation, and direct `env.tocs` patch for this report.
   If the gate fails, keep G unchanged as a narrow bridge and document the
   missing upstream contract; do not reintroduce A/B for this report.

## Acceptance gate

L+ may replace G only when all of the following hold:

* graph traversal discovers ordered components and a second Need-linked report
  dimension without new directive options or dimension-specific drift checks;
* local and external Needs, backlinks, and accepted `needextend` changes are
  present in the rendered report;
* the local ToC is nested and points to stable, collision-free anchors;
* a cross-document `:ref:` to a generated heading and generated Need
  references resolve correctly;
* HTML and one non-HTML builder complete with equivalent section structure;
* clean and incremental serial/parallel builds are deterministic;
* a transitive input refreshes the report, while an unrelated input leaves its
  output unchanged; and
* all non-public Sphinx interaction is contained in the version-pinned ToC
  adapter and covered by compatibility tests.

## Decision checkpoints

After steps 3 and 4, review the adapter size and private API surface. After
step 5, decide whether L+ meets the normal-page requirement rather than merely
producing a convincing PyData sidebar. A failure in either checkpoint rejects
L+ as the target architecture. The fallback is product work: retain G only as
a constrained bridge and pursue a supported upstream report-and-ToC API.
