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
import subprocess
import tempfile
import urllib
import shutil

import rosinstall
import rosinstall.helpers

class RosinstallCommandlineTest(unittest.TestCase):

    def setUp(self):
        #self.rosinstall_tempfile = tempfile.NamedTemporaryFile(mode='a+b')
        self.rosinstall_fn = ["./scripts/rosinstall", "-n"]
        self.new_environ = os.environ
        self.new_environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
        #urllib.urlretrieve("https://code.ros.org/svn/ros/installers/trunk/rosinstall/rosinstall2", self.rosinstall_fn)
        #os.chmod(self.rosinstall_fn, stat.S_IRWXU)
        self.directories = {}


    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        #os.remove(self.rosinstall_fn)

    def test_Rosinstall_executable(self):
        cmd = self.rosinstall_fn
        print cmd.append("-h")
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

    def test_Rosinstall_ros(self):
        directory = tempfile.mkdtemp()
        self.directories["ros"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "ros_w_release.rosinstall")])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))
        shutil.rmtree(directory)
        self.directories.pop("ros")

    def DISABLED_Rosinstall_ros_stack(self):
        directory = tempfile.mkdtemp()
        self.directories["stack"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "distro_stack.rosinstall")])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))
        shutil.rmtree(directory)
        self.directories.pop("stack")

    def DISABLED_Rosinstall_ros_variant(self):
        directory = tempfile.mkdtemp()
        self.directories["variant"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "distro_variant.rosinstall")])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))
        shutil.rmtree(directory)
        self.directories.pop("variant")


class RosinstallCommandlineOverlays(unittest.TestCase):

    def setUp(self):
        self.rosinstall_tempfile = tempfile.NamedTemporaryFile(mode='a+b')
        self.rosinstall_fn = ["./scripts/rosinstall", "-n"]
        self.new_environ = os.environ
        self.new_environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

        #self.rosinstall_fn = "/tmp/test_rosinstall_temp_version"
        #urllib.urlretrieve("https://code.ros.org/svn/ros/installers/trunk/rosinstall/rosinstall", self.rosinstall_fn)
        #os.chmod(self.rosinstall_fn, stat.S_IRWXU)
        self.directories = {}
        self.base = tempfile.mkdtemp()
        cmd = self.rosinstall_fn[:]
        #cmd.extend([self.base, "http://www.ros.org/rosinstalls/boxturtle_base.rosinstall"])
        cmd.extend([self.base, os.path.join("test", "rosinstalls", "ros_w_release.rosinstall")])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))


    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        shutil.rmtree(self.base)
        #os.remove(self.rosinstall_fn)

    def test_Rosinstall_rosinstall_file_generation(self):
        generated_rosinstall_filename = os.path.join(self.base, ".rosinstall")
        self.assertTrue(os.path.exists(generated_rosinstall_filename))
        source_yaml = rosinstall.helpers.get_yaml_from_uri(generated_rosinstall_filename)
        self.assertEqual(source_yaml, 
                         [{'svn': { 'uri': 'https://code.ros.org/svn/ros/stacks/ros/tags/boxturtle',
                                    'local-name': 'ros'} },
                          {'svn': { 'uri': 'https://code.ros.org/svn/ros/stacks/ros_release/trunk',
                                    'local-name': 'ros_release'} }
                          ])

        
            

    def test_Rosinstall_common_msgs_as_explicit_overlay(self):
        directory = tempfile.mkdtemp()
        with tempfile.NamedTemporaryFile() as ri_file:
            file_text = """
- other:
    local-name: %s/ros_release
- other:
    local-name: %s/ros
- svn:
    uri: https://code.ros.org/svn/ros-pkg/stacks/common_msgs/tags/boxturtle
    local-name: stacks/common_msgs
"""%(self.base, self.base)
            print file_text
            ri_file.write(file_text)
            ri_file.flush()
                          
            self.directories["tutorials"] = directory
            cmd = self.rosinstall_fn[:]
            cmd.extend([directory, ri_file.name])
            print "EXECUTING", cmd
            self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        shutil.rmtree(directory)
        self.directories.pop("tutorials")

    def test_Rosinstall_ros_tutorial_as_argument(self):
        directory = tempfile.mkdtemp()
        self.directories["tutorials2"] = directory
        cmd = self.rosinstall_fn[:]
        cmd.extend([directory, self.base, os.path.join("test", "rosinstalls", "overlay.rosinstall")])
        print "Running command %s"%cmd
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))


        shutil.rmtree(directory)
        self.directories.pop("tutorials2")

class RosinstallOptionsTest(unittest.TestCase):

    def setUp(self):
        #self.rosinstall_tempfile = tempfile.NamedTemporaryFile(mode='a+b')
        self.rosinstall_fn = ["scripts/rosinstall"]
        self.new_environ = os.environ
        self.new_environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

        #urllib.urlretrieve("https://code.ros.org/svn/ros/installers/trunk/rosinstall/rosinstall2", self.rosinstall_fn)
        #os.chmod(self.rosinstall_fn, stat.S_IRWXU)
        self.directories = {}


    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        #os.remove(self.rosinstall_fn)


    def test_rosinstall_delete_changes(self):
        directory = tempfile.mkdtemp()
        self.directories["delete"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "simple.rosinstall"), "-n"])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        cmd.extend([directory, os.path.join("test", "rosinstalls", "simple_changed_uri.rosinstall"), "--delete-changed-uri", "-n"])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        shutil.rmtree(directory)
        self.directories.pop("delete")

    def test_rosinstall_abort_changes(self):
        directory = tempfile.mkdtemp()
        self.directories["abort"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "simple.rosinstall"), "-n"])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        cmd.extend([directory, os.path.join("test", "rosinstalls", "simple_changed_uri.rosinstall"), "--abort-changed-uri", "-n"])
        self.assertEqual(1,subprocess.call(cmd, env=self.new_environ))

        shutil.rmtree(directory)
        self.directories.pop("abort")

    def test_rosinstall_backup_changes(self):
        directory = tempfile.mkdtemp()
        self.directories["backup"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "simple.rosinstall"), "-n"])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        directory1 = tempfile.mkdtemp()
        self.directories["backup1"] = directory1
        cmd.extend([directory, os.path.join("test", "rosinstalls", "simple_changed_uri.rosinstall"), "--backup-changed-uri=%s"%directory1, "-n"])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        self.assertEqual(len(os.listdir(directory1)), 1)

        shutil.rmtree(directory)
        self.directories.pop("backup")
        shutil.rmtree(directory1)
        self.directories.pop("backup1")


    def test_rosinstall_invalid_fail(self):
        directory = tempfile.mkdtemp()
        self.directories["invalid_fail"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "broken.rosinstall"), "-n"])
        self.assertEqual(1,subprocess.call(cmd, env=self.new_environ))

        shutil.rmtree(directory)
        self.directories.pop("invalid_fail")

    def test_rosinstall_invalid_continue(self):
        directory = tempfile.mkdtemp()
        self.directories["invalid_continue"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "broken.rosinstall"), "-n", "--continue-on-error"])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        shutil.rmtree(directory)
        self.directories.pop("invalid_continue")

    def test_rosinstall_change_vcs_type(self):
        directory = tempfile.mkdtemp()
        self.directories["change_vcs_type"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join("test", "rosinstalls", "simple.rosinstall"), "-n"])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        cmd.extend([directory, os.path.join("test", "rosinstalls", "simple_changed_vcs_type.rosinstall"), "--delete-changed-uri", "-n"])
        self.assertEqual(0,subprocess.call(cmd, env=self.new_environ))

        shutil.rmtree(directory)
        self.directories.pop("change_vcs_type")


