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

import rosinstall.setupfiles
import wstool.helpers
from wstool.config import Config
from wstool.config_yaml import PathSpec, generate_config_yaml
from rosinstall.helpers import ROSInstallException
from wstool.helpers import ROSINSTALL_FILENAME
from wstool.multiproject_cmd import cmd_persist_config
from rosinstall.rosinstall_cmd import cmd_generate_ros_files

from test.scm_test_base import AbstractFakeRosBasedTest
from test.scm_test_base import AbstractRosinstallBaseDirTest


def has_python3():
    cmd = "python3 --version"
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    p.stdout.close()
    if p.returncode == 0:
        return True
    return False


HAS_PYTHON3 = has_python3()
if 'ROSINSTALL_SKIP_PYTHON3' in os.environ:
    HAS_PYTHON3 = False


def _add_to_file(path, content):
    """Util function to append to file to get a modification"""
    with open(path, 'ab') as f:
        f.write(content.encode('UTF-8'))


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
        result = rosinstall.setupfiles.generate_setup_sh_text(config.get_base_path())
        self.assertTrue(result.count("#!/usr/bin/env sh") == 1)

        config = Config([PathSpec(self.ros_path),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec("bar.sh", tags=['setup-file'])],
                        self.test_root_path,
                        None)
        result = rosinstall.setupfiles.generate_setup_sh_text(config.get_base_path())
        self.assertTrue(result.count("#!/usr/bin/env sh") == 1, result)

    def test_source_setup_sh(self):
        test_folder = os.path.join(self.test_root_path, 'workspacetest')
        os.makedirs(test_folder)
        othersetupfile = os.path.join(test_folder, 'othersetup.sh')
        testsetupfile = os.path.join(test_folder, 'testsetup.sh')
        with open(othersetupfile, 'w') as fhand:
            fhand.write('unset ROS_WORKSPACE')
        config = Config([PathSpec(self.ros_path),
                         PathSpec(othersetupfile,
                                  scmtype=None,
                                  tags=['setup-file'])],
                        install_path=test_folder,
                        config_filename=ROSINSTALL_FILENAME)
        result = rosinstall.setupfiles.generate_setup_sh_text(config.get_base_path())
        self.assertTrue('export ROS_WORKSPACE=%s' % test_folder in result)
        with open(testsetupfile, 'w') as fhand:
            fhand.write(result)
        # check that sourcing setup.sh raises error when .wstool is missing
        raised = False
        try:
            subprocess.check_call(". %s" % testsetupfile , shell=True, env=self.new_environ)
        except:
            raised = True
        self.assertTrue(raised, 'sourcing setup.sh with missing .wstool should fail')
        # test that our otherscript really unsets ROS_WORKSPACE, else nexttest would be invalid
        # using basename to check var is not set
        raised = False
        try:
            cmd = "export ROS_WORKSPACE=foo && . %s && basename $ROS_WORKSPACE" % othersetupfile
            subprocess.check_call(
                cmd,
                shell=True,
                env=self.new_environ)
        except:
            raised = True
        self.assertTrue(raised, 'unsetting-sh-file did not unset var')
        # now test that when sourcing setup.sh that contains a
        # setup-file to other sh file which unsets ROS_WORKSPACE,
        # ROS_WORKSPACE is still set in the end
        generate_config_yaml(config, ROSINSTALL_FILENAME, '')
        self.assertTrue(os.path.isfile(os.path.join(test_folder, ROSINSTALL_FILENAME)))
        # using basename to check var is set
        cmd = "export ROS_WORKSPACE=foo && . %s && echo $ROS_WORKSPACE" % testsetupfile
        po = subprocess.Popen(cmd, shell=True, cwd=test_folder, stdout=subprocess.PIPE)
        workspace = po.stdout.read().decode('UTF-8').rstrip('"').lstrip('"').strip()
        po.stdout.close()
        self.assertEqual(test_folder, workspace)

    def test_source_setup_sh_chain(self):
        """
        Tests chaining of workspaces, which is fragile because
        sourcing very similar setup.sh files recursively
        """
        chain_root_path = os.path.join(self.test_root_path, 'chaintest')
        os.makedirs(chain_root_path)
        test_folder1 = os.path.join(chain_root_path, 'ws1')
        os.makedirs(test_folder1)
        test_folder2 = os.path.join(chain_root_path, 'ws2')
        os.makedirs(test_folder2)
        test_folder3 = os.path.join(chain_root_path, 'ws3')
        os.makedirs(test_folder3)
        test_folder4 = os.path.join(chain_root_path, 'ws4')
        os.makedirs(test_folder4)
        othersetupfile = os.path.join(chain_root_path, 'othersetup.sh')
        with open(othersetupfile, 'w') as fhand:
            fhand.write('export ROS_PACKAGE_PATH=/opt/ros/distro')
        config1 = Config([PathSpec('ws1sub'),
                          PathSpec(os.path.join(test_folder2, "setup.sh"),
                                   scmtype=None,
                                   tags=['setup-file']),
                          PathSpec(os.path.join(test_folder4, "setup.sh"),
                                   scmtype=None,
                                   tags=['setup-file'])],
                         install_path=test_folder1,
                         config_filename=ROSINSTALL_FILENAME)
        config2 = Config([PathSpec('ws2sub'),
                          PathSpec(os.path.join(test_folder3, "setup.sh"),
                                   scmtype=None,
                                   tags=['setup-file'])],
                         install_path=test_folder2,
                         config_filename=ROSINSTALL_FILENAME)
        config3 = Config([PathSpec('ws3sub'),
                          PathSpec(othersetupfile,
                                   scmtype=None,
                                   tags=['setup-file'])],
                         install_path=test_folder3,
                         config_filename=ROSINSTALL_FILENAME)
        config4 = Config([PathSpec('ws4sub')],
                         install_path=test_folder4,
                         config_filename=ROSINSTALL_FILENAME)
        cmd_generate_ros_files(config1, test_folder1, no_ros_allowed=True)
        cmd_persist_config(config1,
                           os.path.join(test_folder1, ROSINSTALL_FILENAME))

        cmd_generate_ros_files(config2, test_folder2, no_ros_allowed=True)
        cmd_persist_config(config2,
                           os.path.join(test_folder2, ROSINSTALL_FILENAME))
        cmd_generate_ros_files(config3, test_folder3, no_ros_allowed=True)
        cmd_persist_config(config3,
                           os.path.join(test_folder3, ROSINSTALL_FILENAME))
        cmd_generate_ros_files(config4, test_folder4, no_ros_allowed=True)
        cmd_persist_config(config4,
                           os.path.join(test_folder4, ROSINSTALL_FILENAME))
        cmd = ". %s && echo $ROS_PACKAGE_PATH" % os.path.join(test_folder1, "setup.sh")
        po = subprocess.Popen(cmd, shell=True, cwd=test_folder1, stdout=subprocess.PIPE)
        ppath = po.stdout.read().decode('UTF-8').strip('"').strip()
        po.stdout.close()
        expected = ':'.join([os.path.join(test_folder1, "ws1sub"),
                             os.path.join(test_folder2, "ws2sub"),
                             os.path.join(test_folder3, "ws3sub"),
                             os.path.join(test_folder4, "ws4sub"),
                             '/opt/ros/distro'])
        self.assertEqual(expected, ppath)
        # test double sourcing
        cmd = ". %s ; . %s && echo $ROS_PACKAGE_PATH" % (os.path.join(test_folder2, "setup.sh"),
                                                         os.path.join(test_folder4, "setup.sh"))
        po = subprocess.Popen(cmd, shell=True, cwd=test_folder1, stdout=subprocess.PIPE)
        ppath = po.stdout.read().decode('UTF-8').strip('"').strip()
        po.stdout.close()
        expected = os.path.join(test_folder4, "ws4sub")
        self.assertEqual(expected, ppath)

    def test_gen_setup_bash(self):
        config = Config([PathSpec(self.ros_path),
                         PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                         PathSpec("bar")],
                        self.test_root_path,
                        None)
        result = rosinstall.setupfiles.generate_setup_bash_text('bash')
        self.assertTrue(result.count("#!/usr/bin/env bash") == 1)
        self.assertTrue(result.count("CATKIN_SHELL=bash") == 1)
        self.assertTrue(result.count("ROSSHELL_PATH=`rospack find rosbash`/rosbash") == 1)
        result = rosinstall.setupfiles.generate_setup_bash_text('zsh')
        self.assertTrue(result.count("#!/usr/bin/env zsh") == 1)
        self.assertTrue(result.count("CATKIN_SHELL=zsh") == 1)
        self.assertTrue(result.count("ROSSHELL_PATH=`rospack find rosbash`/roszsh") == 1)


class Genfiletest(AbstractRosinstallBaseDirTest):

    def test_gen_python_code(self):
        config = Config(
            [PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
             PathSpec("bar.sh", tags=['setup-file']),
             PathSpec("baz")],
            self.directory,
            None)
        wstool.config_yaml.generate_config_yaml(config, '.rosinstall', '')
        filename = os.path.join(self.directory, "test_gen.py")
        _add_to_file(filename, rosinstall.setupfiles.generate_embedded_python())
        sh_filename = os.path.join(self.directory, "bar.sh")
        _add_to_file(sh_filename, "#! /usr/bin/env sh")
        cmd = "python -W ignore %s" % filename
        p = subprocess.Popen(cmd, shell=True, cwd=self.directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        self.assertEqual(''.encode('UTF-8'), err, err)
        self.assertTrue('/test/example_dirs/ros_comm'.encode('UTF-8') in output, output)
        self.assertTrue('baz'.encode('UTF-8') in output, output)
        self.assertTrue('ROSINSTALL_PATH_SETUPFILE_SEPARATOR'.encode('UTF-8') in output, output)
        self.assertTrue(output.endswith('/bar.sh\n'.encode('UTF-8')), output)

    if HAS_PYTHON3:

        def test_gen_python_code_python3(self):
            # requires python3 to be installed, obviously
            config = Config([PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                             PathSpec("bar.sh", tags=['setup-file']),
                             PathSpec("baz")],
                            self.directory,
                            None)
            wstool.config_yaml.generate_config_yaml(config, '.rosinstall', '')
            filename = os.path.join(self.directory, "test_gen.py")
            _add_to_file(filename, rosinstall.setupfiles.generate_embedded_python())
            sh_filename = os.path.join(self.directory, "bar.sh")
            _add_to_file(sh_filename, "#! /usr/bin/env sh")
            cmd = "python3 -W ignore %s" % filename
            p = subprocess.Popen(cmd, shell=True, cwd=self.directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = p.communicate()
            self.assertEqual(''.encode('UTF-8'), err, err)
            self.assertTrue('/test/example_dirs/ros_comm'.encode('UTF-8') in output, output)
            self.assertTrue('baz'.encode('UTF-8') in output, output)
            self.assertTrue('ROSINSTALL_PATH_SETUPFILE_SEPARATOR'.encode('UTF-8') in output, output)
            self.assertTrue(output.endswith('/bar.sh\n'.encode('UTF-8')), output)


def main():
    import unittest
    unittest.main()
