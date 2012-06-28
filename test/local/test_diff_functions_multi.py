import os
import sys
from StringIO import StringIO
import unittest
import subprocess
import tempfile

import rosinstall
import rosinstall.helpers
import rosinstall.rosws_cli
from rosinstall.rosws_cli import RoswsCLI
from rosinstall.rosinstall_cli import rosinstall_main
from rosinstall.rosws_cli import rosws_main

from test.scm_test_base import AbstractSCMTest, _add_to_file, _nth_line_split

from test.local.test_diff_functions_svn import create_svn_repo, modify_svn_repo
from test.local.test_diff_functions_git import create_git_repo, modify_git_repo
from test.local.test_diff_functions_hg import create_hg_repo, modify_hg_repo
from test.local.test_diff_functions_bzr import create_bzr_repo, modify_bzr_repo

class RosinstallDiffMultiTest(AbstractSCMTest):

    @classmethod
    def setUpClass(self):
        AbstractSCMTest.setUpClass()
        remote_path_svn = os.path.join(self.test_root_path, "remote_svn")
        remote_path_git = os.path.join(self.test_root_path, "remote_git")
        remote_path_bzr = os.path.join(self.test_root_path, "remote_bzr")
        remote_path_hg = os.path.join(self.test_root_path, "remote_hg")
        os.makedirs(remote_path_git)
        os.makedirs(remote_path_svn)
        os.makedirs(remote_path_hg)
        os.makedirs(remote_path_bzr)
        
        filler_path = os.path.join(self.test_root_path, "filler")
        svn_uri = "file://localhost"+remote_path_svn
        
        create_svn_repo(self.test_root_path, remote_path_svn, filler_path, svn_uri)
        create_git_repo(remote_path_git)
        create_hg_repo(remote_path_hg)
        create_bzr_repo(remote_path_bzr)

        # rosinstall the remote repo and fake ros (using git twice to check all overlaps)
        rosinstall_spec = u"""- other: {local-name: ../ros}
- git: {local-name: clone_git, uri: ../remote_git}
- svn: {local-name: clone_svn, uri: '"""+svn_uri+"""'}
- hg: {local-name: clone_hg, uri: ../remote_hg}
- bzr: {local-name: clone_bzr, uri: ../remote_bzr}
- git: {local-name: clone_git2, uri: ../remote_git}"""
        
        _add_to_file(os.path.join(self.local_path, ".rosinstall"), rosinstall_spec)

        cmd = ["rosinstall", "ws", "-n"]
        os.chdir(self.test_root_path)
        rosinstall_main(cmd)

        clone_path_git = os.path.join(self.local_path, "clone_git")
        clone_path_git2 = os.path.join(self.local_path, "clone_git2")
        clone_path_svn = os.path.join(self.local_path, "clone_svn")
        clone_path_hg = os.path.join(self.local_path, "clone_hg")
        clone_path_bzr = os.path.join(self.local_path, "clone_bzr")
        
        modify_git_repo(clone_path_git2)
        modify_git_repo(clone_path_git)
        modify_svn_repo(clone_path_svn)
        modify_hg_repo(clone_path_hg)
        modify_bzr_repo(clone_path_bzr)

    def check_diff_output(self, output):
        self.assertTrue("@@\n+foo\nIndex: clone_svn/added.txt" in output, 'git diff misses newline')
        self.assertTrue("@@\n+foo\ndiff --git clone_hg/added.txt" in output, 'svn diff misses newline')
        self.assertTrue("@@\n+foo\n=== added file 'added.txt'\n--- clone_bzr/added.txt" in output, 'hg diff misses newline')
        self.assertTrue("@@ -0,0 +1,1 @@\n+foo\ndiff --git clone_git2/added.txt" in output, 'svn diff misses newline')

    def test_multi_diff_rosinstall_outside(self):
        '''Test rosinstall diff output from outside workspace.
        In particular asserts that there are newlines between diffs, and no overlaps'''
        cmd = ["rosinstall", "ws", "--diff"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO();
        rosinstall_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.check_diff_output(output)
        
    def test_multi_diff_rosws_outside(self):
        '''Test rosws diff output from outside workspace.
        In particular asserts that there are newlines between diffs, and no overlaps'''
        cmd = ["rosws", "diff", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO();
        rosws_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.check_diff_output(output)

        cli = RoswsCLI()
        self.assertEqual(0,cli.cmd_diff(os.path.join(self.test_root_path, 'ws'), []))

    def test_multi_diff_rosinstall_inside(self):
        '''Test rosinstall diff output from inside workspace.
        In particular asserts that there are newlines between diffs, and no overlaps'''
        directory = self.test_root_path + "/ws"
        cmd = ["rosinstall", ".", "--diff"]
        os.chdir(directory)
        sys.stdout = output = StringIO();
        rosinstall_main(cmd)
        output = output.getvalue()
        self.check_diff_output(output)

    def test_multi_diff_rosws_inside(self):
        '''Test rosws diff output from inside workspace.
        In particular asserts that there are newlines between diffs, and no overlaps'''
        directory = self.test_root_path + "/ws"
        cmd = ["rosws", "diff"]
        os.chdir(directory)
        sys.stdout = output = StringIO();
        rosws_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__
        self.check_diff_output(output)

        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_diff(directory, []))
        
        
    def test_multi_status_rosinstall_inside(self):
        """Test rosinstall status output when run inside workspace.
        In particular asserts that there are newlines between statuses, and no overlaps"""
        directory = self.test_root_path + "/ws"
        cmd = ["rosinstall", ".", "--status"]
        os.chdir(directory)
        sys.stdout = output = StringIO();
        rosinstall_main(cmd)
        output = output.getvalue()

        self.assertEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n', output)

    def test_multi_status_rosws_inside(self):
        """Test rosws status output when run inside workspace.
        In particular asserts that there are newlines between statuses, and no overlaps"""
        directory = self.test_root_path + "/ws"
        cmd = ["rosws", "status"]
        os.chdir(directory)
        sys.stdout = output = StringIO();
        rosws_main(cmd)
        output = output.getvalue()
        sys.stdout = sys.__stdout__
        self.assertEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n', output)

        cli = RoswsCLI()
        self.assertEqual(0,cli.cmd_diff(directory, []))

    def test_multi_status_rosinstall_outside(self):
        """Test rosinstall status output when run outside workspace.
        In particular asserts that there are newlines between statuses, and no overlaps"""
        cmd = ["rosinstall", "ws", "--status"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO();
        rosinstall_main(cmd)
        sys.stdout = output = StringIO();
        rosinstall_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n', output)
        
    def test_multi_status_rosws_outside(self):
        """Test rosws status output when run outside workspace.
        In particular asserts that there are newlines between statuses, and no overlaps"""
        cmd = ["rosws", "status", "-t", "ws"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO();
        rosws_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n', output)

        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_status(os.path.join(self.test_root_path, 'ws'), []))

    def test_multi_status_untracked(self):
        '''tests status output for --untracked.
        In particular asserts that there are newlines between statuses, and no overlaps'''
        cmd = ["rosinstall", "ws", "--status-untracked"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO();
        rosinstall_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\n??      clone_git/added-fs.txt\n?       clone_svn/added-fs.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n?       clone_hg/added-fs.txt\n?       clone_bzr/added-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n??      clone_git2/added-fs.txt\n', output)

        cmd = ["rosws", "status", "-t", "ws", "--untracked"]
        os.chdir(self.test_root_path)
        sys.stdout = output = StringIO();
        rosws_main(cmd)
        sys.stdout = sys.__stdout__
        output = output.getvalue()
        self.assertEqual('A       clone_git/added.txt\n D      clone_git/deleted-fs.txt\nD       clone_git/deleted.txt\n M      clone_git/modified-fs.txt\nM       clone_git/modified.txt\n??      clone_git/added-fs.txt\n?       clone_svn/added-fs.txt\nA       clone_svn/added.txt\nD       clone_svn/deleted.txt\n!       clone_svn/deleted-fs.txt\nM       clone_svn/modified.txt\nM       clone_hg/modified-fs.txt\nM       clone_hg/modified.txt\nA       clone_hg/added.txt\nR       clone_hg/deleted.txt\n!       clone_hg/deleted-fs.txt\n?       clone_hg/added-fs.txt\n?       clone_bzr/added-fs.txt\n+N      clone_bzr/added.txt\n D      clone_bzr/deleted-fs.txt\n-D      clone_bzr/deleted.txt\n M      clone_bzr/modified-fs.txt\n M      clone_bzr/modified.txt\nA       clone_git2/added.txt\n D      clone_git2/deleted-fs.txt\nD       clone_git2/deleted.txt\n M      clone_git2/modified-fs.txt\nM       clone_git2/modified.txt\n??      clone_git2/added-fs.txt\n', output)

        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_status(os.path.join(self.test_root_path, 'ws'), ["--untracked"]))
