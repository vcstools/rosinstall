# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
usage: rosinstall [OPTIONS] INSTALL_PATH [ROSINSTALL FILES OR DIRECTORIES]
see: http://www.ros.org/wiki/rosinstall

Common Option:
-n or --nobuild (don't perform a 'make core_cools' on the ros stack)

Type 'rosinstall --help' for usage.

Common invocations:

initial checkout:   rosinstall ~/ros "http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=diamondback&variant=ros-full&overlay=no"
subsequent update:  rosinstall ~/ros

"""

from __future__ import print_function
import os
import sys
from optparse import OptionParser
import yaml
import shutil

from rosinstall import rosinstall_cmd
from wstool import multiproject_cmd
from wstool.helpers import ROSINSTALL_FILENAME
import rosinstall.__version__


def usage():
    print(__doc__ % vars())
    exit(1)


def rosinstall_main(argv):
    if len(argv) < 2:
        usage()
    args = argv[1:]
    parser = OptionParser(usage="usage: rosinstall [OPTIONS] INSTALL_PATH [ROSINSTALL FILES OR DIRECTORIES]\n\n\
rosinstall does the following:\n\
  1. Merges all URIs into new or existing .rosinstall file at PATH\n\
  2. Checks out or updates all version controlled URIs\n\
  3. If ros stack is installed from source, calls rosmake after checkout or updates.\n\
  4. Generates/overwrites updated setup files\n\n\
If running with --catkin mode:\
  1. Merges all URIs into new or existing .rosinstall file at PATH\n\
  2. Checks out or updates all version controlled URIs\n\
  4. Generates/overwrites updated setup files and creates CMakeLists.txt at the root.\n\n\
URIs can be web urls to remote .rosinstall files, local .rosinstall files,\n\
git, svn, bzr, hg URIs, or other (local directories)\n\
Later URIs will shadow packages of earlier URIs.\n",
                          epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
    parser.add_option("-c", "--catkin", dest="catkin", default=False,
                      help="Declare this is a catkin build.",
                      action="store_true")
    parser.add_option("--cmake-prefix-path", dest="catkinpp", default=None,
                      help="Where to set the CMAKE_PREFIX_PATH, implies --catkin",
                      action="store")
    parser.add_option("--version", dest="version", default=False,
                      help="display version information",
                      action="store_true")
    parser.add_option("--verbose", dest="verbose", default=False,
                      help="display more information",
                      action="store_true")
    parser.add_option("-n", "--nobuild", dest="nobuild", default=False,
                      help="skip the build step for the ROS stack",
                      action="store_true")
    parser.add_option("--rosdep-yes", dest="rosdep_yes", default=False,
                      help="Pass through --rosdep-yes to rosmake",
                      action="store_true")
    parser.add_option("--continue-on-error", dest="robust", default=False,
                      help="Continue despite checkout errors",
                      action="store_true")
    parser.add_option("--delete-changed-uris", dest="delete_changed",
                      default=False,
                      help="Delete the local copy of a directory before changing uri.",
                      action="store_true")
    parser.add_option("--abort-changed-uris", dest="abort_changed",
                      default=False,
                      help="Abort if changed uri detected",
                      action="store_true")
    parser.add_option("--backup-changed-uris", dest="backup_changed",
                      default='',
                      help="backup the local copy of a directory before changing uri to this directory.",
                      action="store")
    parser.add_option("--diff", dest="vcs_diff",
                      default=False,
                      help="shows a combined diff over all SCM entries",
                      action="store_true")
    parser.add_option("--status", dest="vcs_status",
                      default=False,
                      help="shows a combined status command over all SCM entries",
                      action="store_true")
    parser.add_option("--status-untracked", dest="vcs_status_untracked",
                      default=False,
                      help="shows a combined status command over all SCM entries, also showing untracked files",
                      action="store_true")
    parser.add_option("-j", "--parallel", dest="jobs",
                      default=1,
                      help="How many parallel threads to use for installing",
                      action="store")
    parser.add_option(
        "--generate-versioned-rosinstall", dest="generate_versioned",
        default=None,
        help="generate a versioned rosinstall file", action="store")
    (options, args) = parser.parse_args(args)

    if options.version:
        print("rosinstall %s\n%s" % (rosinstall.__version__.version, multiproject_cmd.cmd_version()))
        sys.exit(0)

    if len(args) < 1:
        parser.error("rosinstall requires at least 1 argument")

    mode = 'prompt'
    if options.delete_changed:
        mode = 'delete'
    if options.abort_changed:
        if mode == 'delete':
            parser.error(
                "delete-changed-uris is mutually exclusive with abort-changed-uris")
        mode = 'abort'
    if options.backup_changed != '':
        if mode == 'delete':
            parser.error(
                "delete-changed-uris is mutually exclusive with backup-changed-uris")
        if mode == 'abort':
            parser.error(
                "abort-changed-uris is mutually exclusive with backup-changed-uris")
        mode = 'backup'

    # Catkin must be enabled if catkinpp is set
    if options.catkinpp:
        options.catkin = True

    # Get the path to the rosinstall
    options.path = os.path.abspath(args[0])

    config_uris = args[1:]

    config = multiproject_cmd.get_config(basepath=options.path,
                                         additional_uris=config_uris,
                                         config_filename=ROSINSTALL_FILENAME)

    if options.generate_versioned:
        filename = os.path.abspath(options.generate_versioned)
        source_aggregate = multiproject_cmd.cmd_snapshot(config)
        with open(filename, 'w') as fhand:
            fhand.write(yaml.safe_dump(source_aggregate))
        print("Saved versioned rosinstall of current directory %s to %s" %
              (options.path, filename))
        return True

    if options.vcs_diff:
        difflist = multiproject_cmd.cmd_diff(config)
        alldiff = []
        for entrydiff in difflist:
            if entrydiff['diff'] is not None and entrydiff['diff'] != '':
                alldiff.append(entrydiff['diff'])
        print('\n'.join(alldiff))
        return True

    if options.vcs_status or options.vcs_status_untracked:
        statuslist = multiproject_cmd.cmd_status(
          config,
          untracked=options.vcs_status_untracked)
        allstatus = ""
        for entrystatus in statuslist:
            if entrystatus['status'] is not None:
                allstatus += entrystatus['status']
        print(allstatus, end='')
        return True

    print("rosinstall operating on", options.path,
          "from specifications in rosinstall files ",
          ", ".join(config_uris))

    # includes ROS specific files
    print("(Over-)Writing %s" %
          os.path.join(options.path, ROSINSTALL_FILENAME))
    if(os.path.isfile(os.path.join(options.path, ROSINSTALL_FILENAME))):
        shutil.move(os.path.join(options.path, ROSINSTALL_FILENAME),
                    "%s.bak" % os.path.join(options.path, ROSINSTALL_FILENAME))
    rosinstall_cmd.cmd_persist_config(config)

    ## install or update each element
    install_success = multiproject_cmd.cmd_install_or_update(
        config,
        backup_path=options.backup_changed,
        mode=mode,
        robust=options.robust,
        num_threads=int(options.jobs),
        verbose=options.verbose)

    rosinstall_cmd.cmd_generate_ros_files(
        config,
        options.path,
        options.nobuild,
        options.rosdep_yes,
        options.catkin,
        options.catkinpp)

    if not install_success:
        print("Warning: installation encountered errors, but --continue-on-error was requested.    Look above for warnings.")

    print("\nrosinstall update complete.")
    if (options.catkin is False
        and options.catkinpp is None):

        print("\n\nNow, type 'source %s/setup.bash' to set up your environment.\nAdd that to the bottom of your ~/.bashrc to set it up every time.\n\nIf you are not using bash please see http://www.ros.org/wiki/rosinstall/NonBashShells " % os.path.abspath(options.path))
    return True
