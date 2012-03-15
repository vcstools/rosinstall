rosco: checkout source code for ROS resources
=============================================

``rosco`` is instead motivated by "give me the source, now." In
exchange for this haste, it does not do any bookkeeping or environment
configuration for you: it is tries to be equivalent to running ``svn
co``, ``git clone``, or the like.


``rosinstall`` is a useful tool for managing a consistent development
tree of multiple ROS stacks.  It takes care of important environment
configuration, tree updates, and more.  It is less useful in
situations where you just want to quickly get the source for a
particular stack or package as it does more than just retrieve code.

For example, you want to add a stack to an existing checkout, you may have to:

1. Lookup the rosinstall entry for the package/stack using ``roslocate``.
2. Update your rosinstall configuration with this information.
3. Run rosinstall, which will iterate through all entries in the rosinstall configuration.

If you have multiple entries in the rosinstall configuration, you will have to
wait as rosinstall examines each entry for updates.

The roslocate script was suggested in [REP115]_.


Usage
-----

The ``rosco`` command is roughly equivalent to running the equivalent
``svn``, ``git``, or other source control tool to "checkout" or
"clone" a repository.  It does not record any additional state.


rosco <package-or-stack>
''''''''''''''''''''''''

Searches for the specified ROS package or stack and retrieves the
source code use the appropriate version control tool.  For example, if
the source code is stored in a Subversion repository, ``rosco`` will
run a ``svn checkout`` of the resource in the local directory.


rosco --rosinstall <rosinstall-file>, rosco -r <rosinstall-file>
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

For each entry in the rosinstall file, retrieve the source code use
the appropriate version control tool.  Unlike ``rosinstall``, it only
retrieves the source code and nothing more.


piped input
'''''''''''

``rosco`` also accepts piped input formatted as rosinstall entries.
This is primarily meant to be used in combination with ``roslocate``.

Example::

    $ roslocate info rospy | rosco


--distro=DISTRO_NAME
''''''''''''''''''''

Checkout the source code for a particular ROS distribution release,
e.g. ``rosco rospy --distro=electric`` will checkout the Electric
release of rospy.  This option is not valid when used with ``--rosinstall``.
    

--dev
'''''

The ``--dev`` option causes ``rosco`` to checkout the development
branch instead.  It should be specified in combination with a
``--distro=DISTRO_NAME`` option as development branches are
distribution specific.



See also
--------

.. [REP115] rosco and roslocate tools for rosinstall
  (http://www.ros.org/reps/rep-0115.html)
