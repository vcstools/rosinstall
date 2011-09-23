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
     f = io.open(path, 'a')
     f.write(content)
     f.close()

ROSINSTALL_FN = [os.path.join(os.getcwd(), 'scripts/rosinstall')]


class AbstractSCMTest(unittest.TestCase):
    def setUp(self, scm):


        self.test_root_path = tempfile.mkdtemp()
        self.directories = {"root":self.test_root_path}

        self.new_environ = os.environ
        self.new_environ["PYTHONPATH"] = os.path.join(os.getcwd(), "src")

        
        # setup fake ros root
        self.ros_path = os.path.join(self.test_root_path, "ros")
        os.makedirs(self.ros_path)
        _add_to_file(os.path.join(self.ros_path, "stack.xml"), u'<stack></stack>')
        _add_to_file(os.path.join(self.ros_path, "setup.sh"), u'export ROS_ROOT=`pwd`')
        self.local_path = os.path.join(self.test_root_path, "ws")
        os.makedirs(self.local_path)

    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])        
        
class RosinstallDiffGitTest(AbstractSCMTest):

    def setUp(self):
        AbstractSCMTest.setUp(self, "git")
        remote_path = os.path.join(self.test_root_path, "remote")
        os.makedirs(remote_path)
        
        # create a "remote" repo
        subprocess.check_call(["git", "init"], cwd=remote_path)
        subprocess.check_call(["touch", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "modified.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "deleted.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["git", "add", "*"], cwd=remote_path)
        subprocess.check_call(["git", "commit", "-m", "modified"], cwd=remote_path)

        # rosinstall the remote repo and fake ros
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), u"- other: {local-name: ../ros}\n- git: {local-name: clone, uri: remote}")

        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "-n"])
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        clone_path = os.path.join(self.local_path, "clone")
        
        # make local modifications
        subprocess.check_call(["rm", "deleted-fs.txt"], cwd=clone_path)
        subprocess.check_call(["git", "rm", "deleted.txt"], cwd=clone_path)
        _add_to_file(os.path.join(clone_path, "modified-fs.txt"), u"foo\n")
        _add_to_file(os.path.join(clone_path, "modified.txt"), u"foo\n")
        subprocess.check_call(["git", "add", "modified.txt"], cwd=clone_path)
        _add_to_file(os.path.join(clone_path, "added-fs.txt"), u"tada\n")
        _add_to_file(os.path.join(clone_path, "added.txt"), u"flam\n")
        subprocess.check_call(["git", "add", "added.txt"], cwd=clone_path)
                
    def check_diff_output(self, output):
        # sha ids are always same with git
        self.assertEqual('diff --git clone/added.txt clone/added.txt\nnew file mode 100644\nindex 0000000..8d63207\n--- /dev/null\n+++ clone/added.txt\n@@ -0,0 +1 @@\n+flam\ndiff --git clone/deleted-fs.txt clone/deleted-fs.txt\ndeleted file mode 100644\nindex e69de29..0000000\ndiff --git clone/deleted.txt clone/deleted.txt\ndeleted file mode 100644\nindex e69de29..0000000\ndiff --git clone/modified-fs.txt clone/modified-fs.txt\nindex e69de29..257cc56 100644\n--- clone/modified-fs.txt\n+++ clone/modified-fs.txt\n@@ -0,0 +1 @@\n+foo\ndiff --git clone/modified.txt clone/modified.txt\nindex e69de29..257cc56 100644\n--- clone/modified.txt\n+++ clone/modified.txt\n@@ -0,0 +1 @@\n+foo\n\n', output)
        
    def test_Rosinstall_diff_git_outside(self):
        """Test diff output for git when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--diff"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.check_diff_output(output)
        

    def test_Rosinstall_diff_git_inside(self):
        """Test diff output for git when run inside workspace"""
        # dir created by make
        directory = self.test_root_path + "/ws"
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend([".", "--diff"])
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.check_diff_output(output)
        
    def test_Rosinstall_status_git_inside(self):
        """Test status output for git when run inside workspace"""
        # dir created by make
        directory = self.test_root_path + "/ws"
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend([".", "--status"])
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.assertEqual('A       clone/added.txt\n D      clone/deleted-fs.txt\nD       clone/deleted.txt\n M      clone/modified-fs.txt\nM       clone/modified.txt\n\n', output)
   
    def test_Rosinstall_status_git_outside(self):
        """Test status output for git when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--status"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.assertEqual('A       clone/added.txt\n D      clone/deleted-fs.txt\nD       clone/deleted.txt\n M      clone/modified-fs.txt\nM       clone/modified.txt\n\n', output)

    def test_Rosinstall_status_git_untracked(self):
        """Test untracked status output for git when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--status-untracked"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('A       clone/added.txt\n D      clone/deleted-fs.txt\nD       clone/deleted.txt\n M      clone/modified-fs.txt\nM       clone/modified.txt\n??      clone/added-fs.txt\n\n', output)


class RosinstallDiffHgTest(AbstractSCMTest):

    def setUp(self):
        AbstractSCMTest.setUp(self, "hg")
        remote_path = os.path.join(self.test_root_path, "remote")
        os.makedirs(remote_path)
        
        # create a "remote" repo
        subprocess.check_call(["hg", "init"], cwd=remote_path)
        subprocess.check_call(["touch", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "modified.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "deleted.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "modified.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "deleted.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "add", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["hg", "commit", "-m", "modified"], cwd=remote_path)

        # rosinstall the remote repo and fake ros
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), u"- other: {local-name: ../ros}\n- hg: {local-name: clone, uri: remote}")

        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "-n"])
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        clone_path = os.path.join(self.local_path, "clone")
        
        # make local modifications
        subprocess.check_call(["rm", "deleted-fs.txt"], cwd=clone_path)
        subprocess.check_call(["hg", "rm", "deleted.txt"], cwd=clone_path)
        _add_to_file(os.path.join(clone_path, "modified-fs.txt"), u"foo\n")
        _add_to_file(os.path.join(clone_path, "modified.txt"), u"foo\n")
        _add_to_file(os.path.join(clone_path, "added-fs.txt"), u"tada\n")
        _add_to_file(os.path.join(clone_path, "added.txt"), u"flam\n")
        subprocess.check_call(["hg", "add", "added.txt"], cwd=clone_path)
        
    def check_diff_output(self, output):
        # sha ids are always same with hg
        self.assertEqual('diff --git clone/added.txt clone/added.txt\nnew file mode 100644\n--- /dev/null\n+++ clone/added.txt\n@@ -0,0 +1,1 @@\n+flam\ndiff --git clone/deleted.txt clone/deleted.txt\ndeleted file mode 100644\ndiff --git clone/modified-fs.txt clone/modified-fs.txt\n--- clone/modified-fs.txt\n+++ clone/modified-fs.txt\n@@ -0,0 +1,1 @@\n+foo\ndiff --git clone/modified.txt clone/modified.txt\n--- clone/modified.txt\n+++ clone/modified.txt\n@@ -0,0 +1,1 @@\n+foo\n\n\n', output)
        
    def test_Rosinstall_diff_hg_outside(self):
        """Test diff output for hg when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--diff"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.check_diff_output(output)

    def test_Rosinstall_diff_hg_inside(self):
        """Test diff output for hg when run inside workspace"""
        # dir created by make
        directory = self.test_root_path + "/ws"
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend([".", "--diff"])
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.check_diff_output(output)
        
        
    def test_Rosinstall_status_hg_inside(self):
        """Test status output for hg when run inside workspace"""
        # dir created by make
        directory = self.test_root_path + "/ws"
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend([".", "--status"])
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.assertEqual('M       clone/modified-fs.txt\nM       clone/modified.txt\nA       clone/added.txt\nR       clone/deleted.txt\n!       clone/deleted-fs.txt\n\n', output)
   
    def test_Rosinstall_status_hg_outside(self):
        """Test status output for hg when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--status"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('M       clone/modified-fs.txt\nM       clone/modified.txt\nA       clone/added.txt\nR       clone/deleted.txt\n!       clone/deleted-fs.txt\n\n', output)

    def test_Rosinstall_status_hg_untracked(self):
        """Test untracked status output for hg when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--status-untracked"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('M       clone/modified-fs.txt\nM       clone/modified.txt\nA       clone/added.txt\nR       clone/deleted.txt\n!       clone/deleted-fs.txt\n?       clone/added-fs.txt\n\n', output)

class RosinstallDiffBzrTest(AbstractSCMTest):

    def setUp(self):
        AbstractSCMTest.setUp(self, "bzr")
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
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), u"- other: {local-name: ../ros}\n- bzr: {local-name: clone, uri: remote}")

        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "-n"])
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
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--diff"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.check_diff_output(output)


    def test_Rosinstall_diff_bzr_inside(self):
        """Test diff output for bzr when run inside workspace"""
        # dir created by make
        directory = self.test_root_path + "/ws"
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend([".", "--diff"])
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.check_diff_output(output)

        
    def test_Rosinstall_status_bzr_inside(self):
        """Test status output for bzr when run inside workspace"""
        # dir created by make
        directory = self.test_root_path + "/ws"
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend([".", "--status"])
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.assertEqual('+N      clone/added.txt\n D      clone/deleted-fs.txt\n-D      clone/deleted.txt\n M      clone/modified-fs.txt\n M      clone/modified.txt\n\n', output)
   
    def test_Rosinstall_status_bzr_outside(self):
        """Test status output for bzr when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--status"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('+N      clone/added.txt\n D      clone/deleted-fs.txt\n-D      clone/deleted.txt\n M      clone/modified-fs.txt\n M      clone/modified.txt\n\n', output)

    def test_Rosinstall_status_bzr_untracked(self):
        """Test status output for bzr when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--status-untracked"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('?       clone/added-fs.txt\n+N      clone/added.txt\n D      clone/deleted-fs.txt\n-D      clone/deleted.txt\n M      clone/modified-fs.txt\n M      clone/modified.txt\n\n', output)


        
class RosinstallDiffSvnTest(AbstractSCMTest):

    def setUp(self):
        AbstractSCMTest.setUp(self, "svn")
        remote_path = os.path.join(self.test_root_path, "remote")
        filler_path = os.path.join(self.test_root_path, "filler")
        svn_uri = "file://localhost"+remote_path
        
        # create a "remote" repo
        subprocess.check_call(["svnadmin", "create", remote_path], cwd=self.test_root_path)
        subprocess.check_call(["svn", "checkout", svn_uri, filler_path], cwd=self.test_root_path)   
        subprocess.check_call(["touch", "fixed.txt"], cwd=filler_path)
        subprocess.check_call(["touch", "modified.txt"], cwd=filler_path)
        subprocess.check_call(["touch", "modified-fs.txt"], cwd=filler_path)
        subprocess.check_call(["touch", "deleted.txt"], cwd=filler_path)
        subprocess.check_call(["touch", "deleted-fs.txt"], cwd=filler_path)
        subprocess.check_call(["svn", "add", "fixed.txt"], cwd=filler_path)
        subprocess.check_call(["svn", "add", "modified.txt"], cwd=filler_path)
        subprocess.check_call(["svn", "add", "modified-fs.txt"], cwd=filler_path)
        subprocess.check_call(["svn", "add", "deleted.txt"], cwd=filler_path)
        subprocess.check_call(["svn", "add", "deleted-fs.txt"], cwd=filler_path)
        subprocess.check_call(["svn", "commit", "-m", "modified"], cwd=filler_path)

        # rosinstall the remote repo and fake ros
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), u"- other: {local-name: ../ros}\n- svn: {local-name: clone, uri: '"+svn_uri+"'}")

        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "-n"])
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE, env=self.new_environ)
        output=call.communicate()[0]
        clone_path = os.path.join(self.local_path, "clone")


        # make local modifications
        subprocess.check_call(["rm", "deleted-fs.txt"], cwd=clone_path)
        subprocess.check_call(["svn", "rm", "deleted.txt"], cwd=clone_path)
        
        #_add_to_file(os.path.join(clone_path, "modified-fs.txt"), u"foo\n")
        _add_to_file(os.path.join(clone_path, "modified.txt"), u"foo\n")
        _add_to_file(os.path.join(clone_path, "added-fs.txt"), u"tada\n")
        _add_to_file(os.path.join(clone_path, "added.txt"), u"flam\n")
        subprocess.check_call(["svn", "add", "added.txt"], cwd=clone_path)
        
     
    def check_diff_output(self, output):
        #self.assertEqual('Index: clone/added.txt\n===================================================================\n--- clone/added.txt\t(revision 0)\n+++ clone/added.txt\t(revision 0)\n@@ -0,0 +1 @@\n+flam\n\nProperty changes on: clone/added.txt\n===================================================================\nAdded: svn:eol-style\n   + native\n\nIndex: clone/modified.txt\n===================================================================\n--- clone/modified.txt\t(revision 1)\n+++ clone/modified.txt\t(working copy)\n@@ -0,0 +1 @@\n+foo\n\n', output)
         self.assertEqual('Index: clone/added.txt\n===================================================================\n--- clone/added.txt\t(revision 0)\n+++ clone/added.txt\t(revision 0)\n@@ -0,0 +1 @@\n+flam\nIndex: clone/modified.txt\n===================================================================\n--- clone/modified.txt\t(revision 1)\n+++ clone/modified.txt\t(working copy)\n@@ -0,0 +1 @@\n+foo\n\n', output)
         
        
    def test_Rosinstall_diff_svn_outside(self):
        """Test diff output for svn when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--diff"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.check_diff_output(output)

    def test_Rosinstall_diff_svn_inside(self):
        """Test diff output for svn when run inside workspace"""
        # dir created by make
        directory = self.test_root_path + "/ws"
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend([".", "--diff"])
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.check_diff_output(output)

    def test_Rosinstall_status_svn_inside(self):
        """Test status output for svn when run inside workspace"""
        # dir created by make
        directory = self.test_root_path + "/ws"
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend([".", "--status"])
        
        call = subprocess.Popen(cmd, cwd=directory, stdout=subprocess.PIPE)
        output=call.communicate()[0]
        self.assertEqual('A       clone/added.txt\nD       clone/deleted.txt\n!       clone/deleted-fs.txt\nM       clone/modified.txt\n\n', output)
   
    def test_Rosinstall_status_svn_outside(self):
        """Test status output for svn when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--status"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('A       clone/added.txt\nD       clone/deleted.txt\n!       clone/deleted-fs.txt\nM       clone/modified.txt\n\n', output)

    def test_Rosinstall_status_svn_untracked(self):
        """Test status output for svn when run outside workspace"""
        # dir created by make
        cmd = copy.copy(ROSINSTALL_FN)
        cmd.extend(["ws", "--status-untracked"])
        
        call = subprocess.Popen(cmd, cwd=self.test_root_path, stdout=subprocess.PIPE)
        output=call.communicate()[0]

        self.assertEqual('?       clone/added-fs.txt\nA       clone/added.txt\nD       clone/deleted.txt\n!       clone/deleted-fs.txt\nM       clone/modified.txt\n\n', output)

