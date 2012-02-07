from setuptools import setup

setup(name='rosinstall',
      version= '0.5.26',
      packages=['rosinstall'],
      package_dir = {'':'src'},
      install_requires=['vcstools'],
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
