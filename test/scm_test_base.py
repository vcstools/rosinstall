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
import io
import copy
import stat
import struct
import sys
import unittest
import subprocess
import tempfile
import urllib
import shutil

import rosinstall
import rosinstall.helpers

def _add_to_file(path, content):
     """Util function to append to file to get a modification"""
     f = io.open(path, 'a')
     f.write(content)
     f.close()

ROSINSTALL_CMD = os.path.join(os.getcwd(), 'scripts/rosinstall')

class AbstractRosinstallCLITest(unittest.TestCase):

     """Base class for cli tests"""
     @classmethod
     def setUpClass(self):
          self.new_environ = os.environ
          self.new_environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

class AbstractRosinstallBaseDirTest(AbstractRosinstallCLITest):
     """test class where each test method get its own fresh tempdir named self.directory"""
     
     def setUp(self):
          self.directories = {}
          self.directory = tempfile.mkdtemp()
          self.directories["base"] = self.directory
          self.rosinstall_fn = [ROSINSTALL_CMD, "-n"]

     def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        self.directories = {}
     
class AbstractSCMTest(AbstractRosinstallCLITest):
     """Base class for diff tests, setting up a tempdir self.test_root_path for a whole class"""
     @classmethod
     def setUpClass(self):
          AbstractRosinstallCLITest.setUpClass()
          self.test_root_path = tempfile.mkdtemp()
          self.directories = {}
          self.directories["root"] = self.test_root_path
       
          # setup fake ros root
          self.ros_path = os.path.join(self.test_root_path, "ros")
          os.makedirs(self.ros_path)
          _add_to_file(os.path.join(self.ros_path, "stack.xml"), u'<stack></stack>')
          _add_to_file(os.path.join(self.ros_path, "setup.sh"), u'export ROS_ROOT=`pwd`')
          self.local_path = os.path.join(self.test_root_path, "ws")
          os.makedirs(self.local_path)

     @classmethod
     def tearDownClass(self):
          for d in self.directories:
               shutil.rmtree(self.directories[d])
        
