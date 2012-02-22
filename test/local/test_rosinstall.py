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
        """uses base ros folders and overlays a stack"""
        local_rosinstall = os.path.join(self.test_root_path, "local.rosinstall")
        _create_yaml_file([_create_config_elt_dict("other", os.path.join(self.directory, 'ros')),
                           _create_config_elt_dict("hg", "hgrepo", self.hg_path)],
                          local_rosinstall)
                          
        cmd = self.rosinstall_fn
        cmd.extend([self.new_directory, local_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))


    def test_Rosinstall_ros_with_folder(self):
        """Use a folder as a remote rosinstall location"""
        cmd = copy.copy(self.rosinstall_fn)
        cmd.extend([self.new_directory, self.directory])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ), cmd)


