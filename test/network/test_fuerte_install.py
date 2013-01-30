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
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

import rosinstall
import rosinstall.helpers
import rosinstall.config
from rosinstall.rosinstall_cli import rosinstall_main
from rosinstall.common import MultiProjectException
from rosinstall.config_yaml import get_yaml_from_uri, get_path_specs_from_uri
from test.scm_test_base import AbstractRosinstallBaseDirTest, _create_yaml_file, _create_config_elt_dict
from test.network.distro_test_util import ros_found_in_yaml, ros_found_in_path_spec
from rosinstall.multiproject_cmd import get_config


class RosinstallFuerteTest(AbstractRosinstallBaseDirTest):

    @classmethod
    def setUpClass(self):
        AbstractRosinstallBaseDirTest.setUpClass()

    def test_get_path_specs_from_uri_from_url(self):
        # wet
        url = "http://ros.org/rosinstalls/fuerte-ros-full.rosinstall"
        path_specs = get_path_specs_from_uri(url)
        self.assertTrue(ros_found_in_path_spec(path_specs), "No ros element in fuerte %s, URL %s" % (path_specs, url))
        # dry
        url = "http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=fuerte&variant=desktop-full&overlay=no"
        path_specs = get_path_specs_from_uri(url)
        self.assertTrue(ros_found_in_path_spec(path_specs), "No ros element in fuerte %s, URL %s" % (path_specs, url))

    def test_get_yaml_from_uri_from_url(self):
        # wet
        url = "http://ros.org/rosinstalls/fuerte-ros-full.rosinstall"
        yaml_elements = get_yaml_from_uri(url)
        self.assertTrue(ros_found_in_yaml(yaml_elements), "No ros element in %s" % url)
        # dry (contains "other" ros element)
        url = "http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=fuerte&variant=desktop-full&overlay=no"
        yaml_elements = get_yaml_from_uri(url)
        self.assertTrue(ros_found_in_yaml(yaml_elements), "No ros element in %s" % url)

    def test_source(self):
        """checkout into temp dir and test setup files"""
        cmd = copy.copy(self.rosinstall_fn)
        url = "http://packages.ros.org/cgi-bin/gen_rosinstall.py?rosdistro=fuerte&variant=robot&overlay=no"
        self.simple_rosinstall = os.path.join(self.directory, "simple.rosinstall")
        response = urlopen(url)
        contents = response.read()
        with open(self.simple_rosinstall, 'w') as fhand:
            fhand.write(str(contents))
        config = get_config(self.directory, [self.simple_rosinstall])
        cmd.extend(['-j8', '--catkin', self.directory, self.simple_rosinstall])
        self.assertTrue(rosinstall_main(cmd))
        generated_rosinstall_filename = os.path.join(self.directory, ".rosinstall")
        self.assertTrue(os.path.exists(generated_rosinstall_filename))
        # fuerte core ros stacks are catkinized, installed via catkin workspace
        self.assertTrue(os.path.exists(os.path.join(self.directory, "common")))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "dynamic_reconfigure")))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "CMakeLists.txt")))
