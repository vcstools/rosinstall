Contributing Guide
==================

Thanks for your interest in contributing to wstool.

Any kinds of contributions are welcome: Bug reports, Documentation, Patches.

This project is a legacy wrapper of the newer wstool replacement https://github.com/vcstools/wstool. The core functionality of abstracting over different version control systems is contained in the library project https://github.com/vcstools/vcstools.

Developer Environment
---------------------

For many tasks, it is okay to just develop using a single installed python version. But if you need to test/debug the project in multiple python versions, you need to install those versions::

1. (Optional) Install multiple python versions

   1. (Optional) Install [pyenv](https://github.com/pyenv/pyenv-installer) to manage python versions
   2. (Optional) Using pyenv, install the python versions used in testing::

       pyenv install 2.7.16
       pyenv install 3.6.8

It may be okay to run and test python against locally installed libraries, but if you need to have a consistent build, it is recommended to manage your environment using `virtualenv <https://virtualenv.readthedocs.org/en/latest/>`_::

  $ virtualenv ~/rosinstall_venv
  $ source ~/rosinstall_venv/bin/activate


If you want to make changes to vcstools as well, you need to run make to get the vcstools project imported into the devel tree.

Source the setup.sh to include the src folder in your PYTHONPATH.

Testing
-------

Prerequisites:

* The tests require git, mercurial, bazaar and subversion to be installed.

Also you need to install python test support libraries::

  # install python dependencies
  $ pip install .[test]
  # optional also use local vcstools/wstool sources directly
  $ pip install --editable /path/to/vcstools_source
  $ pip install --editable /path/to/wstool_source

Then you can use different commands to run various test scopes::

  # run all tests using nose
  $ nosetests
  # run one test using nose
  $ nosetests {testname}
  # run all tests with coverage check
  $ python setup.py test
  # run all tests using python3
  $ python3 setup.py test
  # run all tests against multiple python versions (same as in travis)
  $ tox
  

Releasing
---------

To test on your local machine you can call make install, with checkinstall installed such that it will make a local deb you can then easily remove.

To release make sure that the version number in src/rosinstall/__version__.py and that the doc/changelog.rst are updated.

* Upgrade vcstools/wstool dependency version in `setup.py`
* Update `src/vcstools/__version__.py`
* Check `doc/changelog` is up to date
* Check `stdeb.cfg` is up to date with OSRF buildfarm distros
* prepare release dependencies::

      pip install --upgrade setuptools wheel twine

* Upload to testpypi::

      python3 setup.py sdist bdist_wheel
      twine upload --repository testpypi dist/*

* Check testpypi download files and documentation look ok
* Actually release::

      twine upload dist/*

* Create and push tag::

      git tag x.y.z
      git push
      git push --tags

