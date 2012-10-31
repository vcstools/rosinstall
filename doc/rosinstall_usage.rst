rosinstall: source-based install tool
=====================================

Usage
-----

::

    Usage: rosinstall <path> <paths...> [options]
    
    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -c, --catkin          Declare this is a catkin build.
      --cmake-prefix-path=CATKINPP
                            Where to set the CMAKE_PREFIX_PATH, implies --catkin
      --version             display version information
      --verbose             display more information
      -n, --nobuild         skip the build step for the ROS stack
      --rosdep-yes          Pass through --rosdep-yes to rosmake
      --delete-changed-uris
                            Delete the local copy of a directory before changing
                            uri.
      --abort-changed-uris  Abort if changed uri detected
      --backup-changed-uris=BACKUP_CHANGED
                            backup the local copy of a directory before changing
                            uri to this directory.
      --diff                shows a combined diff over all SCM entries
      --status              shows a combined status command over all SCM entries
      --status-untracked    shows a combined status command over all SCM entries,
                            also showing untracked files
      -j JOBS, --parallel=JOBS
                            How many parallel threads to use for installing
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

Rosinstall Under the Hood
-------------------------

This is a summary of how rosinstall works under the hood.  

Process Flow
~~~~~~~~~~~~

Whenever rosinstall is executed the following code path is followed:

#. Gather command line arguments
#. Merge source rosinstall files
#. Install source
#. Generate a setup file. 

Merging source rosinstall files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Rosinstall will start with the `.rosinstall` file in the install path.  
 * If one doesn't exist it will create an empty one.  
2. To this it will append the contents of all arguments in order left to right.  
  * if the argument is a directory it will look for a `DIRECTORY/.rosinstall` and add all elements as `other` elements with `local-name` set to the full path.
  * if the argument is a url or a path to a file it will directly take the contents
3. Duplicates will be removed based on the key 'local-name'.  The later definition will be preserved.  
4. This `.rosinstall` file will be saved to disk.

Installing Source
~~~~~~~~~~~~~~~~~

#. rosinstall will iterate through the `.rosinstall` file for each definition of source. 
#. If the source directory does not exist it will be created and checked out
#. if the source directory exists and is of the same `uri` it will be updated
#. If the source directory exists and the uri doesn't match the user will be prompted to abort, delete, or backup 


Generating setup.bash
~~~~~~~~~~~~~~~~~~~~~

1. After a successful installation `rosinstall` will iterate through each of the elements in `.rosinstall` and add their `local-name` to the ROS_PACKAGE_PATH, unless the path is detected to be ros, in which case it will be set to ROS_ROOT.  
 * This will error if a ROS directory is not detected.  (The ros directory must be explicitly called out in the `local-name`)
2. The setup file will be written to disk.
