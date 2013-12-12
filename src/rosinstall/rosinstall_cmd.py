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


import os
import subprocess
from wstool.multiproject_cmd import cmd_persist_config as multipersist
from rosinstall import setupfiles
from wstool.helpers import ROSINSTALL_FILENAME
from rosinstall.helpers import is_path_ros


def cmd_persist_config(config, config_filename=ROSINSTALL_FILENAME, header=''):
    ## Save .rosinstall
    header = (header or '') + """\
# IT IS UNLIKELY YOU WANT TO EDIT THIS FILE BY HAND,
# UNLESS FOR REMOVING ENTRIES.
# IF YOU WANT TO CHANGE THE ROS ENVIRONMENT VARIABLES
# USE THE rosinstall TOOL INSTEAD.
# IF YOU CHANGE IT, USE rosinstall FOR THE CHANGES TO TAKE EFFECT
"""
    multipersist(config, config_filename, header)


def _ros_requires_boostrap(config):
    """
    Tests whether workspace contains a core ros stack, to decide
    whether to rosmake

    :param config: workspace config object
    """
    for entry in config.get_source():
        if is_path_ros(os.path.join(config.get_base_path(), entry.get_local_name())):
            # we assume that if any of the elements we installed came
            # from a VCS source, a bootsrap might be useful
            if entry.get_scmtype() is not None:
                return True
    return False


def cmd_maybe_refresh_ros_files(config):
    """
    Regenerates setup.* files if they exist already

    :param config: workspace config object
    """
    if (os.path.isfile(os.path.join(config.get_base_path(), 'setup.sh'))):
        print("Overwriting setup.sh, setup.bash, and setup.zsh in %s" %
              config.get_base_path())
        setupfiles.generate_setup(config, no_ros_allowed=True)


def cmd_generate_ros_files(config, path, nobuild=False, rosdep_yes=False, catkin=False, catkinpp=None, no_ros_allowed=False):
    """
    Generates ROS specific setup files

    :param nobuild: Unless True, invokes rosmake to build all packages if core ROS stack is detected
    :param rosdep_yes: If True, adds --rosdep-yes to rosmake command
    :param catkin: if true, generates catkin(fuerte) CMakeLists.txt instead of invoking rosmake
    :param catkinpp: Prefix path for catkin if generating for catkin
    :param no_ros_allowed: if true, does not look for a core ros stack
    """

    # Catkin must be enabled if catkinpp is set
    if catkinpp is not None:
        catkin = True

    ## bootstrap the build if installing ros
    if catkin:
        setupfiles.generate_catkin_cmake(path, catkinpp)

    else:  # DRY install case
        ## Generate setup.sh and save
        print("(Over-)Writing setup.sh, setup.bash, and setup.zsh in %s" %
              config.get_base_path())
        setupfiles.generate_setup(config, no_ros_allowed)

        if _ros_requires_boostrap(config) and not nobuild:
            print("Bootstrapping ROS build")
            rosdep_yes_insert = ""
            if rosdep_yes:
                rosdep_yes_insert = " --rosdep-yes"
            ros_comm_insert = ""
            if 'ros_comm' in [os.path.basename(tree.get_path()) for tree in config.get_config_elements()]:
                print("Detected ros_comm bootstrapping it too.")
                ros_comm_insert = " ros_comm"
            cmd = ("source %s && rosmake ros%s --rosdep-install%s" %
                   (os.path.join(path, 'setup.sh'),
                    ros_comm_insert,
                    rosdep_yes_insert))
            subprocess.check_call(cmd, shell=True, executable='/bin/bash')
