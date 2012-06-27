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

import rosinstall.cli_common
import rosinstall.multiproject_cmd
import rosinstall.multiproject_cli
import rosinstall.config
from rosinstall.common import MultiProjectException
from rosinstall.config import MultiProjectException, Config
from rosinstall.config_yaml import PathSpec

from test.scm_test_base import AbstractSCMTest, _add_to_file, _nth_line_split

def _add_to_file(path, content):
    """Util function to append to file to get a modification"""
    f = io.open(path, 'a')
    f.write(unicode(content))
    f.close()

class GetWorkspaceTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.environback = copy.copy(os.environ)
        self.new_environ = os.environ
        self.test_root_path = tempfile.mkdtemp()
        self.install_path = os.path.join(self.test_root_path, "install")
        os.makedirs(self.install_path)
        self.install_path2 = os.path.join(self.test_root_path, "install2")
        os.makedirs(self.install_path2)
        _add_to_file(os.path.join(self.install_path, "configfile"), 'content')
        path = self.install_path
        for i in range(4):
            path = os.path.join(path, "path%s"%i)
            os.makedirs(path)

        
    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.test_root_path)
        os.environ.update(self.environback)
        
    def test_option_arg(self):
        argv = []
        try:
            self.assertEqual(None, rosinstall.cli_common.get_workspace(argv, self.test_root_path))
            self.fail("expected Exception")
        except MultiProjectException: pass
        argv = ["."]
        try:
            self.assertEqual(None, rosinstall.cli_common.get_workspace(argv, self.test_root_path))
            self.fail("expected Exception")
        except MultiProjectException: pass
        abspath = os.path.abspath('good')
        argv = ['bad', '-a', "foo", '-t', 'good', '-b', 'bar', '--bad']
        self.assertEqual(abspath, rosinstall.cli_common.get_workspace(argv, self.test_root_path))
        argv = ['bad', '-a', "foo", '--target-workspace=good', '-b', 'bar', '--bad']
        self.assertEqual(abspath, rosinstall.cli_common.get_workspace(argv, self.test_root_path))
        argv = ['bad', '-a', "foo", '--target-workspace', 'good', '-b', 'bar', '--bad']
        self.assertEqual(abspath, rosinstall.cli_common.get_workspace(argv, self.test_root_path))

    def test_option_env(self):
        self.new_environ["VARNAME"] = ""
        self.new_environ.pop("VARNAME")
        argv = []
        try:
            self.assertEqual(None, rosinstall.cli_common.get_workspace(argv, self.test_root_path, varname='VARNAME'))
            self.fail("expected Exception")
        except MultiProjectException: pass

        self.new_environ["VARNAME"] = ''
        argv = []
        try:
            self.assertEqual(None, rosinstall.cli_common.get_workspace(argv, self.test_root_path, varname='VARNAME'))
            self.fail("expected Exception")
        except MultiProjectException: pass

        self.new_environ["VARNAME"] = self.install_path2
        argv = []
        self.assertEqual(self.install_path2, rosinstall.cli_common.get_workspace(argv, self.test_root_path, varname='VARNAME'))

    def test_option_path(self):
        path = self.install_path
        self.new_environ["VARNAME"] = self.install_path2
        for i in range(4):
            path = os.path.join(path, "path%s"%i)
            argv = []
            self.assertEqual(self.install_path, rosinstall.cli_common.get_workspace(argv, path, config_filename= "configfile"))
        try:
            self.assertEqual(self.install_path, rosinstall.cli_common.get_workspace(argv, path, config_filename= "configfile", varname='VARNAME'))
            self.fail("expected Exception")
        except MultiProjectException: pass



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
        self.assertEqual("prompt", rosinstall.multiproject_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele = True, ab = False, back = '')
        ferr = FakeErrors()
        self.assertEqual("delete", rosinstall.multiproject_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele = False, ab = True, back = '')
        ferr = FakeErrors()
        self.assertEqual("abort", rosinstall.multiproject_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)
        opts = FakeOpts(dele = False, ab = False, back = 'Foo')
        ferr = FakeErrors()
        self.assertEqual("backup", rosinstall.multiproject_cli._get_mode_from_options(ferr, opts))
        self.assertEqual(None, ferr.rerror)

        opts = FakeOpts(dele = True, ab = True, back = '')
        ferr = FakeErrors()
        rosinstall.multiproject_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)

        opts = FakeOpts(dele = False, ab = True, back = 'Foo')
        ferr = FakeErrors()
        rosinstall.multiproject_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)

        opts = FakeOpts(dele = True, ab = False, back = 'Foo')
        ferr = FakeErrors()
        rosinstall.multiproject_cli._get_mode_from_options(ferr, opts)
        self.assertFalse(None is ferr.rerror)


        
class FakeConfig():
    def __init__(self, elts = [], path = ''):
        self.elts = elts
        self.path = path
    def get_config_elements(self):
        return self.elts
    def get_base_path(self):
        return self.path

class MockVcsConfigElement(rosinstall.config_elements.VCSConfigElement):

    def __init__(self, scmtype, path, local_name, uri, version = '', actualversion = '', specversion = '', properties = None):
        self.scmtype = scmtype
        self.path = path
        self.local_name = local_name
        self.vcsc = MockVcsClient(scmtype, actualversion = actualversion, specversion = specversion)
        self.uri = uri
        self.version = version
        self.install_success = True
        self.properties = properties

    def install(self, checkout=True, backup = False, backup_path = None, robust = False, verbose=False):
        if not self.install_success:
            raise MultiProjectException("Unittest Mock says install failed")

    def _get_vcsc(self):
        return self.vcsc

class MockVcsClient():

    def __init__(self,
                 scmtype = 'mocktype',
                 path_exists = False,
                 checkout_success = True,
                 update_success = True,
                 vcs_presence = False,
                 url = "mockurl",
                 actualversion = None,
                 specversion = None):
        self.scmtype = scmtype
        self.path_exists_flag = path_exists
        self.checkout_success = checkout_success
        self.update_success = update_success
        self.vcs_presence = vcs_presence
        self.mockurl = url
        self.checkedout = vcs_presence
        self.updated = False
        self.actualversion = actualversion
        self.specversion = specversion
        
    def get_vcs_type_name(self):
        return self.scmtype

    def get_diff(self, basepath=None):
        return self.scmtype + "mockdiff%s"%basepath

    def get_version(self, revision=None):
        if revision == None:
            return self.actualversion
        else:
            return self.specversion
  
    def get_status(self, basepath=None, untracked=False):
        return self.scmtype + " mockstatus%s,%s"%(basepath, untracked)

    def path_exists(self):
        return self.path_exists_flag

    def checkout(self, uri=None, version=None, verbose=False):
        self.checkedout = True
        return self.checkout_success

    def update(self, version, verbose=False):
        self.updated = True
        return self.update_success

    def detect_presence(self):
        return self.vcs_presence

    def get_url(self):
        return self.mockurl

class InstallTest(unittest.TestCase):
    def test_mock_install(self):
        git1 = PathSpec('foo', 'git', 'git/uri', 'git.version')
        svn1 = PathSpec('foos', 'svn', 'svn/uri', '12345')
        hg1 = PathSpec('fooh', 'hg', 'hg/uri', 'hg.version')
        bzr1 = PathSpec('foob', 'bzr', 'bzr/uri', 'bzr.version')
        config = Config([git1, svn1, hg1, bzr1],
                        '.',
                        None,
                        {"svn": MockVcsConfigElement,
                         "git": MockVcsConfigElement,
                         "hg": MockVcsConfigElement,
                         "bzr": MockVcsConfigElement})
        rosinstall.multiproject_cmd.cmd_install_or_update(config)
        rosinstall.multiproject_cmd.cmd_install_or_update(config)
        rosinstall.multiproject_cmd.cmd_install_or_update(config, num_threads=10)
        rosinstall.multiproject_cmd.cmd_install_or_update(config, num_threads=10)
        rosinstall.multiproject_cmd.cmd_install_or_update(config, num_threads=1)
        rosinstall.multiproject_cmd.cmd_install_or_update(config, num_threads=1)

    def test_mock_install_fail(self):
        # robust
        git1 = PathSpec('foo', 'git', 'git/uri', 'git.version')
        svn1 = PathSpec('foos', 'svn', 'svn/uri', '12345')
        hg1 = PathSpec('fooh', 'hg', 'hg/uri', 'hg.version')
        bzr1 = PathSpec('foob', 'bzr', 'bzr/uri', 'bzr.version')
        config = Config([git1, svn1, hg1, bzr1],
                        '.',
                        None,
                        {"svn": MockVcsConfigElement,
                         "git": MockVcsConfigElement,
                         "hg": MockVcsConfigElement,
                         "bzr": MockVcsConfigElement})
        config.get_config_elements()[1].install_success = False
        rosinstall.multiproject_cmd.cmd_install_or_update(config, robust = True)
        try:
            rosinstall.multiproject_cmd.cmd_install_or_update(config, robust = False)
            self.fail("expected Exception")
        except MultiProjectException:
            pass
    
class GetStatusDiffCmdTest(unittest.TestCase):

    def test_status(self):
        self.mock_config = FakeConfig()
        result = rosinstall.multiproject_cmd.cmd_status(self.mock_config)
        self.assertTrue(len(result) == 0)
        self.mock_config = FakeConfig([MockVcsConfigElement('git', 'gitpath', 'gitname', None)])
        result = rosinstall.multiproject_cmd.cmd_status(self.mock_config)
        self.assertTrue(len(result) == 1)
        self.assertTrue(result[0]['status'] is not None)
        self.assertTrue(result[0]['entry'] is not None)
        self.mock_config = FakeConfig([MockVcsConfigElement('git', 'gitpath', 'gitname', None),
                                       MockVcsConfigElement('svn', 'svnpath', 'svnname', None),
                                       MockVcsConfigElement('hg', 'hgpath', 'hgname', None),
                                       MockVcsConfigElement('bzr', 'bzrpath', 'bzrname', None)])
        result = rosinstall.multiproject_cmd.cmd_status(self.mock_config)
        self.assertTrue(len(result) == 4)
        self.assertTrue(result[0]['status'].count('git')==1)
        self.assertTrue(result[1]['status'].count('svn')==1)
        self.assertTrue(result[2]['status'].count('hg')==1)
        self.assertTrue(result[3]['status'].count('bzr')==1)

          
    def test_diff(self):
        self.mock_config = FakeConfig()
        result = rosinstall.multiproject_cmd.cmd_diff(self.mock_config)
        self.assertTrue(len(result) == 0)
        self.mock_config = FakeConfig([MockVcsConfigElement('git', 'gitpath', 'gitname', None)])
        result = rosinstall.multiproject_cmd.cmd_diff(self.mock_config)
        self.assertEqual(1, len(result))
        self.assertTrue(result[0]['diff'] is not None)
        self.assertTrue(result[0]['entry'] is not None)
        self.mock_config = FakeConfig([MockVcsConfigElement('git', 'gitpath', 'gitname', None),
                                       MockVcsConfigElement('svn', 'svnpath', 'svnname', None),
                                       MockVcsConfigElement('hg', 'hgpath', 'hgname', None),
                                       MockVcsConfigElement('bzr', 'bzrpath', 'bzrname', None)])
        result = rosinstall.multiproject_cmd.cmd_diff(self.mock_config)
        self.assertTrue(len(result) == 4)
        self.assertTrue(result[0]['diff'].count('git')==1)
        self.assertTrue(result[1]['diff'].count('svn')==1)
        self.assertTrue(result[2]['diff'].count('hg')==1)
        self.assertTrue(result[3]['diff'].count('bzr')==1)


    def test_info(self):
        self.mock_config = FakeConfig([], 'foopath')
        result = rosinstall.multiproject_cmd.cmd_info(self.mock_config)
        self.assertTrue(len(result) == 0)
        self.mock_config = FakeConfig([MockVcsConfigElement('git', 'gitpath', 'gitname', None, version = 'version')],
                                      'foopath')
        result = rosinstall.multiproject_cmd.cmd_info(self.mock_config)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['scm'], 'git')
        self.assertEqual(result[0]['version'], 'version')
   
        
        self.mock_config = FakeConfig([MockVcsConfigElement('git', 'gitpath', 'gitname', None),
                                       MockVcsConfigElement('svn', 'svnpath', 'svnname', None),
                                       MockVcsConfigElement('hg', 'hgpath', 'hgname', None),
                                       MockVcsConfigElement('bzr', 'bzrpath', 'bzrname', None)],
                                      'foopath')
        result = rosinstall.multiproject_cmd.cmd_info(self.mock_config)
        self.assertTrue(len(result) == 4)
        self.assertTrue(result[0]['scm'] == 'git')
        self.assertTrue(result[1]['scm'] == 'svn')
        self.assertTrue(result[2]['scm'] == 'hg')
        self.assertTrue(result[3]['scm'] == 'bzr')

    def test_info_real_path(self):
        root_path = tempfile.mkdtemp()
        el_path = os.path.join(root_path, "ros")
        os.makedirs(el_path)
        try:
            self.mock_config = FakeConfig([], 'foopath')
            result = rosinstall.multiproject_cmd.cmd_info(self.mock_config)
            self.assertTrue(len(result) == 0)
            mock = MockVcsConfigElement('git',
                                        el_path,
                                        'gitname',
                                        None,
                                        version = 'version',
                                        actualversion = 'actual',
                                        specversion = 'spec')
            self.mock_config = FakeConfig([mock], 'foopath')
            result = rosinstall.multiproject_cmd.cmd_info(self.mock_config)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['scm'], 'git')
            self.assertEqual(result[0]['version'], 'version')
            self.assertEqual(result[0]['specversion'], 'spec')
            self.assertEqual(result[0]['actualversion'], 'actual')
            mock = MockVcsConfigElement('git',
                                        el_path,
                                        'gitname',
                                        None,
                                        version = 'version',
                                        actualversion = 'actual',
                                        specversion = None) # means scm does not know version
            self.mock_config = FakeConfig([mock], 'foopath')
            result = rosinstall.multiproject_cmd.cmd_info(self.mock_config)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['scm'], 'git')
            self.assertEqual(result[0]['version'], 'version')
            self.assertEqual(result[0]['specversion'], '"version"')
            self.assertEqual(result[0]['actualversion'], 'actual')
            
        finally:
            shutil.rmtree(root_path)
        

    def test_get_status(self):
        self.test_root_path = tempfile.mkdtemp()
        try:
            basepath = '/foo/path'
            entry = {}
            self.assertEqual('', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'exists': False}
            self.assertEqual('x', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'exists': False, 'modified': True}
            self.assertEqual('x', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'exists': True, 'modified': True}
            self.assertEqual('M', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'modified': True}
            self.assertEqual('M', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'actualversion': 'foo', 'specversion': 'bar'}
            self.assertEqual('V', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'actualversion': 'foo', 'specversion': 'foo'}
            self.assertEqual('', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'uri': 'foo', 'curr_uri': 'foo'}
            self.assertEqual('', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'uri': 'foo', 'curr_uri': 'bar'}
            self.assertEqual('V', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'uri': self.test_root_path, 'curr_uri': self.test_root_path}
            self.assertEqual('', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'uri': self.test_root_path, 'curr_uri': self.test_root_path+'/foo/..'}
            self.assertEqual('', rosinstall.cli_common._get_status_flags(basepath, entry))
            entry = {'actualversion': 'foo', 'specversion': 'bar', 'modified': True}
            self.assertEqual('MV', rosinstall.cli_common._get_status_flags(basepath, entry))
        finally:
            shutil.rmtree(self.test_root_path)
        
    def test_info_table(self):
        basepath = '/foo/path'
        entries = []
        self.assertEqual('', rosinstall.cli_common.get_info_table(basepath, entries))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'uri',
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "scm", "version", "uri"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'uri',
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': 'specversion',
                    'actualversion': 'actualversion'}]
        self.assertEqual(["localname", 'V', "scm", "version", "actualversion", "(specversion)", "uri"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'curr_uri': 'curr_uri',
                    'version': 'version',
                    'localname': 'localname'}]
        self.assertEqual(["localname", 'V', "scm", "version", "curr_uri", "(uri)"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'scm',
                    'uri': 'uri',
                    'version': 'version',
                    'localname': 'localname',
                    'exists': False}]
        self.assertEqual(["localname", 'x', "scm", "version", "uri"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        # shorten SHAIDs for git
        entries = [{'scm': 'git',
                    'uri': 'uri',
                    'actualversion': '01234567890123456789012345678',
                    'localname': 'localname',
                    'exists': False}]
        self.assertEqual(["localname", 'x', "git", "012345678901", "uri"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'git',
                    'uri': 'uri',
                    'actualversion': '01234567890123456789012345678',
                    'specversion': '1234567890123456789012345678',
                    'localname': 'localname'}]
        self.assertEqual(["localname", 'V', "git", "012345678901", "(123456789012)", "uri"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        # recompute svn startdard layout
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/tags/tagname',
                    'curr_uri': None,
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "svn", "tags/tagname", "some.svn.tags.server/some/"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/branches/branchname',
                    'curr_uri': None,
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "svn", "branches/branchname", "some.svn.tags.server/some/"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/trunk',
                    'curr_uri': None,
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "svn", "trunk", "some.svn.tags.server/some/"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/branches/branchname',
                    'curr_uri': 'https://some.svn.tags.server/some/tags/tagname',
                    'version': 'version',
                    'localname': 'localname',
                    'specversion': None,
                    'actualversion': None}]
        self.assertEqual(["localname", "svn", "tags/tagname", "(branches/branchname)", "some.svn.tags.server/some/"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))
        entries = [{'scm': 'svn',
                    'uri': 'https://some.svn.tags.server/some/branches/branchname',
                    'curr_uri': 'https://some.svn.tags.server/some/tags/tagname',
                    'version': None,
                    'localname': 'localname',
                    'specversion': 'broken',
                    'actualversion': 'version'}]
        self.assertEqual(["localname", "V", "svn", "tags/tagname", "(branches/branchname)", "version", "(broken)", "some.svn.tags.server/some/"], _nth_line_split(-1, rosinstall.cli_common.get_info_table(basepath, entries)))

        
    def test_info_list(self):
        basepath = '/foo/path'
        entry = {'scm': 'somescm',
                 'uri': 'someuri',
                 'curr_uri': 'somecurr_uri',
                 'version': 'someversion',
                 'specversion': 'somespecversion',
                 'actualversion': 'someactualversion',
                 'localname': 'somelocalname',
                 'path': 'somepath'}
        result =  rosinstall.cli_common.get_info_list(basepath, entry).split()
        for x in ['somepath', 'somelocalname', 'someactualversion', 'somespecversion', 'someversion', 'somecurr_uri', 'someuri', 'somescm']:
            self.assertTrue(x in result)
