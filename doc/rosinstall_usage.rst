rosinstall: source-based install tool
=====================================

Usage
-----

::

    Usage: rosinstall <path> <paths...> [options]
    
    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -n, --nobuild         skip the build step for the ROS stack
      --rosdep-yes          Pass through --rosdep-yes to rosmake
      --delete-changed-uris
                            Delete the local copy of a directory before changing
                            uri.
      --abort-changed-uris  Abort if changed uri detected
      --backup-changed-uris=BACKUP_CHANGED
                            backup the local copy of a directory before changing
                            uri to this directory.
      --generate-versioned-rosinstall=GENERATE_VERSIONED
                            generate a versioned rosintall file


The first `<path>` is the filesystem path where the source code will
be downloaded.  Any additional `<paths...>` are treated as locations
from which to fetch additional rosinstall file configuration.  *These
can be filesystem paths or URLs*. The behavior of rosinstall depends
on what `<paths...>` points to:

 - If an additional path is a filesystem directory, rosinstall will look for a `.rosinstall` file in the directory, and then overlay the new environment on top of that directory's configuration.
 - If an additional path points to a `.rosinstall` file, rosinstall will include the contents of that file.  

For example::

    rosinstall ~/ros "http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=electric&variant=desktop-full&overlay=no"

After installation, ``rosinstall`` writes a bash setup file, called
``setup.bash``, into ``<path>``.  Source this file to configure your
`environment variables`_.

.. _environment variables: http://ros.org/wiki/ROS/EnvironmentVariables

rosinstall will also store the checkout information used in ``<path>/.rosinstall``.


Updating a rosinstall checkout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


After using rosinstall to download and setup a certain directory tree.  You can update the the contents of that tree using rosinstall as well.

::

    rosinstall ~/workspace

will read the ``.rosinstall`` file in ``~/ros`` and then call ``svn up`` or other VCS "update" equivalent.  This will also regenerate the ``setup.bash`` environment file.  

If you are already in ``~/workspace`` you can update by typing::

    rosinstall .


Examples usages
~~~~~~~~~~~~~~~

*Developing on top of boxturtle shared install*::

    rosinstall ~/workspace /opt/ros/boxturtle http://www.ros.org/rosinstalls/wg_boxturtle_devel.rosinstall

*Full source checkout*::

    rosinstall ~/workspace http://www.ros.org/rosinstalls/boxturtle_pr2all.rosinstall

*Developing a stack against a full tree*::

    rosinstall ~/workspace http://www.ros.org/rosinstalls/boxturtle_pr2all.rosinstall my_stack.rosinstall


*Adding a rosinstall layout to an existing workspace*

Create a new workspace directory and include `/opt/ros/diamondback` in the `ROS_PACKAGE_PATH`::

    rosinstall ~/workspace /opt/ros/diamondback

Add wg_boxturtle_devel packages to the workspace::

    rosinstall ~/workspace http://www.ros.org/rosinstalls/wg_boxturtle_devel.rosinstall

