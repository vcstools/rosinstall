rosinstall file format
======================

REP 126
-------

The rosinstall file format was changed in [REP126]_.


Format
------

The rosinstall file format is a yaml document. It is a list of
top level dictionaries. Each top level dictionary is expected to have one of the vcs type keys and no other keys.

Inside every top level dictionary there is one required key, ``local-name`` this represents the path where to install files.  It will support both workspace relative paths as well as absolute paths.

Each of the vcs type keys requires a ``uri`` key, and optionally takes a ``version`` key.

Additional experimental keys exist, which may be changed or go out of support anygiventime: :ref:`inofficial-format`.

Top Level Keys
--------------
The valid keys are ``svn``, ``hg``, ``git``, ``bzr``, ``other``, ``setup-file``.

Each key represents a form of version control system to use.  These are supported from the vcstools module.

The ``other`` key is used to add a path to the workspace without associating a version control system.

In [REP126]_ the key ``setup-file`` was added to support the Fuerte
release.

Example rosinstall syntax:
--------------------------

Below is an example rosinstall syntax with examples of most of the
possible permutations:

::

 - svn: {local-name: some/local/path2, uri: /some/local/uri}
 - hg: {local-name: some/local/path3, uri: http://some/uri, version: 123}
 - git: {local-name: /some/local/aboslute/path, uri: http://some/uri, version: 123}
 - bzr: {local-name: some/local/path4, uri: http://some/uri, version: 123}
 - setup-file:
     local-name: /opt/ros/fuerte/setup.sh
 - other:
     local-name: /opt/ros/fuerte/share/ros

Things to note are:

 - VCS keys require ``uri``, but ``version`` is optional though recommended.
 - Absolute or relative paths are valid for ``local-name``
 - ``setup-file`` and ``other`` do not take any keys besides ``local-name``
 - ``uri`` can be a local file path to a repository.

See also
--------

.. [REP126] setup-file root element
  (http://www.ros.org/reps/rep-0126.html)
