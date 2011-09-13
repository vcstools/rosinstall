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
import stat
import struct
import sys
import unittest

import rosinstall.helpers


class ConditionalAbspath(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_conditional_abspath(self):
        path = "foo"
        self.assertEqual(os.path.normpath(os.path.join(os.getcwd(), path)), rosinstall.helpers.conditional_abspath(path))
        
    def test_is_path_stack(self):
        self.assertTrue(rosinstall.helpers.is_path_stack(os.path.join("test", "example_dirs", "ros")))
        self.assertFalse(rosinstall.helpers.is_path_stack(os.path.join("test", "example_dirs", "roscpp")))

    def test_is_path_ros(self):
        self.assertTrue(rosinstall.helpers.is_path_stack((os.path.join("test", "example_dirs", "ros"))))
        self.assertFalse(rosinstall.helpers.is_path_stack((os.path.join("test", "example_dirs", "roscpp"))))

    def test_get_yaml_from_uri_from_file(self):
        file = os.path.join("test", "example.yaml")
        y = rosinstall.helpers.get_yaml_from_uri(file)
        
        self.assertTrue("text" in y)
        self.assertTrue(y["text"] == "foobar")

        self.assertTrue("number" in y)
        self.assertTrue(y["number"] == 2)

    def test_get_yaml_from_uri_from_missing_file(self):
        file = "/asdfasdfasdfasfasdf_does_not_exist"
        y = rosinstall.helpers.get_yaml_from_uri(file)
        self.assertEqual(y, None)

#TODO Fix this
#    def test_get_yaml_from_uri_from_non_yaml_file(self):
#        file = os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "Makefile")
#        y = rosinstall.helpers.get_yaml_from_uri(file)
#        self.assertEqual(y, None)

    def test_get_yaml_from_uri_from_url(self):
        url = "http://www.ros.org/rosinstalls/boxturtle_base.rosinstall"
        y = rosinstall.helpers.get_yaml_from_uri(url)
        
        ros_found = False
        for e in y:
            if "svn" in e:
                element = e["svn"]
                if "local-name" in element:
                    if element["local-name"] == "ros":
                        ros_found = True
        self.assertTrue(ros_found)

    def test_get_yaml_from_uri_from_invalid_url(self):
        url = "http://www.ros.org/invalid"
        y = rosinstall.helpers.get_yaml_from_uri(url)
        self.assertEqual(y, None)

