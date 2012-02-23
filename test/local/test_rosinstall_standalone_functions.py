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
from rosinstall.helpers import ROSInstallException
from rosinstall.config import Config
from rosinstall.config_yaml import PathSpec

class FunctionsTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

        
    def test_is_path_stack(self):
        self.assertTrue(rosinstall.helpers.is_path_stack(os.path.join("test", "example_dirs", "ros")))
        self.assertTrue(rosinstall.helpers.is_path_stack(os.path.join("test", "example_dirs", "ros_comm")))
        self.assertFalse(rosinstall.helpers.is_path_stack(os.path.join("test", "example_dirs", "roscpp")))

    def test_is_path_ros(self):
        self.assertTrue(rosinstall.helpers.is_path_ros((os.path.join("test", "example_dirs", "ros"))))
        self.assertFalse(rosinstall.helpers.is_path_ros(os.path.join("test", "example_dirs", "ros_comm")))
        self.assertFalse(rosinstall.helpers.is_path_ros((os.path.join("test", "example_dirs", "roscpp"))))

    def test_get_ros_stack_path(self):
        config = Config([PathSpec("foo"),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec(os.path.join("test", "example_dirs", "roscpp")),
                         PathSpec("bar")],
                        ".",
                        None)
        self.assertEqual(None, rosinstall.helpers.get_ros_stack_path(config))
        config = Config([PathSpec("foo"),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec(os.path.join("test", "example_dirs", "ros")),
                         PathSpec(os.path.join("test", "example_dirs", "roscpp")),
                         PathSpec("bar")],
                        ".",
                        None)
        self.assertEqual("test/example_dirs/ros", rosinstall.helpers.get_ros_stack_path(config))

    def test_get_ros_package_path(self):
        config = Config([],
                        "test/example_dirs",
                        None)
        self.assertEqual([], rosinstall.helpers.get_ros_package_path(config))
        config = Config([PathSpec("foo")],
                        "test/example_dirs",
                        None)
        self.assertEqual(['test/example_dirs/foo'], rosinstall.helpers.get_ros_package_path(config))
        config = Config([PathSpec("foo"),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec(os.path.join("test", "example_dirs", "ros")),
                         PathSpec(os.path.join("test", "example_dirs", "roscpp")),
                         PathSpec("bar")],
                        "test/example_dirs",
                        None)
        self.assertEqual(['test/example_dirs/bar', 'test/example_dirs/test/example_dirs/roscpp', 'test/example_dirs/test/example_dirs/ros', 'test/example_dirs/test/example_dirs/ros_comm', 'test/example_dirs/foo'], rosinstall.helpers.get_ros_package_path(config))
