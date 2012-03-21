from setuptools import setup

import imp

file = None
try:
    file, pathname, description = imp.find_module('__version__', ['src/rosinstall'])
    vermod = imp.load_module('__version__', file, pathname, description)
    version = vermod.version
finally:
    if file is not None:
        file.close()

    
setup(name='rosinstall',
      version= version,
      packages=['rosinstall'],
      package_dir = {'':'src'},
      install_requires = ['vcstools', 'pyyaml'],
      scripts = ["scripts/rosinstall", "scripts/roslocate", "scripts/rosws", "scripts/rosco"],
      author = "Tully Foote", 
      author_email = "tfoote@willowgarage.com",
      url = "http://www.ros.org/wiki/rosinstall",
      download_url = "http://pr.willowgarage.com/downloads/rosinstall/", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      description = "The installer for ROS", 
      long_description = """\
The installer for ROS
""",
      license = "BSD"
      )
