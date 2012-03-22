Changelog
=========

0.6
---



0.6.11
------

- bugfix rosinstall --snapshot not working (refactoring victim)
- minor bugfixes on options of rosws update
- pyyaml added as dependency in setup.py, rather than failure on import

0.6.10
------

- undoing bash completion install as it fails with easy_install

0.6.9
-----

- fix #25 rejection of git short-hand notation user@server:file
- Create a .rosinstall.bak on every rewrite
- diverse minor bugs
- strictly accept only one ros root in workspace
- parallelity is non-default for init and update, options -j and --parallel like cmake
- setup.sh also infers ROS_ROOT from .rosinstall
- docs contain tutorial for rosws
- more verbose out of paralelity
- added this changelog
- more versatile info command --only option
- bugfix unable to add plain folder
- allow to set version to None

0.6.8
-----

- REP110 implemented as rosws, not py-rosws
- Restructured rosws command, removed rosws install
- improved information given with merge
- merge reads from stdin

0.6.7
-----

(does not exist)

0.6.6
-----

- using thread pool
- Bugfix busy waiting bug
- bugfix sourcing setup.bash leading to build server failure

0.6.5 (unstable)
----------------

- undo deployment of contrib/rosws.shell, did not work

0.6.4 (defective)
-----------------

- deployment of contrib/rosws.shell
- better exception handling
- better debug output
- dropped rosws dependency to ROS

0.6.3 (unstable)
----------------

- adapted to vcstools change
- major bugfix ROS_PACKGAE_PATH only consisted of relative paths.

0.6.2 (unstable)
----------------

- stricter validation, no non-scm entries within scm entries
- minor issues around rosbash

0.6.1 (unstable)
----------------

- bugfix tar not supported
- bugfix inofficial 'meta' attribute causes failure

0.6.0 (unstable)
----------------

- new py-rosws CLI as reference implementation for REP110
- parallel operations diff, stat, install
- Generally stricter semantics and checking for validity of inputs
- No more recursing into other .rosinstall files
- roughly 100 more unit tests
- refactored single rosinstall script into several python module
- setup.sh parses .rosinstall to generate ROS_PACKAGE_PATH


0.5
---

0.5.30
------

- small bugfix location-find with rospack 
- small bugfix roszsh not found
- support top-level setup-file element for fuerte

0.5.29
------

- removed dependency to datetime again

0.5.28
------

- add allegedly missing dependency to dateutil

0.5.27
------

- split up integration tests and testing against local repos
- support for fuerte setup-file element

0.5.26
------

- initial support of the preliminary opt/ros/fuerte/.rosinstall file

0.5.25
------

- fix rosbash for fuerte

0.5.24
------

- Fixed string defect

0.5.23 (defective)
------------------

- basic catkin support
- option -n to not build ros
- fix rstripping of ``/`` in uri

0.5.22
------

- fix #3683
- basic Sphinx support
- other fixes

0.5.21
------

- Moved to kforge
