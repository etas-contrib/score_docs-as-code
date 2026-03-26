.. _any_folder_concept:

Any Folder
==========

The goal is simple: developers should be able to place documentation files
anywhere in the repository, not only in ``docs/``.
A component developer writing ``src/my_component/`` naturally wants the component's docs
to live next to the code in ``src/my_component/docs/``.

Sphinx, however, only reads files inside its source directory (``confdir``,usually ``docs/``).
The ``score_any_folder`` extension bridges this gap
by creating temporary symlinks inside ``confdir`` that point to the external directories.
Sphinx then discovers the files as if they were always there.

The fundamental conflict: two build modes
-----------------------------------------

The difficulty is that docs-as-code supports two structurally different build modes
that pull in opposite directions.

**Live/incremental builds**
(``bazel run :docs``, ``bazel run :live_preview``, Esbonio)
run Sphinx directly on the developer's real workspace filesystem.
Every file in the repository is accessible by its real path.
Symlinks created by ``score_any_folder`` work naturally here.

**Combo builds** (``bazel run :docs_combo``)
aggregate documentation from multiple external repositories into a single Sphinx run.
External modules are not present as real directories on the filesystem;
they are mounted from Bazel runfiles by ``sphinx_collections``.
Each module's file tree appears under
``_collections/{module}/`` as a directory symlink into the runfiles.

.. mermaid::

   graph LR
       subgraph a["Module A"]
           LIVE[":live_preview"]
           SRCS["docs/**"]
           EXT["src/extensions/docs/**"]
           CONFA["conf.py"]
           LIVE --> CONFA
           CONFA -.-> EXT
       end

       subgraph b["Module B"]
           COMBO[":docs_combo"]
           SRCS2["docs/**"]
           CONFB["conf.py"]
           COMBO --> CONFB
       end

       LIVE --> SRCS
       COMBO --> SRCS
       COMBO --> SRCS2

The conflict: ``score_any_folder`` is designed to create symlinks based on
the ``score_any_folder_mapping`` in the *active* ``conf.py``.
In a combo build the active conf.py belongs to the aggregating project,
not to any external module.
Each mounted module has its own ``conf.py`` with its own mapping,
but nothing would apply it —
so the symlinks for those modules are never created, and their docs are broken.

How the conflict is resolved
-----------------------------

The resolution has three cooperating parts.

#. **Runtime symlinks (score_any_folder).**
   ``score_any_folder`` runs at Sphinx event priority 600,
   after ``sphinx_collections`` (priority 500) has already created all mounts.
   It then scans ``confdir`` for ``conf.py`` files in *subdirectories*,
   which includes the mounted modules' conf files.
   For each one it finds, it extracts the ``score_any_folder_mapping``
   and applies the symlink mapping relative to that module's directory —
   exactly as if Sphinx were building that module standalone.

#. **Deduplication (exclude_patterns).**
   ``sphinx_collections`` mounts a module's *entire* runfiles tree, not just its ``docs/`` directory.
   This means files from ``source_dir_extras`` (e.g. ``src/extensions/docs/``) are visible to Sphinx at two paths:
   directly through the mount *and* through the symlink just created.
   To prevent duplicate-label errors,
   ``score_any_folder`` adds the direct paths to Sphinx's ``exclude_patterns``
   so only the symlinked path is indexed.

#. **Bazel dependency declarations (source_dir_extras).**
   For hermetic ``needs_json`` builds, Bazel must know about every input file before the build starts.
   Files reachable only through runtime symlinks are invisible to Bazel's dependency analysis.
   The ``source_dir_extras`` parameter of ``docs()`` lets a module declare these external directories
   as explicit Bazel filegroup targets.
   For combo builds, ``docs_sources`` also includes ``conf.py`` itself
   so that the auto-discovery scan in step 1 can find and read it from within the mounted runfiles.

Architectural risks
--------------------

This design works today but rests on several assumptions that could break silently.

**Symlinks into runfiles.**
Secondary symlinks are created inside the Bazel runfiles tree
(because the sphinx_collections mount is itself a symlink into it).
This works because ``bazel run`` currently provides a writable runfiles tree.
If Bazel ever makes the runfiles read-only, symlink creation will fail.

**exclude_patterns is a workaround for a mount granularity problem.**
The real cause of the duplication is that ``sphinx_collections`` mounts the full module root, not just ``docs/``.
The ``exclude_patterns`` approach is a compensating hack.
If Sphinx changes how it processes ``exclude_patterns``,
or if ``sphinx_collections`` changes how it creates mounts,
the deduplication can silently stop working.
The symptom would be a flood of duplicate-label warnings in combo builds.

**Timing dependency.**
The entire secondary-scan mechanism depends on ``sphinx_collections``
completing its mounts before ``score_any_folder`` scans for conf.py files.
This is enforced by Sphinx event priority (600 vs. 500), an internal detail not visible in any public API.
A change in either extension's registered priority would break the ordering silently.

**Python symlink traversal.**
``os.walk(followlinks=True)`` is used rather than ``Path.rglob()``
because Python ≤ 3.12 does not follow symlinked directories in ``rglob``.
This is a known Python limitation,
but it means that any future refactor to use ``rglob`` would silently break auto-discovery in all combo builds.
