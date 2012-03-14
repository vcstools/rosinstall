ROS installation tools
======================

.. module:: rosinstall
.. moduleauthor:: Tully Foote <tfoote@willowgarage.com>, Thibault Kruse <kruset@in.tum.de>, Ken Conley <kwc@willowgarage.com>

The rosinstall package provides a Python API for interacting with a source code workspace as well as a group of command line tools.  Rosinstall leverages the :mod:`vcstools` module for source control and stores its state in .rosinstall files.

  
Command Line Tools:
===================
.. toctree::
   :maxdepth: 2

   rosinstall
   roslocate
   rosco
   rosws


Rosinstall File Format:
=======================
.. toctree::
   :maxdepth: 2

   rosinstall_file_format   

Installation
============

rosinstall is available on pypi and can be installed via ``pip``
::

    pip install -U rospkg

or ``easy_install``:

::

    easy_install -U rosinstall




Advanced: rosinstall developers/contributors
============================================

.. toctree::
   :maxdepth: 2

   developers_guide


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

