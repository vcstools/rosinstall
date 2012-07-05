====================
 rosws ROS Tutorial
====================

In this tutorial we will focus on how to use ``rosws`` for doing
development work for ROS.  We will use the ROS fuerte distribution,
but you can use other distributions as well.

.. contents:: Contents
   :depth: 3

Introduction
------------

The problem ``rosws`` tries to solve is that developers in robotics today
have to work with source code from multiple sources, multiple version
control systems, in multiple versions.

While many ROS libraries can be installed into system directories via
Debian packages or other system-based distribution mechanisms, many
developers have ROS libraries installed from source somewhere in their
home directory, and then made available at runtime by inclusion in the 
``ROS_PACKAGE_PATH`` environment variable. 

By manipulating this environment variable, users can create their own
packages, install additional packages from source, or even shadow
installed packages with experimental versions.

There are a few ways to manage these "overlay" environments. A user
can manage ``ROS_PACKAGE_PATH`` environment variable by hand, but this
is cumbersome, can lead to confusion when switching environments, and
errors in this variable can easily break a user's
environment. Alternatively, ``rosws`` (ROS Workspace) provides a
systematic method for managing package overlays in a user's workspace.

When the developer makes changes to the source code and builds the
code, it is important that the builder uses the right ROS distribution
(e.g. electric vs fuerte) as well as the right version of the source code.

A builder will typically use environment variables such as ``CPATH,
LD_LIBRARY_PATH, PKG_CONFIG_PATH,`` etc. So the developer will have to
make sure that all those variables are all set correctly every time he
runs a build. Similarly, when the developer has a ROS package both
installed as a system library as well as local 'overlay' checkout
(with his modifications), it is important that the builder chooses the
right libraries for the build process, so the order of entries in the
environment variables also needs to be managed.

This is what ``rosws`` attempts to make easier for developers.

Binding a workspace to a ROS distribution
-----------------------------------------

The following command creates a new fuerte overlay workspace in ~/fuerte::

  $ rosws init ~/fuerte /opt/ros/fuerte

.. note:: 
  This command does nothing else than to create the folder
  ``~/fuerte``, the files ``setup.bash``, ``setup.sh``, ``setup.zsh``
  and the hidden file ``.rosinstall`` in the directory ``~/fuerte``.

We will use ``~/fuerte`` from now on. Other workspaces could be set
up similarly like this::

    $ rosws init ~/electric /opt/ros/electric
    $ rosws init ~/electric_unstable /opt/ros/electric

The next step is to source the ``setup.bash`` in ``~/fuerte``::

    $ source ~/fuerte/setup.bash

.. note::
  You can only source one workspace at a time. It is generally error
  prone to switch from one workspace to another, this can cause
  confusing errors. Prefer to keep the same workspace in the same
  terminal. If you work with several workspaces, do not source any of
  them in your ``.bashrc``.

It is very common to replace the line ``source
/opt/ros/fuerte/setup.bash`` in the ``.bashrc`` to the command above,
so that whenever you create a new terminal, that environment is used.

You can verify the workspace using again ``rosws info``::

  $ rosws info
  workspace: ~/fuerte
  ROS_ROOT: /opt/ros/fuerte/share/ros

   Localname                 S SCM  Version-Spec UID  (Spec) URI  (Spec) (https://...)
   ---------                 - ---- ------------ ----------- -------------------------
   /opt/ros/fuerte/stacks                                    
   /opt/ros/fuerte/share                                     
   /opt/ros/fuerte/share/ros 

You see in the second output line that there is a defined ROS_ROOT in
our workspace.  The info table has many columns, all of which are
empty so far, we will get to that in a moment.  You may notice that
``rosws merge`` listed an added setup.sh, which is not shown in the
table, it is hidden because that entry is of no further interest to
you in your daily work.

The overlay now includes all packages that were installed in
``/opt/ros/fuerte``, which is by itself not very useful yet. However we
can now easily overlay installed packages.

Creating a sandbox directory for new packages
---------------------------------------------

New packages need to be put in a path that is in the variable
``ROS_PACKAGE_PATH``. All directories that are managed by ``rosws``,
i.e. that have been added using ``rosws`` are automatically added to the
``ROS_PACKAGE_PATH`` when the file ``setup.bash`` of the corresponding
workspace is sourced. Although new packages should always be put in
repositories that have been installed using ``rosws``, it can be very
convenient to have a sandbox directory where for instance packages
created during the tutorials can be put without requiring any
additional ``rosws`` commands. For that we create a new directory sandbox
and add it to the .rosinstall file::

  $ mkdir ~/fuerte/sandbox
  $ rosws set ~/fuerte/sandbox

.. note::
  Now, it is necessary to re-source ``~/fuerte/setup.bash`` to make
  sure that the updated ``ROS_PACKAGE_PATH`` is used::

    $ source ~/fuerte/setup.bash

You can verify the workspace using again ``rosws info``::

  $ cd ~/fuerte
  $ rosws info
  workspace: ~/fuerte
  ROS_ROOT: /opt/ros/fuerte/share/ros

   Localname                 S SCM  Version-Spec UID  (Spec) URI  (Spec) (https://...)
   ---------                 - ---- ------------ ----------- -------------------------
   sandbox
   /opt/ros/fuerte/stacks                                    
   /opt/ros/fuerte/share                                     
   /opt/ros/fuerte/share/ros

As you can see the sandbox folder is at the top of the list. This is
important, as early entries overlay later entries. You can also check
the ``ROS_PACKAGE_PATH``, it should be the same as the left column of
the table::

  $ echo $ROS_PACKAGE_PATH
  /home/user/fuerte/sandbox:/opt/ros/fuerte/stacks:/opt/ros/fuerte/share:/opt/ros/fuerte/share/ros


You can now create packages in the sandbox folder e.g. using
``roscreate-pkg``, and they will be found within the ROS_PACKAGE_PATH.

Adding repositories to the overlay
----------------------------------

Development normally happens in repositories and when installing
packages from source, they normally need to be checked out from a
repository and added to the ``ROS_PACKAGE_PATH``. This can easily be
done using ``rosws``. For instance, the following commands add the
development version of the stack turtlebot which is a Mercurial
repository::

  $ rosws set turtlebot --hg https://kforge.ros.org/turtlebot/turtlebot
  $ rosws update turtlebot

After re-sourcing setup.bash the new overlayed stack turtlebot should
be in your package path, i.e. ``roscd turtlebot`` should switch to the
directory ``~/fuerte/turtlebot``.

If a stack is already installed in ``/opt/ros/fuerte``, adding it
locally using ``rosws`` will shadow the existing stack, as long as
``rosws`` info lists the stack earlier than the ``/opt/ros/fuerte``
folders.

I.e. instead of the system installation, the stack in
``~/ros_workspace`` will be used. That way, it is possible to edit
existing packages by cloning them in the overlay.

This makes it possible for you to use different workspaces with
different versions of the same libraries without much hassle. Also
this allows multiple users on a robot to each have their own version
of libraries.


Combining merge with roslocate
------------------------------

A usecase that was considered in the design of ``rosws`` was to quickly
get ROS stacks into a workspace. The ``roslocate`` script uses an
online index to lookup stack or package source information by name.

We can pipe that information to ``rosws`` to add the definition to 
our workspace. 

As an example we will add the navigation stack. Just to show you what
is happening, we first call ``roslocate``::

  $ roslocate info navigation
  - hg:
      local-name: navigation
      meta:
        repo-name: wg-kforge
      uri: https://kforge.ros.org/navigation/navigation
      version: default

As you can see the command finds the required meta-information for a
stack or package by the given name ``navigation``. We can call
``roslocate info`` it again passing the output to "``rosws merge -``"::

  $ roslocate info navigation | rosws merge -
       Performing actions: 

       Add new elements:
    navigation    hg  https://kforge.ros.org/navigation/navigation   default

If you wanted, you could next checkout the source code calling ``rosws
update navigation``.


Updating repositories in an overlay
-----------------------------------

``rosws`` allows to update only a single repository or all repositories::

  $ rosws update navigation

updates only the stack navigation while::

  $ rosws update

updates all repositories.

Developing against multiple distributions
-----------------------------------------

As an example a developer might have the ROS navigation stack in versions 
electric stable, electric unstable and fuerte on his harddisk.

(You may not have more than one distribution when you start learning
ROS, but the next distribution will come, so it's good to be prepared.)

So as a developer, it is be good to create one local overlay
workspace for each distribution and variant to use::

  $ rosws init ~/fuerte /opt/ros/fuerte
  $ rosws init ~/electric /opt/ros/electric
  $ rosws init ~/electric_unstable /opt/ros/electric

It is useful to use such folders to manage different source 
checkouts of the same ROS package. Using the same folder and 
switching versions is very prone to mistakes and not recommended.

You can use each of these folders as an independent workspace.

.. note::
  It is generally not a good idea to change the distribution a ROS
  workspace is bound to. This often leads to confusing error messages
  because compiled files assume the wrong distribution.
