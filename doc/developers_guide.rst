Developer's Guide
=================

Code API
--------

.. toctree::
   :maxdepth: 1

   modules

Changelog
---------

.. toctree::
   :maxdepth: 1

   changelog

Bug reports and feature requests
--------------------------------

- `Submit a bug report <https://kforge.ros.org/vcstools/trac/newticket?component=rosinstall&type=defect>`_
- `Submit a feature request <https://kforge.ros.org/vcstools/trac/newticket?component=rosinstall&type=enhancement>`_


Developer Setup
---------------

The rosinstall source can be downloaded using Mercurial::

  $ hg clone https://kforge.ros.org/vcstools/rosinstall

You will also need vcstools, which you can either install using pip or download using::

  $ hg clone https://kforge.ros.org/vcstools/hg

If you download it without installing it, you need to export its location to your :envvar:`PYTHONPATH`::

  $ cd vcstools
  $ . setup.sh

To work on the bash completion, there is a separate repository::

  $ hg clone https://kforge.ros.org/vcstools/ri_bash_completion

That one does not contain python code.

rosinstall uses `setuptools <http://pypi.python.org/pypi/setuptools>`_,
which you will need to download and install in order to run the
packaging.  We use setuptools instead of distutils in order to be able
use ``setup()`` keys like ``install_requires``.

Configure your :envvar:`PYTHONPATH`::

   $ cd rosinstall
   $ . setup.sh

OR::

   $ cd rosinstall
   $ python setup.py install

The first will prepend ``rosinstall/src`` to your :envvar:`PYTHONPATH`. The second will install rosinstall into your dist/site-packages.

Testing
-------

Install test dependencies

::

   $ pip install nose
   $ pip install mock


rosinstall uses `Python nose
<http://readthedocs.org/docs/nose/en/latest/>`_ for testing, which is
a fairly simple and straightforward test framework.  The rosinstall
mainly use :mod:`unittest` to construct test fixtures, but with nose
you can also just write a function that starts with the name ``test``
and use normal ``assert`` statements.

rosinstall also uses `mock <http://www.voidspace.org.uk/python/mock/>`_
to create mocks for testing.

You can run the tests, including coverage, as follows:

::

   $ cd rosinstall
   $ make test


Documentation
-------------

Sphinx is used to provide API documentation for rosinstall.  The documents
are stored in the ``doc`` sub-directory.

You can build the docs as follows:

::

   $ cd rosinstall/doc
   $ make html


Inofficial file format
----------------------

The willow garage build system relies on these two extensions to the rosinstall file format.
Basic element types include 'tar', and meta properties can be attached.

Example::

  - svn:
    local-name: rosorg
    meta:
      repo-name: ros-docs
    uri: https://code.ros.org/svn/ros/stacks/rosorg/trunk
  - tar:
    local-name: foo.tar.bvz2
    version: foo-1.2.0

The meta element has no further semantics to rosinstall, it is just passed through.
The tar element is an unsupported but required feature of vcstools, with the peculiar 
semantics that 'version' must refer to a folder inside the tar root.

