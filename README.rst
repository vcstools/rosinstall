rosinstall
==========

Command-line tools for maintaining a workspace of projects from multiple version-control systems, tailored for the ROS (Robot operating system) community.

See http://www.ros.org/doc/api/rosinstall/html

Installing
----------

Install the latest release on Ubuntu using apt-get::

  $ sudo apt-get install rosinstall

On other Systems, use the pypi package::

  $ pip install rosinstall

For Bash/Zsh completion::

  $ pip install rosinstall-shellcompletion

To test in a development environment

Developer Environment
---------------------

If you want to make changes to vcstools as well, you need to run make to get the vcstools project imported into the devel tree.

Source the setup.sh to include the src folder in your PYTHONPATH.

Testing
-------

Use the python library nose to test::

  $ nosetests

To test with coverage, make sure to have python-coverage installed and run::

  $ nosetests --with-coverage --cover-package vcstools

To run python3 compatibility tests, you'd need python-dateutil for python3.
Best to create a virtualenv for python3 and pip install python-dateutil to that one. Then::

  $ python -m unittest discover --pattern *.py

Releasing
---------

To test on your local machine you can call make install, with checkinstall installed such that it will make a local deb you can then easily remove.

To release make sure that the version number in src/rosinstall/__version__.py and that the doc/changelog.rst are updated.

* To upload to pypi make push
* To upload to ppa make upload
* You will need stdeb available from pip, and
