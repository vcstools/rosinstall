# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
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
import rosinstall.__version__

from rosinstall.helpers import ROSInstallException, get_ros_stack_path

# template for catkin fuerte, not valid for Groovy and beyond, to be
# removed once fuerte goes out of support
CATKIN_CMAKE_TOPLEVEL = """#
#  TOPLEVEL cmakelists
#
cmake_minimum_required(VERSION 2.8)
cmake_policy(SET CMP0003 NEW)
cmake_policy(SET CMP0011 NEW)

set(CMAKE_CXX_FLAGS_INIT "-Wall")

enable_testing()

include(${CMAKE_SOURCE_DIR}/workspace-config.cmake OPTIONAL)

list(APPEND CMAKE_PREFIX_PATH ${CMAKE_BINARY_DIR} ${CMAKE_BINARY_DIR}/cmake)

file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

if (IS_DIRECTORY ${CMAKE_SOURCE_DIR}/catkin)
  message(STATUS "+++ catkin")
  set(CATKIN_BUILD_PROJECTS "ALL" CACHE STRING
    "List of projects to build, or ALL for all.  Use to completely exclude certain projects from cmake traversal.")
  add_subdirectory(catkin)
else()
  find_package(catkin)
endif()

catkin_workspace()
"""

SHELL_HEADER = """# THIS IS AN AUTO-GENERATED FILE
# IT IS UNLIKELY YOU WANT TO EDIT THIS FILE BY HAND
# IF YOU WANT TO CHANGE THE ROS ENVIRONMENT VARIABLES
# USE THE rosinstall OR rosws TOOL INSTEAD.
# Generator version: %s
# see: http://www.ros.org/wiki/rosinstall
""" % rosinstall.__version__.version


def generate_catkin_cmake(path, catkinpp):
    with open(os.path.join(path, "CMakeLists.txt"), 'w') as cmake_file:
        cmake_file.write(CATKIN_CMAKE_TOPLEVEL)

    if catkinpp:
        with open(os.path.join(path, "workspace-config.cmake"), 'w') as config_file:
            config_file.write("set (CMAKE_PREFIX_PATH %s)" % catkinpp)


def generate_embedded_python():
    return """import sys
import os
import yaml

workspace_path = os.environ.get('ROS_WORKSPACE', os.path.abspath('.'))
filename = os.path.join(workspace_path, '.rosinstall')

if not os.path.isfile(filename):
  print('ERROR')
  sys.exit("There is no file at %s" % filename)

with open(filename, "r") as fhand:
  try:
    v = fhand.read();
  except Exception as e:
    print('ERROR')
    sys.exit("Failed to read file: %s %s " % (filename, str(e)))

try:
  y = yaml.load(v);
except Exception as e:
  print('ERROR')
  sys.exit("Invalid yaml in %s: %s " % (filename, str(e)))

if y is not None:

  # put all non-setupfile entries into ROS_PACKAGE_PATH
  paths = []
  for vdict in y:
    for k, v in vdict.items():
      if v is not None and k != "setup-file":
        path = os.path.join(workspace_path, v['local-name'])
        if not os.path.isfile(path):
          # add absolute path from workspace to relative paths
          paths.append(os.path.normpath(path))
        else:
          print('ERROR')
          sys.exit("ERROR: referenced path is a file, not a folder: %s" % path)
  output = ''
  # add paths in reverse order
  if len(paths) > 0:
    output += ':'.join(reversed(paths))

  # We also want to return the location of any setupfile elements
  output += 'ROSINSTALL_PATH_SETUPFILE_SEPARATOR'
  setupfile_paths = []
  for vdict in y:
    for k, v in vdict.items():
      if v is not None and k == "setup-file":
        path = os.path.join(workspace_path, v['local-name'])
        if not os.path.exists(path):
          print('ERROR')
          sys.exit("WARNING: referenced setupfile does not exist: %s" % path)
        elif os.path.isfile(path):
          setupfile_paths.append(path)
        else:
          print('ERROR')
          sys.exit("ERROR: referenced setupfile is a folder: %s" % path)
  output += ':'.join(setupfile_paths)

  # printing will store the result in the variable
  print(output)"""


def generate_setup_sh_text(workspacepath):
    '''
    generates the string that goes into setup.sh.

    Sadly we cannot infer the workspacepath from within the sourced
    file, previous hacks trying to determine it from the shell context
    all failed in corner cases.

    :param workspacepath: The path to the workspace
    '''

    pycode = generate_embedded_python()

    # overlay or standard
    text = """#!/usr/bin/env sh
%(header)s

# This setup.sh file has to parse .rosinstall file, and source similar
# setup.sh files recursively. In the course of recursion, shell
# variables get overwritten. This means that when returning from
# recursion, any variable may be in a different state

# These variables accumulate data through recursion and must only be
# reset and unset at the top level of recursion.

if [ x"$_ROSINSTALL_IN_RECURSION" != x"recurse" ] ; then
  # reset setupfile accumulator
  _SETUPFILES_ROSINSTALL=
  _ROS_PACKAGE_PATH_ROSINSTALL=
  # reset RPP before sourcing other setup files
  export ROS_PACKAGE_PATH=
fi

export ROS_WORKSPACE=%(wspath)s
if [ ! "$ROS_MASTER_URI" ] ; then export ROS_MASTER_URI=http://localhost:11311 ; fi
unset ROS_ROOT

unset _SETUP_SH_ERROR

# python script to read .rosinstall even when rosinstall is not installed
# this files parses the .rosinstall and sets environment variables accordingly
# The ROS_PACKAGE_PATH contains all elements in reversed order (for historic reasons)

# We store into _PARSED_CONFIG the result of python code,
# which is the ros_package_path and the list of setup_files to source
# Using python here to benefit of the pyyaml library
export _PARSED_CONFIG=`/usr/bin/env python << EOPYTHON

%(pycode)s
EOPYTHON`

if [ x"$_PARSED_CONFIG" = x"ERROR" ]; then
  echo 'Could not parse .rosinstall file' 1<&2
  _SETUP_SH_ERROR=1
fi

# using sed to split up ros_package_path and setupfile results
_ROS_PACKAGE_PATH_ROSINSTALL_NEW=`echo "$_PARSED_CONFIG" | sed 's,\(.*\)ROSINSTALL_PATH_SETUPFILE_SEPARATOR\(.*\),\\1,'`
if [ ! -z "$_ROS_PACKAGE_PATH_ROSINSTALL_NEW" ]; then
  if [ ! -z "$_ROS_PACKAGE_PATH_ROSINSTALL" ]; then
    export _ROS_PACKAGE_PATH_ROSINSTALL=$_ROS_PACKAGE_PATH_ROSINSTALL:$_ROS_PACKAGE_PATH_ROSINSTALL_NEW
  else
    export _ROS_PACKAGE_PATH_ROSINSTALL=$_ROS_PACKAGE_PATH_ROSINSTALL_NEW
  fi
fi

_SETUPFILES_ROSINSTALL_NEW=`echo "$_PARSED_CONFIG" | sed 's,\(.*\)'ROSINSTALL_PATH_SETUPFILE_SEPARATOR'\(.*\),\\2,'`
if [ ! -z "$_SETUPFILES_ROSINSTALL_NEW" ]; then
  if [ ! -z "$_SETUPFILES_ROSINSTALL" ]; then
    _SETUPFILES_ROSINSTALL=$_SETUPFILES_ROSINSTALL_NEW:$_SETUPFILES_ROSINSTALL
  else
    _SETUPFILES_ROSINSTALL=$_SETUPFILES_ROSINSTALL_NEW
  fi
fi
unset _PARSED_CONFIG

# colon separates entries
_LOOP_SETUP_FILE=`echo $_SETUPFILES_ROSINSTALL | sed 's,\([^:]*\)[:]\(.*\),\\1,'`
# this loop does fake recursion, as the called setup.sh may work on
# the remaining elements in the _SETUPFILES_ROSINSTALL stack
while [ ! -z "$_LOOP_SETUP_FILE" ]
do
  # need to pop from stack before recursing, as chained setup.sh might rely on this
  _SETUPFILES_ROSINSTALL=`echo $_SETUPFILES_ROSINSTALL | sed 's,\([^:]*[:]*\),,'`
  if [ -f "$_LOOP_SETUP_FILE" ]; then
    _ROSINSTALL_IN_RECURSION=recurse
    . $_LOOP_SETUP_FILE
    unset _ROSINSTALL_IN_RECURSION
  else
    echo warn: no such file : "$_LOOP_SETUP_FILE"
  fi
  _LOOP_SETUP_FILE=`echo $_SETUPFILES_ROSINSTALL | sed 's,\([^:]*\)[:]\(.*\),\\1,'`
done

unset _LOOP_SETUP_FILE
unset _SETUPFILES_ROSINSTALL

# prepend elements from .rosinstall file to ROS_PACKAGE_PATH
# ignoring duplicates entries from value set by setup files
export ROS_PACKAGE_PATH=`/usr/bin/env python << EOPYTHON
import os
ros_package_path = os.environ.get('ROS_PACKAGE_PATH', '')
original_elements = ros_package_path.split(':')
ros_package_path2 = os.environ.get('_ROS_PACKAGE_PATH_ROSINSTALL', '')
new_elements = ros_package_path2.split(':')
new_elements = [path for path in new_elements if path]

for original_path in original_elements:
  if original_path and original_path not in new_elements:
    new_elements.append(original_path)
print(':'.join(new_elements))
EOPYTHON`

unset _ROS_PACKAGE_PATH_ROSINSTALL

# restore ROS_WORKSPACE in case other setup.sh changed/unset it
export ROS_WORKSPACE=%(wspath)s

# if setup.sh did not set ROS_ROOT (pre-fuerte)
if [ -z "${ROS_ROOT}" ]; then
  # using ROS_ROOT now being in ROS_PACKAGE_PATH
  export _ROS_ROOT_ROSINSTALL=`/usr/bin/env python << EOPYTHON
import sys, os;
if 'ROS_PACKAGE_PATH' in os.environ:
  pkg_path = os.environ['ROS_PACKAGE_PATH']
  for path in pkg_path.split(':'):
    if (os.path.basename(path) == 'ros'
        and os.path.isfile(os.path.join(path, 'stack.xml'))):
      print(path)
      break
EOPYTHON`

  if [ ! -z "${_ROS_ROOT_ROSINSTALL}" ]; then
    export ROS_ROOT=$_ROS_ROOT_ROSINSTALL
    export PATH=$ROS_ROOT/bin:$PATH
    export PYTHONPATH=$ROS_ROOT/core/roslib/src:$PYTHONPATH
  fi
unset _ROS_ROOT_ROSINSTALL
fi

if [ ! -z "$_SETUP_SH_ERROR" ]; then
  # return failure code when sourcing file
  false
fi
""" % {'header': SHELL_HEADER, 'wspath': workspacepath, 'pycode': pycode}

    return text


def generate_setup_bash_text(shell):
    '''
    Generates the contents that go into a setup.bash or setup.zsh
    file.  The intent of such a file is to enable shell extensions,
    such as special ros commands and tab completion.  The generation
    is complex because the setup of the system changed between ROS
    electric and fuerte. In fuerte, the distro setup.sh also loads
    distro rosbash based on CATKIN_SHELL. Before fuerte, it is up to
    setup.bash to do so.
    '''
    if shell == 'bash':
        script_path = """
SCRIPT_PATH="${BASH_SOURCE[0]}";
if([ -h "${SCRIPT_PATH}" ]) then
  while([ -h "${SCRIPT_PATH}" ]) do SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`; done
fi
export OLDPWDBAK=$OLDPWD
pushd . > /dev/null
cd `dirname ${SCRIPT_PATH}` > /dev/null
SCRIPT_PATH=`pwd`;
popd  > /dev/null
export OLDPWD=$OLDPWDBAK
"""
        call_setup_sh = ". $SCRIPT_PATH/setup.sh"
    elif shell == 'zsh':
        script_path = 'SCRIPT_PATH="$(dirname $0)"'
        call_setup_sh = """
emulate sh # emulate POSIX
. $SCRIPT_PATH/setup.sh
emulate zsh # back in zsh
"""
    else:
        raise ROSInstallException("%s shell unsupported." % shell)

    text = """#!/usr/bin/env %(shell)s
%(header)s

CATKIN_SHELL=%(shell)s

%(script_path)s

# Load the path of this particular setup.%(shell)s

if [ ! -f "$SCRIPT_PATH/setup.sh" ]; then
  echo "Bug: shell script unable to determine its own location: $SCRIPT_PATH"
  return 22
fi

# unset _ros_decode_path (function of rosbash) to check later whether setup.sh has sourced ros%(shell)s
unset -f _ros_decode_path 1> /dev/null 2>&1

%(call_setup_sh)s

# if we have a ROS_ROOT, then we might need to source rosbash (pre-fuerte)
if [ ! -z "${ROS_ROOT}" ]; then
  # check whether setup.sh also already sourced rosbash
  # Cannot rely on $? due to set -o errexit in build scripts
  RETURNCODE=`type _ros_decode_path 2> /dev/null | grep function 1>/dev/null 2>&1 || echo error`

  # for ROS electric and before, source rosbash
  if [ ! "$RETURNCODE" = "" ]; then
    RETURNCODE=`rospack help 1> /dev/null 2>&1 || echo error`
    if  [ "$RETURNCODE" = "" ]; then
      ROSSHELL_PATH=`rospack find rosbash`/ros%(shell)s
      if [ -e "$ROSSHELL_PATH" ]; then
        . $ROSSHELL_PATH
      fi
    else
      echo "rospack could not be found, you cannot have ros%(shell)s features until you bootstrap ros"
    fi
  fi
fi
""" % {'shell': shell,
       'script_path': script_path,
       'call_setup_sh': call_setup_sh,
       'header': SHELL_HEADER}
    return text


def generate_setup(config, no_ros_allowed=False):
    ros_root = get_ros_stack_path(config)
    if ros_root is None:
        if not no_ros_allowed:
            candidates = []
            for t in config.get_config_elements():
                if os.path.basename(t.get_local_name()) == 'ros':
                    candidates.append(t.get_path())
            raise ROSInstallException("""
No 'ros' stack detected in candidates %s.
Please add the location of a ros distribution to this command.

See http://ros.org/wiki/rosinstall.""" % (candidates))

    text = generate_setup_sh_text(workspacepath=config.get_base_path())
    setup_path = os.path.join(config.get_base_path(), 'setup.sh')
    with open(setup_path, 'w') as fhand:
        fhand.write(text)

    for shell in ['bash', 'zsh']:
        text = generate_setup_bash_text(shell)
        setup_path = os.path.join(config.get_base_path(), 'setup.%s' % shell)
        with open(setup_path, 'w') as fhand:
            fhand.write(text)
