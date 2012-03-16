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

class ROSInstallException(Exception): pass

ROSINSTALL_FILENAME = ".rosinstall"


def is_path_stack(path):
  """
  
  @return: True if the path provided is the root of a stack.
  """
  stack_path = os.path.join(path, 'stack.xml')
  if os.path.isfile(stack_path):
    return True
  return False

def is_path_ros(path):
  """
  warning: exits with code 1 if stack document is invalid
  @param path: path of directory to check
  @type  path: str
  @return: True if path points to the ROS stack
  @rtype: bool
  """
  if path is None:
    return False
  stack_path = os.path.join(path, 'stack.xml')
  if os.path.isfile(stack_path):
    return 'ros' == os.path.basename(path)
  return False


def get_ros_stack_path(config):
  rp = None
  for t in config.get_config_elements():
    if is_path_ros(t.get_path()):
      if rp is not None:
        raise ROSInstallException("Two ros roots defined in config, delete one: %s %s"%(rp, t.get_path()))
      rp = t.get_path()
  return rp


def get_ros_package_path(config):
  """ Return the simplifed ROS_PACKAGE_PATH """
  code_trees = []
  for t in reversed(config.get_config_elements()):
    if not is_path_ros(t.get_path()):
      if not os.path.isfile(t.get_path()):
        code_trees.append(t.get_path())
  return code_trees

