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
import unittest
import subprocess
import tempfile

import rosinstall
import rosinstall.helpers

import test.scm_test_base
from test.scm_test_base import AbstractSCMTest, _add_to_file, ROSINSTALL_CMD

class RosinstallDiffBzrTest(AbstractSCMTest):

    @classmethod
    def setUpClass(self):
        AbstractSCMTest.setUpClass()
        remote_path = os.path.join(self.test_root_path, "remote")
        os.makedirs(remote_path)
        
        # create a "remote" repo
        subprocess.check_call(["bzr", "init"], cwd=remote_path)
        subprocess.check_call(["touch", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "modified.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "deleted.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "add", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "add", "modified.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "add", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "add", "deleted.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "add", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "commit", "-m", "modified"], cwd=remote_path)

        # rosinstall the remote repo and fake ros
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), u"- other: {local-name: ../ros}\n- bzr: {local-name: clone, uri: ../remote}")

        cmd = [ROSINSTALL_CMD, "ws", "-n"]
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE, env=self.new_environ)
        output=call.communicate()[0]

        clone_path = os.path.join(self.local_path, "clone")
        
        # make local modifications
        subprocess.check_call(["rm", "deleted-fs.txt"], cwd=clone_path)
        subprocess.check_call(["bzr", "rm", "deleted.txt"], cwd=clone_path)
        _add_to_file(os.path.join(clone_path, "modified-fs.txt"), u"foo\n")
        _add_to_file(os.path.join(clone_path, "modified.txt"), u"foo\n")
        _add_to_file(os.path.join(clone_path, "added-fs.txt"), u"tada\n")
        _add_to_file(os.path.join(clone_path, "added.txt"), u"flam\n")
        subprocess.check_call(["bzr", "add", "added.txt"], cwd=clone_path)
        
    def check_diff_output (self, output):
        # uncomment following line for easiest way to get actual output with escapes
        # self.assertEqual(None, output);

        # bzr writes date-time of file into diff
        self.assertTrue(output.startswith("=== added file 'added.txt'\n--- clone/added.txt"), msg=0)
        self.assertTrue(0 < output.find("+++ clone/added.txt"), msg=1)
        self.assertTrue(0 < output.find("@@ -0,0 +1,1 @@\n+flam\n\n"), msg=2)
        self.assertTrue(0 < output.find("=== removed file 'deleted-fs.txt'\n=== removed file 'deleted.txt'\n=== modified file 'modified-fs.txt'\n--- clone/modified-fs.txt"), msg=3 )
        self.assertTrue(0 < output.find("@@ -0,0 +1,1 @@\n+foo\n\n=== modified file 'modified.txt'\n--- clone/modified.txt"), msg=4)

        
    def test_Rosinstall_diff_bzr_outside(self):
        """Test diff output for bzr when run outside workspace"""
        cmd = [ROSINSTALL_CMD, "ws", "--diff"]
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.check_diff_output(output)


    def test_Rosinstall_diff_bzr_inside(self):
        """Test diff output for bzr when run inside workspace"""
        directory = self.test_root_path + "/ws"
        cmd = [ROSINSTALL_CMD, ".", "--diff"]
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.check_diff_output(output)

        
    def test_Rosinstall_status_bzr_inside(self):
        """Test status output for bzr when run inside workspace"""
        directory = self.test_root_path + "/ws"
        cmd = [ROSINSTALL_CMD, ".", "--status"]
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.assertEqual('+N      clone/added.txt\n D      clone/deleted-fs.txt\n-D      clone/deleted.txt\n M      clone/modified-fs.txt\n M      clone/modified.txt\n\n', output)
   
    def test_Rosinstall_status_bzr_outside(self):
        """Test status output for bzr when run outside workspace"""
        cmd = [ROSINSTALL_CMD, "ws", "--status"]
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('+N      clone/added.txt\n D      clone/deleted-fs.txt\n-D      clone/deleted.txt\n M      clone/modified-fs.txt\n M      clone/modified.txt\n\n', output)

    def test_Rosinstall_status_bzr_untracked(self):
        """Test status output for bzr when run outside workspace"""
        cmd = [ROSINSTALL_CMD, "ws", "--status-untracked"]
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('?       clone/added-fs.txt\n+N      clone/added.txt\n D      clone/deleted-fs.txt\n-D      clone/deleted.txt\n M      clone/modified-fs.txt\n M      clone/modified.txt\n\n', output)


        
