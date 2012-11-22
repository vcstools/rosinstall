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
import sys
import copy
import yaml
import subprocess
import tempfile
import shutil
import rosinstall
import rosinstall.helpers
from test.io_wrapper import StringIO
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
        except SystemExit:
            pass
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(os.path.join(workspace, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(workspace, 'setup.sh')))
        self.assertTrue(os.path.isdir(os.path.join(workspace, 'ros')))
        self.assertTrue(os.path.isdir(os.path.join(workspace, 'gitrepo')))
        self.assertTrue(os.path.isdir(os.path.join(workspace, 'gitrepo', '.git')))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(2, len(config.get_config_elements()))

    def test_init_pwd(self):
        workspace = os.path.join(self.test_root_path, 'ws1b')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace]))
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(os.path.join(workspace, '.rosinstall')))
        self.assertTrue(os.path.exists(os.path.join(workspace, 'setup.sh')))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(0, len(config.get_config_elements()))

    def test_init_parallel(self):
        workspace = os.path.join(self.test_root_path, 'ws1d')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall, "--parallel=5"]))
        self.assertTrue(os.path.exists(workspace))
        self.assertTrue(os.path.exists(os.path.join(workspace, '.rosinstall')))

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
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))

    def test_remove(self):
        workspace = os.path.join(self.test_root_path, 'ws3')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        self.assertEqual(0, cli.cmd_merge(workspace, [self.simple_changed_vcs_rosinstall, '-y']))
        self.assertEqual(0, cli.cmd_update(workspace, []))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual(0, cli.cmd_remove(workspace, ['hgrepo']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(2, len(config.get_config_elements()))

    def test_set_detached(self):
        workspace = os.path.join(self.test_root_path, 'ws4')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        self.assertEqual(0, cli.cmd_merge(workspace, [self.simple_changed_vcs_rosinstall, '-y']))
        self.assertEqual(0, cli.cmd_update(workspace, []))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        self.assertEqual(True, config.get_config_elements()[1].is_vcs_element())
        self.assertEqual('hgrepo', config.get_config_elements()[2].get_local_name())
        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, 'gitrepo'), '--detached', '-y']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        self.assertEqual(False, config.get_config_elements()[1].is_vcs_element())
        self.assertEqual('hgrepo', config.get_config_elements()[2].get_local_name())

    def test_set_add_plain(self):
        workspace = os.path.join(self.test_root_path, 'ws5')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        # detached
        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, 'foo'), '-y']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        self.assertEqual(False, config.get_config_elements()[2].is_vcs_element())
        self.assertEqual('foo', config.get_config_elements()[2].get_local_name())
        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, 'hgrepo'), '-y', '--detached']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(4, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        self.assertEqual(False, config.get_config_elements()[2].is_vcs_element())
        self.assertEqual('foo', config.get_config_elements()[2].get_local_name())
        self.assertEqual(False, config.get_config_elements()[3].is_vcs_element())
        self.assertEqual('hgrepo', config.get_config_elements()[3].get_local_name())
        # turn into scm repo
        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, 'hgrepo'), '../hgrepo', '-y', '--hg']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(4, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        self.assertTrue(config.get_config_elements()[3].is_vcs_element())
        self.assertEqual('hgrepo', config.get_config_elements()[3].get_local_name())

    def test_set_add_scm(self):
        workspace = os.path.join(self.test_root_path, 'ws6')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())

        # scm repo
        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, 'hgrepo'), '../hgrepo', '-y', '--hg']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(3, len(config.get_config_elements()))
        self.assertEqual('ros', config.get_config_elements()[0].get_local_name())
        self.assertEqual('gitrepo', config.get_config_elements()[1].get_local_name())
        self.assertTrue(config.get_config_elements()[2].is_vcs_element())
        self.assertEqual('hgrepo', config.get_config_elements()[2].get_local_name())
        self.assertFalse(os.path.exists(os.path.join(workspace, 'hgrepo')))

        self.assertEqual(0, cli.cmd_update(workspace, []))
        self.assertTrue(os.path.exists(os.path.join(workspace, 'hgrepo')))

        path_spec = config.get_config_elements()[2].get_versioned_path_spec()
        self.assertFalse(path_spec is None)
        self.assertEqual(None, path_spec.get_version())
        self.assertEqual(None, path_spec.get_revision())
        self.assertFalse(path_spec.get_current_revision() is None)

        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, 'hgrepo'), '--version-new=0', '-y']))

        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        path_spec = config.get_config_elements()[2].get_versioned_path_spec()
        self.assertEqual('0', path_spec.get_version())
        self.assertFalse(path_spec.get_revision() is None)
        self.assertFalse(path_spec.get_current_revision() is None)
        self.assertEqual(path_spec.get_revision(), path_spec.get_current_revision())

        # change in FS to version 1
        subprocess.check_call(["touch", "hgfixed2.txt"], cwd=os.path.join(workspace, 'hgrepo'))
        subprocess.check_call(["hg", "add", "hgfixed2.txt"], cwd=os.path.join(workspace, 'hgrepo'))
        subprocess.check_call(["hg", "commit", "-m", "2nd"], cwd=os.path.join(workspace, 'hgrepo'))
        self.assertTrue(os.path.exists(os.path.join(workspace, 'hgrepo', 'hgfixed2.txt')))

        path_spec = config.get_config_elements()[2].get_versioned_path_spec()
        self.assertEqual('0', path_spec.get_version())
        self.assertFalse(path_spec.get_revision() is None)
        self.assertFalse(path_spec.get_current_revision() is None)
        self.assertNotEqual(path_spec.get_revision(), path_spec.get_current_revision())

        # revert FS to spec
        self.assertEqual(0, cli.cmd_update(workspace, []))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        path_spec = config.get_config_elements()[2].get_versioned_path_spec()
        self.assertEqual('0', path_spec.get_version())
        self.assertFalse(path_spec.get_revision() is None)
        self.assertFalse(path_spec.get_current_revision() is None)
        self.assertEqual(path_spec.get_revision(), path_spec.get_current_revision())

        # change spec to 1
        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, 'hgrepo'), '--version-new=1', '-y']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        path_spec = config.get_config_elements()[2].get_versioned_path_spec()
        self.assertEqual('1', path_spec.get_version())
        self.assertFalse(path_spec.get_revision() is None)
        self.assertFalse(path_spec.get_current_revision() is None)
        self.assertNotEqual(path_spec.get_revision(), path_spec.get_current_revision())

        # setting version to ''
        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, 'hgrepo'), "--version-new=''", '-y']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        path_spec = config.get_config_elements()[2].get_versioned_path_spec()
        self.assertEqual(None, path_spec.get_version())
        self.assertTrue(path_spec.get_revision() is None)
        self.assertFalse(path_spec.get_current_revision() is None)

        self.assertEqual(0, cli.cmd_update(workspace, []))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        path_spec = config.get_config_elements()[2].get_versioned_path_spec()
        self.assertEqual(None, path_spec.get_version())
        self.assertTrue(path_spec.get_revision() is None)
        self.assertFalse(path_spec.get_current_revision() is None)

    def test_info_only(self):
        workspace = os.path.join(self.test_root_path, 'ws7')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.simple_rosinstall]))
        #pkg_path
        sys.stdout = output = StringIO();
        self.assertEqual(0, cli.cmd_info(workspace, ['--pkg-path-only']))
        output = output.getvalue()
        self.assertEqual(os.path.join(workspace, 'gitrepo'), output.strip())

        sys.stdout = output = StringIO();
        self.assertEqual(0, cli.cmd_info(workspace, ['--only=localname']))
        output = output.getvalue()
        self.assertEqual('ros\ngitrepo', output.strip())

        sys.stdout = output = StringIO();
        self.assertEqual(0, cli.cmd_info(workspace, ['--only=version']))
        output = output.getvalue()
        self.assertEqual('', output.strip())

        sys.stdout = output = StringIO();
        self.assertEqual(0, cli.cmd_info(workspace, ['--only=uri']))
        output = output.getvalue()
        self.assertEqual('%s\n%s\n' % (os.path.join(self.test_root_path, 'ros'), os.path.join(self.test_root_path, 'gitrepo')), output)

        sys.stdout = output = StringIO();
        self.assertEqual(0, cli.cmd_info(workspace, ['--only=cur_revision']))
        output = output.getvalue()
        self.assertEqual(82, len(output))
        sys.stdout = sys.__stdout__

        # pairs
        sys.stdout = output = StringIO();
        self.assertEqual(0, cli.cmd_info(workspace, ['--only=localname,scmtype']))
        output = output.getvalue()
        self.assertEqual('ros,git\ngitrepo,git', output.strip())
        sys.stdout = output = StringIO();
        self.assertEqual(0, cli.cmd_info(workspace, ['--only=scmtype,localname']))
        output = output.getvalue()
        self.assertEqual('git,ros\ngit,gitrepo', output.strip())

    def test_set_add_scm_change_localname(self):
        workspace = os.path.join(self.test_root_path, 'ws8')
        cli = RoswsCLI()
        self.assertEqual(0, cli.cmd_init([workspace, self.ros_path]))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual(os.path.join(self.test_root_path, 'ros'), config.get_config_elements()[0].get_local_name())

        # use a weird absolute localname
        self.assertEqual(0, cli.cmd_set(workspace, [os.path.join(workspace, '..', 'ws8', 'hgrepo'), '../hgrepo', '-y', '--hg']))
        config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
        self.assertEqual(2, len(config.get_config_elements()))
        self.assertEqual('hgrepo', config.get_config_elements()[1].get_local_name())

        oldcwd = os.getcwd()
        try:
            os.chdir(self.test_root_path)
            # try pointing to a relative dir that also exists elsewhere
            try:
                cli.cmd_set(workspace, ['gitrepo', '../gitrepo', '-y', '--hg'])
                self.fail("Expected SystemExit")
            except SystemExit:
                pass
            # use a weird relative localname
            self.assertEqual(0, cli.cmd_set(workspace, [os.path.join('ws8', 'gitrepo'), '../gitrepo', '-y', '--hg']))
            config = rosinstall.multiproject_cmd.get_config(workspace, config_filename='.rosinstall')
            self.assertEqual(3, len(config.get_config_elements()))

            self.assertEqual('hgrepo', config.get_config_elements()[1].get_local_name())
            self.assertEqual('gitrepo', config.get_config_elements()[2].get_local_name())
        finally:
            os.chdir(oldcwd)
