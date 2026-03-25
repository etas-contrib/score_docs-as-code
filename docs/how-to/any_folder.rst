Use Any Folder for Documentation
================================

Generally, your documentation must be ``docs/``,
but the RST files for a module may live closer to the code they describe,
for example in ``src/my_module/docs/``.
You can symlink the folders by adding to your ``conf.py``:

.. code-block:: python

   score_any_folder_mapping = {
       "../score/containers/docs": "component/containers",
   }

All files in ``score/containers/docs/`` become available at ``docs/component/containers/``.
Include them via ``toctree`` as usual.

If you have ``docs/component/overview.rst``, for example,
you can include the component documentation via ``toctree``:

.. code-block:: rst
   :caption: some rst file

   .. toctree::

      containers/index

Only relative links are allowed.

The symlinks will show up in your sources.
**Don't commit the symlinks to git!**

Bazel
-----

When building with Bazel, declare the mapped directories as ``source_dir_extras``
in your ``docs()`` call so Bazel tracks them as dependencies:

.. code-block:: python
   :caption: BUILD

   docs(
       source_dir = "docs",
       source_dir_extras = ["//score/containers:docs_sources"],
       ...
   )

This is necessary for sandboxed builds.
For example, when other modules use your documentation's ``needs.json`` as a dependency.
