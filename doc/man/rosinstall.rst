:orphan:

rosdep manual page
==================

Synopsis
--------

**rosinstall** [*options*] <*install-path*> [*rosinstall files or directories*]...


Options
-------

**--version**
  Show program's version number and exit

**-h**, **--help**
  Show this help message and exit

**-n, --nobuild**
  Skip the build step for the ROS stack
  
**--rosdep-yes**
  Pass through --rosdep-yes to rosmake
  
**--continue-on-error**
  Continue despite checkout errors
  
**--delete-changed-uris**

  Delete the local copy of a directory before changing URI.
  
**--abort-changed-uris**

  Abort if changed uri detected

**--backup-changed-uris=BACKUP_CHANGED**

  Backup the local copy of a directory before changing URI to this directory.

**--generate-versioned-rosinstall=GENERATE_VERSIONED**

  Generate a versioned rosinstall file


Description
-----------

The **rosinstall** command can download source code trees from a variety of source control systems (e.g. Git, Mercurial, Bazaar, Subversion).  The rosinstall file format lets you specify multiple source code trees, which simplifies the process of creating development workspaces.

rosinstall does the following:

  1. Merges all URIs into new or existing .rosinstall file at PATH
  2. Checks out or updates all version controlled URIs
  3. Calls rosmake after checkout or updates
  4. Generates/overwrites updated setup files

Run "rosinstall -h" to access the built-in tool documentation.

See http://www.ros.org/wiki/rosinstall for more details

