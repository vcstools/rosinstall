roslocate: locate source-control repositories
=============================================

``roslocate`` is a tool for finding version-control and other
information about a ROS package or stack.  The main use is to locate
the source-control repository of a resource, though it can also
provide additional metadata about that resource. 

The roslocate script was suggested in [REP115]_.


.. contents::
   :depth: 3

Usage
-----

::

    roslocate
    	info	Get rosinstall info of resource
    	vcs	Get name of source control system
    	type	Package or stack
    	uri	Get source control URI of resource
    	www	Get web page of resource
    	repo	Get repository name of resource
    	describe	Get description of resource


``roslocate`` has a command-based API.  Each of the commands is described below.


describe
''''''''

``roslocate describe`` summarizes information about a ROS package or
stack.  

Example::

    $ roslocate describe rosinstall
    
    Type: package
    Stack: ros_release
    Description: rosinstall is a tool to check out ROS source code (or
    any source code, really) from multiple version control
    repositories and updating these checkouts. Given a *.rosinstall
    file that specifies where to get code, rosinstall will check out a
    working copy for you. We recommend the use of rosinstall when
    checking out development versions of ROS source code. This package
    is where the code lives, however it is not expected for users to
    checkout and use this package directly.  It is expected that users
    use the version available through pypi.python.org.
    URL: http://ros.org/wiki/rosinstall
        
info
''''

Prints the rosinstall entry for the resource.  

Example::

    $ roslocate info common
    - hg:
        local-name: common
        meta:
          repo-name: wg-kforge
        uri: https://kforge.ros.org/common/common
        version: default
    

repo
''''

Prints the name of the repository the resource is stored in.  This
repository name is for display purposes only -- it cannot be used as
input to source control tools.

Example::

    $ roslocate repo cram_pl
    tum-ros-pkg

uri
'''

Prints the source control URI of a resource.  This is mainly intended
as input to other programs via shell backtick or pipe.


Example::

    $ roslocate uri rospy
    https://code.ros.org/svn/ros/stacks/ros_comm/trunk/clients/rospy


vcs
'''

Prints the type of version control system used for the resource.
Possible values include ``svn``, ``hg``, ``git``, and ``bzr``.


Example::

    $ roslocate vcs common
    hg

www
'''

Prints the website of a resource.  

Example::

    $ roslocate www rospy
    http://ros.org/wiki/rospy


--distro=DISTRO_NAME
''''''''''''''''''''

If the ``--distro=DISTRO_NAME`` option is combined with a roslocate
command, the information returned will be based on a particular
distribution release of a resource.


Example::

    $ roslocate info rospy
    - svn:
        local-name: rospy
        uri: https://code.ros.org/svn/ros/stacks/ros_comm/trunk/clients/rospy
    
    $ roslocate info rospy --distro=diamondback
    - svn:
        local-name: ros_comm
        uri: https://code.ros.org/svn/ros/stacks/ros_comm/tags/ros_comm-1.4.7
    

--dev
'''''

If the ``--dev`` option is combined with a roslocate command, the
information returned will be based on the development branch of the
resource (e.g. ``trunk``), if possible.  It should be used in
combination with the ``--distro=DISTRO_NAME`` option as development
trees are indexed based on a particular ROS distribution.

The ``-dev`` option generally only affects source control information,
like URIs and rosinstall entries.  Other information, like resource
descriptions, are not guaranteed to be development-branch specific.

    
Example::

    $ roslocate info rospy --distro=electric
    - svn:
        local-name: ros_comm
        uri: https://code.ros.org/svn/ros/stacks/ros_comm/tags/ros_comm-1.6.0
        
    $ roslocate info rospy --distro=electric --dev
    - svn:
        local-name: ros_comm
        uri: https://code.ros.org/svn/ros/stacks/ros_comm/trunk
    



Indexer
-------

``roslocate`` is a command-line interface for accessing information
produced by the ROS.org indexing system, which crawls the known public
repositories of ROS-compatible software.

The process for getting a repository added to this index is described
`on the "Get Involved" ROS.org page
<http://www.ros.org/wiki/Get%20Involved#Create_Your_Own_.2A-ros-pkg_Repository>`_.
The indexer files themselves are stored in the ``rosdoc_rosorg``
package, which can be `browsed online`_.
Of particular interest is the ``repos.list`` file as well as the
individual rosinstall file in the ``repos`` directory.

.. _browsed online: https://code.ros.org/svn/ros/stacks/rosorg/trunk/rosdoc_rosorg/>_`.

See also
--------

.. [REP115] rosco and roslocate tools for rosinstall
  (http://www.ros.org/reps/rep-0115.html)

