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
import subprocess
import tempfile

import rosinstall
import rosinstall.helpers
import rosinstall.config

from test.scm_test_base import AbstractRosinstallBaseDirTest, _create_yaml_file, _create_config_elt_dict

class RosinstallCommandlineTest(AbstractRosinstallBaseDirTest):

    @classmethod
    def setUpClass(self):
        AbstractRosinstallBaseDirTest.setUpClass()

    def test_source_boxturtle(self):
        """install boxturtle into temp dir"""
        cmd = self.rosinstall_fn
        self.simple_rosinstall = os.path.join(self.directory, "simple.rosinstall")
        _create_yaml_file([_create_config_elt_dict("svn", "ros", 'https://code.ros.org/svn/ros/stacks/ros/tags/boxturtle'),
                           _create_config_elt_dict("svn", "ros_release", 'https://code.ros.org/svn/ros/stacks/ros_release/trunk')],
                          self.simple_rosinstall)
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertEqual(0, subprocess.call(cmd, env=self.new_environ))
        generated_rosinstall_filename = os.path.join(self.directory, ".rosinstall")
        self.assertTrue(os.path.exists(generated_rosinstall_filename))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "ros")))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "ros_release")))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "setup.sh")))
        source_yaml = rosinstall.config.get_yaml_from_uri(generated_rosinstall_filename)
        self.assertEqual(source_yaml, 
                         [{'svn': { 'uri': 'https://code.ros.org/svn/ros/stacks/ros/tags/boxturtle',
                                    'local-name': 'ros'} },
                          {'svn': { 'uri': 'https://code.ros.org/svn/ros/stacks/ros_release/trunk',
                                    'local-name': 'ros_release'} }
                          ])
        
    # def test_source_cturtle(self):
    #     TODO
        
    # def test_source_boxdiamondback(self):
    #     TODO
        
    # def test_source_boxelectric(self):
    #     TODO
