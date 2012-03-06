#!/usr/bin/env python
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
import copy
import yaml
import subprocess
import tempfile

import rosinstall
import rosinstall.helpers

from test.scm_test_base import AbstractFakeRosBasedTest, _create_yaml_file, _create_config_elt_dict

class RosinstallCommandlineOverlays(AbstractFakeRosBasedTest):
    """test creating parallel rosinstall env with overlayed stacks"""
      
    def setUp(self):
        """runs rosinstall with generated self.simple_rosinstall to create local rosinstall env
        and creates a directory for a second local rosinstall env"""
        AbstractFakeRosBasedTest.setUp(self)

        # setup a rosinstall env as base for further tests
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))

        self.new_directory = tempfile.mkdtemp()
        self.directories["new_ros_env"] = self.new_directory

    def test_Rosinstall_rosinstall_file_input(self):
        """uses base rosinstall with ros and git repo"""
                          
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.new_directory, self.directory])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        stream = open(os.path.join(self.new_directory, '.rosinstall'), 'r')
        yamlsrc = yaml.load(stream)
        stream.close()
        self.assertEqual(2, len(yamlsrc))
        self.assertEqual('other', yamlsrc[0].keys()[0])
        self.assertEqual('other', yamlsrc[1].keys()[0])
        
    def test_Rosinstall_rosinstall_file_input_ros_only(self):
        """uses base ros folder"""
        local_rosinstall = os.path.join(self.test_root_path, "local.rosinstall")
        # invalid recursion itno some other rosinstall folder
        _create_yaml_file([_create_config_elt_dict("other", self.directory)],  local_rosinstall)
                          
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.new_directory, self.ros_path, local_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        stream = open(os.path.join(self.new_directory, '.rosinstall'), 'r')
        yamlsrc = yaml.load(stream)
        stream.close()
        self.assertEqual(1, len(yamlsrc))
        self.assertEqual('other', yamlsrc[0].keys()[0])

    def test_Rosinstall_rosinstall_file_input_add(self):
        """uses base ros folders and adds a stack"""
        local_rosinstall = os.path.join(self.test_root_path, "local2.rosinstall")
        # self.directory points invalidly at a folder containing a .rosinstall pointing to ros and gitrepo
        _create_yaml_file([_create_config_elt_dict("other", self.directory),
                           _create_config_elt_dict("hg", "gitrepo", self.hg_path)],
                          local_rosinstall)
                          
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.new_directory, self.ros_path, local_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        stream = open(os.path.join(self.new_directory, '.rosinstall'), 'r')
        yamlsrc = yaml.load(stream)
        stream.close()
        self.assertEqual(2, len(yamlsrc))
        self.assertEqual('other', yamlsrc[0].keys()[0])
        self.assertEqual('hg', yamlsrc[1].keys()[0])

    def test_Rosinstall_ros_with_folder(self):
        """Use a folder as a remote rosinstall location"""
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.new_directory, self.ros_path, self.directory])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ), cmd)


class RosinstallCommandlineOverlaysWithSetup(AbstractFakeRosBasedTest):
    """test creating parallel rosinstall env with overlayed stacks"""
      
    def setUp(self):
        """runs rosinstall with generated self.simple_rosinstall to create local rosinstall env
        and creates a second directory self.new_directory for a second local rosinstall env"""
        AbstractFakeRosBasedTest.setUp(self)

        self.simple_fuerte_rosinstall = os.path.join(self.test_root_path, "simple_fuerte.rosinstall")
        _create_yaml_file([_create_config_elt_dict("git", "ros", self.ros_path),
                           _create_config_elt_dict("setup-file", "setup.sh"),
                           _create_config_elt_dict("hg", "hgrepo", self.hg_path)],
                          self.simple_fuerte_rosinstall)
        
        # setup a rosinstall env as base for further tests
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.directory, self.simple_fuerte_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))

        self.new_directory = tempfile.mkdtemp()
        self.directories["new_ros_env"] = self.new_directory

    def test_Rosinstall_rosinstall_file_input_with_setupfile(self):
        local_rosinstall = os.path.join(self.test_root_path, "local.rosinstall")
        _create_yaml_file([_create_config_elt_dict("other", self.directory),
                           _create_config_elt_dict("hg", "hgrepo", self.hg_path)],
                          local_rosinstall)
                          
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.new_directory, self.ros_path, local_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        stream = open(os.path.join(self.new_directory, '.rosinstall'), 'r')
        yamlsrc = yaml.load(stream)
        stream.close()
        self.assertEqual(2, len(yamlsrc), yamlsrc)
        self.assertEqual('other', yamlsrc[0].keys()[0]) #ros
        self.assertEqual('hg', yamlsrc[1].keys()[0]) #hg_repo


    def test_Rosinstall_ros_with_folder_and_setupfile(self):
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.new_directory, self.directory])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ), cmd)
        stream = open(os.path.join(self.new_directory, '.rosinstall'), 'r')
        yamlsrc = yaml.load(stream)
        stream.close()
        self.assertEqual(3, len(yamlsrc))
        self.assertEqual('other', yamlsrc[0].keys()[0])
        self.assertEqual('setup-file', yamlsrc[1].keys()[0])
        self.assertEqual('other', yamlsrc[2].keys()[0])

