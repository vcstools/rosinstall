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
import shutil
import rosinstall
import rosinstall.helpers

import rosinstall.multiproject_cmd

from test.scm_test_base import AbstractFakeRosBasedTest
from rosinstall.rosws_cli import RoswsCLI

class RosWsTest(AbstractFakeRosBasedTest):
      
    def setUp(self):
        """runs rosinstall with generated self.simple_rosinstall to create local rosinstall env
        and creates a directory for a second local rosinstall env"""
        AbstractFakeRosBasedTest.setUp(self)
        
    def test_init(self):
        workspace = os.path.join(self.test_root_path, 'ws1')
        cli = RoswsCLI()
        try:
            cli.cmd_init([workspace, 'foo', 'bar'])
            fail("expected exit")
        except SystemExit: pass
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(os.path.join(workspace, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(workspace, 'setup.sh')))
        self.assertTrue(os.path.isdir(os.path.join(workspace, 'ros')))
        self.assertTrue(os.path.isdir(os.path.join(workspace, 'gitrepo')))
        self.assertTrue(os.path.isdir(os.path.join(workspace, 'gitrepo', '.git')))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename = '.rosinstall')
        self.assertEqual(2, len(config.get_config_elements()))

    def test_init_pwd(self):
        workspace = os.path.join(self.test_root_path, 'ws1b')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace]))
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(os.path.join(workspace, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(workspace, 'setup.sh')))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename = '.rosinstall')
        self.assertEqual(0, len(config.get_config_elements()))

    def test_regenerate(self):
        workspace = os.path.join(self.test_root_path, 'ws1c')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(os.path.join(workspace, '.rosinstall')))
        os.remove(os.path.join(workspace, 'setup.sh'))
        self.assertFalse(os.path.exists(os.path.join(workspace, 'setup.sh')))
        self.assertEqual(0, cli.cmd_regenerate(workspace, []))
        self.assertTrue(os.path.exists(os.path.join(workspace, 'setup.sh')))

        
    def test_merge(self):
        workspace = os.path.join(self.test_root_path, 'ws2')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        self.assertEqual(0, cli.cmd_merge(workspace, [self.simple_changed_vcs_rosinstall, '-y']))
        self.assertFalse(os.path.isdir(os.path.join(workspace, 'hgrepo')))
        self.assertFalse(os.path.isdir(os.path.join(workspace, 'hgrepo', '.hg')))
        self.assertEqual(0, cli.cmd_update(workspace, []))
        self.assertTrue(os.path.isdir(os.path.join(workspace, 'hgrepo')))
        self.assertTrue(os.path.isdir(os.path.join(workspace, 'hgrepo', '.hg')))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename = '.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        
    def test_remove(self):
        workspace = os.path.join(self.test_root_path, 'ws3')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        self.assertEqual(0, cli.cmd_merge(workspace, [self.simple_changed_vcs_rosinstall, '-y']))
        self.assertEqual(0, cli.cmd_update(workspace, []))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename = '.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual(0, cli.cmd_remove(workspace, ['hgrepo']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename = '.rosinstall')
        self.assertEqual(2, len(config.get_config_elements()))

    def test_modify(self):
        workspace = os.path.join(self.test_root_path, 'ws4')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        self.assertEqual(0, cli.cmd_merge(workspace, [self.simple_changed_vcs_rosinstall, '-y']))
        self.assertEqual(0, cli.cmd_update(workspace, []))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename = '.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        self.assertEqual(True, config.get_config_elements()[1].is_vcs_element())
        self.assertEqual('hgrepo', config.get_config_elements()[2].get_local_name())
        self.assertEqual(0, cli.cmd_set(workspace, ['gitrepo', '--detached', '-y']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename = '.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        self.assertEqual(False, config.get_config_elements()[1].is_vcs_element())
        self.assertEqual('hgrepo', config.get_config_elements()[2].get_local_name())
