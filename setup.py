from setuptools import setup

try:
    import yaml
except:
    raise SystemExit("rosinstall requires python-yaml. Please install python-yaml. On debian systems sudo apt-get install python-yaml.")


setup(name='rosinstall',
      version= '0.5.28',
      packages=['rosinstall'],
      package_dir = {'':'src'},
      install_requires=['vcstools', 'datetime'],
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
