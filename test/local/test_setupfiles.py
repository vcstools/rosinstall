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
import yaml
import subprocess
import tempfile
import unittest
import shutil

import rosinstall.setupfiles
import rosinstall.helpers
from rosinstall.config import Config
from rosinstall.config_yaml import PathSpec
from rosinstall.common import MultiProjectException
from rosinstall.helpers import ROSInstallException

from test.scm_test_base import AbstractFakeRosBasedTest

def _add_to_file(path, content):
     """Util function to append to file to get a modification"""
     f = io.open(path, 'a')
     f.write(unicode(content))
     f.close()

class GenerateTest(AbstractFakeRosBasedTest):


    def test_gen_setup(self):
        try:
            config = Config([PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                             PathSpec("bar")],
                            self.test_root_path,
                            None)
            rosinstall.setupfiles.generate_setup(config)
            self.fail('expected exception')
        except ROSInstallException:
            pass
        
        config = Config([PathSpec(self.ros_path),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec("bar")],
                        self.test_root_path,
                        None)
        rosinstall.setupfiles.generate_setup(config)
        self.assertTrue(os.path.isfile(os.path.join(self.test_root_path, 'setup.sh')))
        self.assertTrue(os.path.isfile(os.path.join(self.test_root_path, 'setup.bash')))
        self.assertTrue(os.path.isfile(os.path.join(self.test_root_path, 'setup.zsh')))

    def test_gen_setupsh(self):
        config = Config([PathSpec(self.ros_path),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec("bar")],
                        self.test_root_path,
                        None)
        result = rosinstall.setupfiles.generate_setup_sh_text(config, "ros")
        self.assertTrue(result.count("#!/usr/bin/env sh")==1)

        config = Config([PathSpec(self.ros_path),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec("bar.sh", tags = 'setup-file')],
                        self.test_root_path,
                        None)
        result = rosinstall.setupfiles.generate_setup_sh_text(config, "foorosbar")
        self.assertTrue(result.count("#!/usr/bin/env sh")==1)
        self.assertTrue(result.count(". %s/bar.sh"%self.test_root_path)==1)


    def test_gen_setup_bash(self):
        config = Config([PathSpec(self.ros_path),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec("bar")],
                        self.test_root_path,
                        None)
        result = rosinstall.setupfiles.generate_setup_bash_text('bash')
        self.assertTrue(result.count("#!/usr/bin/env bash")==1)
        self.assertTrue(result.count("CATKIN_SHELL=bash")==1)
        result = rosinstall.setupfiles.generate_setup_bash_text('zsh')
        self.assertTrue(result.count("#!/usr/bin/env zsh")==1)
        self.assertTrue(result.count("CATKIN_SHELL=zsh") == 1)
