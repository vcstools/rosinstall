from setuptools import setup

import imp


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


setup(name='rosinstall',
      version=get_version(),
      packages=['rosinstall'],
      package_dir={'': 'src'},
      install_requires=['vcstools>=0.1.30', 'pyyaml', 'rosdistro>=0.3.0', 'catkin_pkg', 'wstool>=0.1.0'],
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
                   "License :: OSI Approved :: BSD License"],
      description="The installer for ROS",
      long_description="""\
The installer for ROS
""",
      license="BSD")
