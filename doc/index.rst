ROS installation tools
======================

.. module:: rosinstall
.. moduleauthor:: Tully Foote <tfoote@willowgarage.com>, Thibault Kruse <kruset@in.tum.de>, Ken Conley <kwc@willowgarage.com>

Using rosinstall you can update several folders using a variety 
of SCMs (SVN, Mercurial, git, Bazaar) with just one command.

That way you can more effectively manage source code workspaces.

The rosinstall package provides a Python API for interacting with a
source code workspace as well as a group of command line tools.
Rosinstall leverages the :mod:`vcstools` module for source control and
stores its state in .rosinstall files.

  
Command Line Tools:
===================
.. toctree::
   :maxdepth: 2

   rosinstall_usage
   rosws
   roslocate
   rosco

Tutorials
---------

.. toctree::
   :maxdepth: 2

   rosws_tutorial



Rosinstall File Format:
=======================
.. toctree::
   :maxdepth: 2

   rosinstall_file_format   

Installation
============

rosinstall is available on pypi and can be installed via ``pip``
::

    pip install -U rosinstall

or ``easy_install``:

::

    easy_install -U rosinstall vcstools


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


