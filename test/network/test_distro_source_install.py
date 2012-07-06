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
import rosinstall.config
from rosinstall.rosinstall_cli import rosinstall_main
from rosinstall.common import MultiProjectException
from rosinstall.config_yaml import get_yaml_from_uri, get_path_specs_from_uri
from nose.plugins.skip import SkipTest
from test.scm_test_base import AbstractRosinstallBaseDirTest, _create_yaml_file, _create_config_elt_dict

class RosinstallCommandlineTest(AbstractRosinstallBaseDirTest):

    @classmethod
    def setUpClass(self):
        AbstractRosinstallBaseDirTest.setUpClass()

    def _ros_found(self, yaml):
        ros_found = False
        for e in yaml:
            if "svn" in e:
                element = e["svn"]
                if "local-name" in element:
                    if element["local-name"] == "ros":
                        ros_found = True
            elif "tar" in e:
                element = e["tar"]
                if "local-name" in element:
                    if element["local-name"] == "ros":
                        ros_found = True
        return ros_found

    def _ros_found_path_spec(self, specs):
        ros_found = False
        for s in specs:
            if "svn" == s.get_scmtype() or "tar" == s.get_scmtype():
                if "ros" == s.get_path():
                    ros_found = True
        return ros_found
        
    def test_get_path_specs_from_uri_from_url(self):
        # boxturtle
        url = "http://www.ros.org/rosinstalls/boxturtle_base.rosinstall"
        path_specs = get_path_specs_from_uri(url)
        self.assertTrue(self._ros_found_path_spec(path_specs), "No ros element in boxturtle")
        # diamondback
        path_specs = get_path_specs_from_uri("http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=diamondback&variant=desktop-full&overlay=no")
        self.assertTrue(path_specs is not None)
        self.assertTrue(len(path_specs)>0)
        self.assertTrue(self._ros_found_path_spec(path_specs), "No ros element in diamondback")
        # electric
        path_specs = get_path_specs_from_uri("http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=electric&variant=desktop-full&overlay=no")
        self.assertTrue(path_specs is not None)
        self.assertTrue(len(path_specs)>0)
        self.assertTrue(self._ros_found_path_spec(path_specs), "No ros element in electric")

    def test_get_yaml_from_uri_from_url(self):
        # boxturtle
        url = "http://www.ros.org/rosinstalls/boxturtle_base.rosinstall"
        yaml = get_yaml_from_uri(url)
        self.assertTrue(self._ros_found(yaml), "No ros element in boxturtle")
        # diamondback
        yaml = get_yaml_from_uri("http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=diamondback&variant=desktop-full&overlay=no")
        self.assertTrue(yaml is not None)
        self.assertTrue(len(yaml)>0)
        self.assertTrue(self._ros_found(yaml), "No ros element in diamondback")
        # electric
        yaml = get_yaml_from_uri("http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=electric&variant=desktop-full&overlay=no")
        self.assertTrue(yaml is not None)
        self.assertTrue(len(yaml)>0)
        self.assertTrue(self._ros_found(yaml), "No ros element in electric")


    def test_get_yaml_from_uri_from_invalid_url(self):
        url = "http://invalidurl"
        try:
            get_yaml_from_uri(url)
            self.fail("Expected exception")
        except MultiProjectException:
            pass

        # valid but non-yaml
        url = "http://www.google.com"
        try:
            get_yaml_from_uri(url)
            self.fail("Expected exception")
        except MultiProjectException:
            pass
                
    def test_source_boxturtle(self):
        """install boxturtle into temp dir"""
        cmd = copy.copy(self.rosinstall_fn)
        self.simple_rosinstall = os.path.join(self.directory, "simple.rosinstall")
        _create_yaml_file([_create_config_elt_dict("svn", "ros", 'https://code.ros.org/svn/ros/stacks/ros/tags/boxturtle'),
                           _create_config_elt_dict("svn", "ros_release", 'https://code.ros.org/svn/ros/stacks/ros_release/trunk')],
                          self.simple_rosinstall)
        cmd.extend([self.directory, self.simple_rosinstall])
        self.assertTrue(rosinstall_main(cmd))
        generated_rosinstall_filename = os.path.join(self.directory, ".rosinstall")
        self.assertTrue(os.path.exists(generated_rosinstall_filename))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "ros")))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "ros_release")))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "setup.sh")))
        source_yaml = get_yaml_from_uri(generated_rosinstall_filename)
        self.assertEqual(source_yaml, 
                         [{'svn': { 'uri': 'https://code.ros.org/svn/ros/stacks/ros/tags/boxturtle',
                                    'local-name': 'ros'} },
                          {'svn': { 'uri': 'https://code.ros.org/svn/ros/stacks/ros_release/trunk',
                                    'local-name': 'ros_release'} }
                          ])
        self.assertEqual(0, subprocess.call(". %s"%os.path.join(self.directory, 'setup.sh') , shell=True, env=self.new_environ))
        self.assertEqual(0, subprocess.call(". %s"%os.path.join(self.directory, 'setup.bash') , shell=True, env=self.new_environ, executable='/bin/bash'))


        
    # def test_source_cturtle(self):
    #     TODO
        
    # def test_source_boxdiamondback(self):
    #     TODO
        
    # def test_source_boxelectric(self):
    #     TODO

