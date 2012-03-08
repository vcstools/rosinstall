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
import tempfile
import unittest
import subprocess
import rosinstall.rosws_cli
from test.scm_test_base import AbstractFakeRosBasedTest, _create_yaml_file, _create_config_elt_dict
from rosinstall.config_yaml import PathSpec
import rosinstall.rosws_cli
import rosinstall.multiproject_cmd
from rosinstall.rosws_cli import RoswsCLI
from rosinstall.helpers import ROSInstallException

class FakeConfig():
    def __init__(self, elts = [], celts=[], basepath = ''):
        self.elts = elts
        self.celts = celts
        self.basepath = basepath
    def get_config_elements(self):
        return self.celts
    def get_source(self):
        return self.elts
    def get_base_path(self):
        return self.basepath

class MockConfigElement():
    def __init__(self, scmtype=None, path=None, uri = None):
        self.scmtype = scmtype
        self.path = path
        self.uri = uri
    def get_config_elements(self):
        return self.scmtype
    def get_path(self):
        return self.path

class FunctionsTest(unittest.TestCase):

    def test_get_mode(self):
        class FakeOpts:
            def __init__(self, dele, ab, back):
                self.delete_changed = dele
                self.backup_changed = back
                self.abort_changed = ab
        class FakeErrors:
            def __init__(self):
                self.rerror = None
            def error(self, foo):
                self.rerror = foo

        opts = FakeOpts(dele = False, ab = False, back = '')
        ferr = FakeErrors()
        self.assertEqual("prompt", rosinstall.rosws_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele = True, ab = False, back = '')
        ferr = FakeErrors()
        self.assertEqual("delete", rosinstall.rosws_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele = False, ab = True, back = '')
        ferr = FakeErrors()
        self.assertEqual("abort", rosinstall.rosws_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele = False, ab = False, back = 'Foo')
        ferr = FakeErrors()
        self.assertEqual("backup", rosinstall.rosws_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)

        opts = FakeOpts(dele = True, ab = True, back = '')
        ferr = FakeErrors()
        rosinstall.rosws_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)

        opts = FakeOpts(dele = False, ab = True, back = 'Foo')
        ferr = FakeErrors()
        rosinstall.rosws_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)

        opts = FakeOpts(dele = True, ab = False, back = 'Foo')
        ferr = FakeErrors()
        rosinstall.rosws_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)

class RosinstallUsagetest(unittest.TestCase):
    def test_usage(self):
        #test functin exists and does not fail
        rosinstall.rosws_cli.usage()

        
class RosinstallCommandlineTest(AbstractFakeRosBasedTest):

    def test_require_bootstrap(self):
        config = FakeConfig()
        self.assertFalse(rosinstall.rosinstall_cmd._ros_requires_boostrap(config))
        config = FakeConfig([PathSpec(self.ros_path, path = self.ros_path)])
        self.assertFalse(rosinstall.rosinstall_cmd._ros_requires_boostrap(config))
        config = FakeConfig([PathSpec(self.ros_path, 'git', 'gituri', path = self.ros_path)])
        self.assertTrue(rosinstall.rosinstall_cmd._ros_requires_boostrap(config))

        
class RosinstallCommandLineGenerationTest(AbstractFakeRosBasedTest):
    
    def test_cmd_generate_ros_files_simple(self):
        self.local_path = os.path.join(self.test_root_path, "ws")
        os.makedirs(self.local_path)
          
        config = FakeConfig(celts = [MockConfigElement(path = self.ros_path)], basepath = self.local_path)
        rosinstall.rosinstall_cmd.cmd_generate_ros_files(config, self.local_path, nobuild = True, rosdep_yes = False, catkin = False, catkinpp = None)
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))

    def test_cmd_generate_ros_files_vcs(self):
        self.local_path = os.path.join(self.test_root_path, "ws2")
        os.makedirs(self.local_path)
        
        config = FakeConfig(celts = [MockConfigElement(path = self.ros_path), MockConfigElement(path ='gitrepo', scmtype = 'git', uri = self.git_path), MockConfigElement(path = 'hgrepo', scmtype= 'hg', uri = self.hg_path)], basepath = self.local_path)
        rosinstall.rosinstall_cmd.cmd_generate_ros_files(config, self.local_path, nobuild = True, rosdep_yes = False, catkin = False, catkinpp = None)
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))

      
    def test_cmd_generate_ros_files_catkin(self):
        self.local_path = os.path.join(self.test_root_path, "ws3")
        os.makedirs(self.local_path)
        
        config = FakeConfig([PathSpec(self.ros_path), PathSpec('gitrepo', 'git', uri = self.git_path)], self.local_path)
        rosinstall.rosinstall_cmd.cmd_generate_ros_files(config, self.local_path, nobuild = True, rosdep_yes = False, catkin = True, catkinpp = False)
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'CMakeLists.txt')))

    def test_cmd_generate_ros_files_catkinpp(self):
        self.local_path = os.path.join(self.test_root_path, "ws4")
        os.makedirs(self.local_path)
        
        config = FakeConfig([PathSpec(self.ros_path), PathSpec('gitrepo', 'git', uri = self.git_path)], self.local_path)
        rosinstall.rosinstall_cmd.cmd_generate_ros_files(config, self.local_path, nobuild = True, rosdep_yes = False, catkin = True, catkinpp = True)
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'CMakeLists.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'workspace-config.cmake')))

    def test_cmd_generate_ros_files_build(self):
        self.local_path = os.path.join(self.test_root_path, "ws2b")
        os.makedirs(self.local_path)
        local_rosinstall = os.path.join(self.test_root_path, "local.rosinstall")
        _create_yaml_file([_create_config_elt_dict("git", 'ros_comm', self.git_path),
                           _create_config_elt_dict("git", 'ros', self.ros_path),
                           _create_config_elt_dict("hg", 'hgrepo', self.hg_path)],  local_rosinstall)
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([self.local_path, local_rosinstall]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        
    def test_cmd_init(self):
        self.local_path = os.path.join(self.test_root_path, "ws5")
        os.makedirs(self.local_path)
        
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([self.local_path, self.ros_path]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))

        self.assertEqual(0, cli.cmd_install(self.local_path, [self.ros_path, "-y"]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))

    def test_cmd_init_catkin(self):
        self.local_path = os.path.join(self.test_root_path, "ws6")
        os.makedirs(self.local_path)
        
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([self.local_path, self.ros_path, "-c"]))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'CMakeLists.txt')))

        self.assertEqual(0, cli.cmd_install(self.local_path, [self.ros_path, "-cy"]))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'CMakeLists.txt')))

    def test_cmd_init_catkin2(self):
        self.local_path = os.path.join(self.test_root_path, "ws7")
        os.makedirs(self.local_path)
        
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([self.local_path, self.ros_path, "--catkin"]))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'CMakeLists.txt')))
        
        self.assertEqual(0, cli.cmd_install(self.local_path, [self.ros_path, "-y", "--catkin"]))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'CMakeLists.txt')))

    def test_cmd_init_catkinpp(self):
        self.local_path = os.path.join(self.test_root_path, "ws8")
        os.makedirs(self.local_path)
        
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([self.local_path, self.ros_path, "--catkin", "--cmake-prefix-path=foo"]))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'CMakeLists.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'workspace-config.cmake')))

        self.assertEqual(0, cli.cmd_install(self.local_path, [self.ros_path, "-y", "--catkin", "--cmake-prefix-path=foo"]))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertFalse(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'CMakeLists.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'workspace-config.cmake')))

    def test_cmd_init_makedir(self):
        # rosinstall to create dir
        self.local_path = os.path.join(self.test_root_path, "ws9")
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([self.local_path, self.ros_path]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))

    def test_cmd_init_no_ros(self):
        self.local_path = os.path.join(self.test_root_path, "ws10")


        ros_root_existed = False
        if 'ROS_ROOT' in os.environ:
            ros_root_existed = True
            oldros = os.environ.pop('ROS_ROOT')
        cli = RoswsCLI()
        try:
            self.assertEqual(0, cli.cmd_init([self.local_path]))
            self.fail("expected Exception")
        except ROSInstallException:
            pass
        os.environ['ROS_ROOT'] = self.ros_path
        self.assertEqual(0, cli.cmd_init([self.local_path]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        if ros_root_existed:
            os.environ['ROS_ROOT'] = oldros
        else:
            os.environ.pop('ROS_ROOT')

    def test_cmd_init_main(self):
        # rosinstall to create dir
        ros_root_existed = False

        if 'ROS_ROOT' in os.environ:
            ros_root_existed = True
            oldros = os.environ.pop('ROS_ROOT')
        os.environ['ROS_ROOT'] = self.ros_path
        self.local_path = os.path.join(self.test_root_path, "ws11")
        self.assertEqual(0, rosinstall.rosws_cli.rosws_main(['rosws', 'help']))
        self.assertEqual(0, rosinstall.rosws_cli.rosws_main(['rosws', 'init', self.local_path]))
        self.assertEqual(0, rosinstall.rosws_cli.rosws_main(['rosws', 'info', '-t', self.local_path]))
        self.assertEqual(0, rosinstall.rosws_cli.rosws_main(['rosws', 'info', '--pkg-path-only', '-t', self.local_path]))
        self.assertEqual(0, rosinstall.rosws_cli.rosws_main(['rosws', 'info', '--no-pkg-path', '-t', self.local_path]))
        self.assertEqual(0, rosinstall.rosws_cli.rosws_main(['rosws', 'info', '--data-only', '-t', self.local_path]))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.sh')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.bash')))
        self.assertTrue(os.path.exists(os.path.join(self.local_path, 'setup.zsh')))
        if ros_root_existed:
            os.environ['ROS_ROOT'] = oldros
        else:
            os.environ.pop('ROS_ROOT')


    def test_cmd_remove(self):
        # rosinstall to create dir
        self.local_path = os.path.join(self.test_root_path, "ws12")
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([self.local_path, self.ros_path]))
        self.assertEqual(0, cli.cmd_install(self.local_path, [self.git_path, self.hg_path, "-y"]))
        config = rosinstall.multiproject_cmd.get_config(basepath = self.local_path,                                                       config_filename = '.rosinstall')
        self.assertEqual(len(config.get_config_elements()), 3)
        self.assertEqual(0, cli.cmd_remove(self.local_path, [self.git_path]))
        config = rosinstall.multiproject_cmd.get_config(basepath = self.local_path,                                                       config_filename = '.rosinstall')
        self.assertEqual(len(config.get_config_elements()), 2)

    def test_setup_sh(self):
        self.local_path = os.path.join(self.test_root_path, "ws13")
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([self.local_path, self.ros_path]))
        
        command = ". %s ; echo $ROS_WORKSPACE" %os.path.join(self.local_path, 'setup.sh')
        output = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]
        self.assertEqual(self.local_path, output.strip())
        
        command = ". %s ; echo $ROS_WORKSPACE" %'./setup.sh'
        output = subprocess.Popen(command, shell=True, cwd=self.local_path, stdout=subprocess.PIPE).communicate()[0]
        self.assertEqual(self.local_path, output.strip())

        command = ". %s ; echo $ROS_WORKSPACE" %'ws13/setup.sh'
        output = subprocess.Popen(command, shell=True, cwd=self.test_root_path, stdout=subprocess.PIPE).communicate()[0]
        self.assertEqual(self.local_path, output.strip())
