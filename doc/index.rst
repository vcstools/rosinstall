ROS installation tools
======================

.. module:: rosinstall
.. moduleauthor:: Tully Foote <tfoote@willowgarage.com>, Thibault Kruse <kruset@in.tum.de>, Ken Conley <kwc@willowgarage.com>

Using rosinstall you can update several folders using a variety 
of SCMs (SVN, Mercurial, git, Bazaar) with just one command.

That way you can more effectively manage source code workspaces.

The rosinstall package provides a Python API for interacting with a
source code workspace as well as a group of command line tools.
Rosinstall leverages the :mod:`vcstools` package for source control and
stores its state in .rosinstall files.

rosinstall was developed to help with the ROS software, but it 
has no install dependencies to ROS. It offers support for ROS
environments and thus makes some assumptions about ROS being 
present at runtime, but those can be easily removed and rosws
provides all services even when there is no ROS installed. The 
vision is for the bulk of rosinstall to be a ROS agnostic 
tool one day.

  
Command Line Tools:
===================
.. toctree::
   :maxdepth: 2

   rosinstall_usage
   rosws
   roslocate
   rosco

Installation
============

Ubuntu
------

On Ubuntu the recommended way to install rosinstall is to use apt. If
the ros sources are added to your apt sources .

To set ROS sources see http://www.ros.org/wiki/fuerte/Installation/Sources

::

    sudo apt-get install python-rosinstall

Other Platforms
---------------

On other platforms rosinstall is available on pypi and can be installed via ``pip``
::

    pip install -U rosinstall

or ``easy_install``:

::

    easy_install -U rosinstall vcstools

Linux and Bash users will benefit a lot from also installing bash
completion. This is provided in a different package due to the 
installation process currently requiring linux. It is only available 
via pip for now::

    pip install -U rosinstall_shellcompletion


Tutorials
=========

.. toctree::
   :maxdepth: 2

   rosws_tutorial
   rosws_ros_tutorial


Rosinstall File Format:
=======================
.. toctree::
   :maxdepth: 2

   rosinstall_file_format   


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


