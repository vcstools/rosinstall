from setuptools import setup

import imp


with open('README.rst') as readme_file:
    README = readme_file.read()


def get_version():
    ver_file = None
    try:
        ver_file, pathname, description = imp.find_module('__version__', ['src/rosinstall'])
        vermod = imp.load_module('__version__', ver_file, pathname, description)
        version = vermod.version
        return version
    finally:
        if ver_file is not None:
            ver_file.close()


test_required = [
    "nose",
    "coverage",
    "mock",
    # run checks in multiple environments
    "tox",
    "tox-pyenv"
]


setup(name='rosinstall',
      version=get_version(),
      packages=['rosinstall'],
      package_dir={'': 'src'},
      install_requires=[
          'vcstools>=0.1.38',
          'pyyaml',
          'rosdistro>=0.3.0',
          'catkin_pkg',
          'wstool>=0.1.14',
          'rospkg'
      ],
      tests_require=test_required,
      # extras_require allow pip install .[test]
      extras_require={
        'test': test_required
      },
      scripts=["scripts/rosinstall", "scripts/roslocate",
               "scripts/rosws", "scripts/rosco"],
      author="Tully Foote",
      author_email="tfoote@osrfoundation.org",
      url="http://wiki.ros.org/rosinstall",
      download_url="http://download.ros.org/downloads/rosinstall/",
      keywords=["ROS"],
      classifiers=["Programming Language :: Python",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 3",
                   "Development Status :: 7 - Inactive",
                   "License :: OSI Approved :: BSD License",
                   "Topic :: Software Development :: Version Control"
      ],
      description="The installer for ROS",
      long_description=README,
      license="BSD")
