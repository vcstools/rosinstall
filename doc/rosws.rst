rosws: A tool for managing source code workspaces
=================================================

rosws can do anything that rosinstall can do, and more.  Most commands
will just do a small subset of a single rosinstall invocation, so
users can more easily understand and control the tool actions.

The main difference to rosinstall is that rosws uses an SCM like
syntax of command keywords. 

The motivation for rosws was that many users were overwhelmed with the
number of things rosinstall does with just one command, and ended up
not using it at all. rosws does much less and informs the user more
about what it will do, so that users should feel safer and also should
more easily understand what the tool is doing.

The single most important feature that is different to rosinstall is
the info command. The second most is the set command.

The general design philosophy for rosws wa that each command should
just perform a single task, not multiple tasks.

The command was introduced with [REP110]_.

.. contents:: Contents
   :depth: 3



Usage
-----

::

  rosws is a command to manipulate ROS workspaces. rosws replaces its predecessor rosinstall.
  
  Official usage:
    rosws CMD [ARGS] [OPTIONS]
  
  rosws will try to infer install path from context
  
  Type 'rosws help' for usage.
  Options:
    help            provide help for commands
    init            set up a directory as workspace
    set             add or changes one entry from your workspace config
    merge           merges your workspace with another config set
    remove (rm)     remove an entry from your workspace config, without deleting files
    update (up)     update or check out some of your config elements
    info            Overview of some entries
    status (st)     print the change status of files in some SCM controlled entries
    diff (di)       print a diff over some SCM controlled entries
    regenerate      create ROS workspace specific setup files


init
~~~~

set up a directory as workspace

rosws init does the following:

 1. Reads folder/file/web-uri SOURCE_PATH looking for a rosinstall yaml
 2. Creates new .rosinstall file at TARGET-PATH configured
 3. Generates ROS setup files

SOURCE_PATH can e.g. be a folder like /opt/ros/electric
If PATH is not given, uses current folder.

::

  Usage: rosws init [TARGET_PATH [SOURCE_PATH]]?
 
  Options::
  
    -h, --help            show this help message and exit
    -c, --catkin          Declare this is a catkin build.
    --cmake-prefix-path=CATKINPP
                          Where to set the CMAKE_PREFIX_PATH
    --continue-on-error   Continue despite checkout errors
    -j JOBS, --parallel=JOBS
                          How many parallel threads to use for installing

Examples::

  $ rosws init ~/fuerte /opt/ros/fuerte


set
~~~

add or changes one entry from your workspace config
The command will infer whether you want to add or modify an entry. If
you modify, it will only change the details you provide, keeping
those you did not provide. if you only provide a uri, will use the
basename of it as localname unless such an element already exists.

The command only changes the configuration, to checkout or update
the element, run rosws update afterwards.

::

  Usage: rosws set [localname] [SCM-URI]?  [--(detached|svn|hg|git|bzr)] [--version=VERSION]]
  
  Options:
    -h, --help            show this help message and exit
    --detached            make an entry unmanaged (default for new element)
    -v VERSION, --version-new=VERSION
                          point SCM to this version
    --git                 make an entry a git entry
    --svn                 make an entry a subversion entry
    --hg                  make an entry a mercurial entry
    --bzr                 make an entry a bazaar entry
    -y, --confirm         Do not ask for confirmation
    -u, --update          update repository after set
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use

Examples::

  $ rosws set robot_model --hg https://kforge.ros.org/robotmodel/robot_model
  $ rosws set robot_model --version robot_model-1.7.1
  $ rosws set robot_model --detached



merge
~~~~~

The command merges config with given other rosinstall element sets, from files
or web uris.

The default workspace will be inferred from context, you can specify one using
-t.

By default, when an element in an additional URI has the same
local-name as an existing element, the existing element will be
replaced. In order to ensure the ordering of elements is as
provided in the URI, use the option ``--merge-kill-append``.

::

  Usage: rosws merge [URI] [OPTIONS]
  
  Options:
    -h, --help            show this help message and exit
    -a, --merge-kill-append
                          merge by deleting given entry and appending new one
    -k, --merge-keep      (default) merge by keeping existing entry and
                          discarding new one
    -r, --merge-replace   merge by replacing given entry with new one
                          maintaining ordering
    -y, --confirm-all     do not ask for confirmation unless strictly necessary
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use

Examples::

  $ rosws merge someother.rosinstall

You can use '-' to pipe in input, as an example::

  $ roslocate info robot_mode | rosws merge -

  
update
~~~~~~

update or check out some of your config elements

This command calls the SCM provider to pull changes from remote to
your local filesystem. In case the url has changed, the command will
ask whether to delete or backup the folder.

::

  Usage: rosws update [localname]*

  Options:
    -h, --help            show this help message and exit
    --delete-changed-uris
                          Delete the local copy of a directory before changing
                          uri.
    --abort-changed-uris  Abort if changed uri detected
    --continue-on-error   Continue despite checkout errors
    --backup-changed-uris=BACKUP_CHANGED
                          backup the local copy of a directory before changing
                          uri to this directory.
    -j JOBS, --parallel=JOBS
                          How many parallel threads to use for installing
    -v, --verbose         Whether to print out more information
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use


Examples::

  $ rosws update -t ~/fuerte
  $ rosws update robot_model geometry



info
~~~~

Overview of some entries

The Status (S) column shows
 x  for missing
 L  for uncommited (local) changes
 V  for difference in version and/or remote URI
 C  for difference in local and remote versions

The 'Version-Spec' column shows what tag, branch or revision was given
in the .rosinstall file. The 'UID' column shows the unique ID of the
current (and specified) version. The 'URI' column shows the configured
URL of the repo.

If status is V, the difference between what was specified and what is
real is shown in the respective column. For SVN entries, the url is
split up according to standard layout (trunk/tags/branches).  The
ROS_PACKAGE_PATH follows the order of the table, earlier entries
overlay later entries.

When given one localname, just show the data of one element in list
form.
This also has the generic properties element which is usually empty.

The ``--only`` option accepts keywords: ['path', 'localname', 'version',
'revision', 'cur_revision', 'uri', 'cur_uri', 'scmtype']

::
  
  Usage: rosws info [localname]* [OPTIONS]
  
  
  Options:
    -h, --help            show this help message and exit
    --root                Show workspace root path
    --data-only           Does not provide explanations
    --no-pkg-path         Suppress ROS_PACKAGE_PATH.
    --pkg-path-only       Shows only ROS_PACKAGE_PATH separated by ':'.
                          Supercedes all other options.
    --only=ONLY           Shows comma-separated lists of only given comma-
                          separated attribute(s).
    --yaml                Shows only version of single entry. Intended for
                          scripting.
    --fetch               When used, retrieves version information from remote
                          (takes longer).
    -u, --untracked       Also show untracked files as modifications
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use

Examples::

  $ rosws info -t ~/ros/fuerte
  $ rosws info robot_model
  $ rosws info --yaml
  $ rosws info --only=path,cur_uri,cur_revision robot_model geometry


    
    
status
~~~~~~

print the change status of files in some SCM controlled entries. The status
columns meanings are as the respective SCM defines them.

::

  Usage: rosws status [localname]* 
  
  Options:
    -h, --help            show this help message and exit
    --untracked           Also shows untracked files
    -t WORKSPACE, --target-workspace=WORKSPACE
                          which workspace to use

diff
~~~~

print a diff over some SCM controlled entries
    
::

  Usage: rosws diff [localname]* 

  Options:
    -h, --help            show this help message and exit
    --untracked           Also shows untracked files
    -t WORKSPACE, --target-workspace=WORKSPACE
                        which workspace to use
  
regenerate
~~~~~~~~~~

remove an entry from your workspace config, without deleting files

this command without options generates files setup.sh, setup.bash and
setup.zsh. Note that doing this is unnecessary in general, as these
files do not change anymore, unless you change from one ROS distro to
another (which you should never do like this, create a separate new
workspace instead), or you deleted or modified any of those files
accidentally.

::

  Usage: rosws regenerate

  Options:
    -h, --help            show this help message and exit
    -c, --catkin          Declare this is a catkin build.
    --cmake-prefix-path=CATKINPP
                        Where to set the CMAKE_PREFIX_PATH

See also
--------

.. [REP110] SCM-like rosinstall command structure
  (http://www.ros.org/reps/rep-0110.html)
