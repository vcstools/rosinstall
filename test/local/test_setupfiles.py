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
from rosinstall.config_yaml import PathSpec, generate_config_yaml
from rosinstall.common import MultiProjectException
from rosinstall.helpers import ROSInstallException, ROSINSTALL_FILENAME

from test.scm_test_base import AbstractFakeRosBasedTest, AbstractRosinstallBaseDirTest, _add_to_file


def has_python3():
    cmd = "python3 --version"
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    p.stdout.close()
    if not p.returncode == 0:
        return True
    return False


HAS_PYTHON3 = has_python3()


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
        # check that sourcing setup.sh raises error when .rosinstall is missing
        raised = False
        try:
            subprocess.check_call(". %s" % testsetupfile , shell=True, env=self.new_environ)
        except:
            raised = True
        self.assertTrue(raised, 'sourcing setup.sh with missing .rosinstall should fail')
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
        rosinstall.config_yaml.generate_config_yaml(config, '.rosinstall', '')
        filename = os.path.join(self.directory, "test_gen.py")
        _add_to_file(filename, rosinstall.setupfiles.generate_embedded_python())
        sh_filename = os.path.join(self.directory, "bar.sh")
        _add_to_file(sh_filename, "#! /usr/bin/env sh")
        cmd = "python %s" % filename
        p = subprocess.Popen(cmd, shell=True, cwd=self.directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        self.assertEqual(''.encode('UTF-8'), err, err)
        self.assertTrue('/test/example_dirs/ros_comm'.encode('UTF-8') in output, output)
        self.assertTrue('baz'.encode('UTF-8') in output, output)
        self.assertTrue('ROSINSTALL_PATH_SETUPFILE_SEPARATOR'.encode('UTF-8') in output, output)
        self.assertTrue(output.endswith('/bar.sh\n'.encode('UTF-8')), output)

    if not HAS_PYTHON3:

        def test_gen_python_code_python3(self):
            # requires python3 to be installed, obviously
            config = Config([PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                             PathSpec("bar.sh", tags=['setup-file']),
                             PathSpec("baz")],
                            self.directory,
                            None)
            rosinstall.config_yaml.generate_config_yaml(config, '.rosinstall', '')
            filename = os.path.join(self.directory, "test_gen.py")
            _add_to_file(filename, rosinstall.setupfiles.generate_embedded_python())
            sh_filename = os.path.join(self.directory, "bar.sh")
            _add_to_file(sh_filename, "#! /usr/bin/env sh")
            cmd = "python3 %s" % filename
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
