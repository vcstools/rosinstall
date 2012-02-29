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
import multiproject_cmd
import rosinstall.setupfiles
from rosinstall.helpers import ROSInstallException, __ROSINSTALL_FILENAME

def cmd_persist_config_file(config):
  ## Save .rosinstall
  header = """# THIS IS A FILE WHICH IS MODIFIED BY rosinstall
# IT IS UNLIKELY YOU WANT TO EDIT THIS FILE BY HAND,
# UNLESS FOR REMOVING ENTRIES.
# IF YOU WANT TO CHANGE THE ROS ENVIRONMENT VARIABLES
# USE THE rosinstall TOOL INSTEAD.
# IF YOU CHANGE IT, USE rosinstall FOR THE CHANGES TO TAKE EFFECT
"""
  multiproject_cmd.cmd_persist_config(config, __ROSINSTALL_FILENAME, header)

def _ros_requires_boostrap(config):
  """Whether we might need to bootstrap ros"""
  for entry in config.get_source():
    if rosinstall.helpers.is_path_ros(entry.get_path()):
      # we assume that if any of the elements we installed came
      # from a VCS source, a bootsrap might be useful
      if entry.get_scmtype() is not None:
        return True
  return False
  
def cmd_generate_ros_files(config, path, nobuild = False, rosdep_yes = False, catkin = False, catkinpp = None):
  """
  Generates ROS specific setup files
  """
 
  ## bootstrap the build if installing ros
  if catkin:
    setupfiles.generate_catkin_cmake(path, catkinpp)    
                
  else: # DRY install case
    ## Generate setup.sh and save
    rosinstall.setupfiles.generate_setup(config)

    if _ros_requires_boostrap(config) and not nobuild:
      print("Bootstrapping ROS build")
      rosdep_yes_insert = ""
      if rosdep_yes:
        rosdep_yes_insert = " --rosdep-yes"
      ros_comm_insert = ""
      if 'ros_comm' in [os.path.basename(tree.path) for tree in config.trees]:
        print("Detected ros_comm bootstrapping it too.")
        ros_comm_insert = " ros_comm"
      subprocess.check_call("source %s && rosmake ros%s --rosdep-install%s" % (os.path.join(path, 'setup.sh'), ros_comm_insert, rosdep_yes_insert), shell=True, executable='/bin/bash')
    print("\nrosinstall update complete.\n\nNow, type 'source %s/setup.bash' to set up your environment.\nAdd that to the bottom of your ~/.bashrc to set it up every time.\n\nIf you are not using bash please see http://www.ros.org/wiki/rosinstall/NonBashShells " % path)
  
    
