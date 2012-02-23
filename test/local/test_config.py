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
import urllib2

import rosinstall.config
from rosinstall.config import MultiProjectException, Config
from rosinstall.config_yaml import PathSpec

class MockVcsClient():

    def __init__(self,
                 path_exists = False,
                 checkout_success = True,
                 update_success = True,
                 vcs_presence = True,
                 url = "mockurl"):
        self.path_exists_flag = path_exists
        self.checkout_success = checkout_success
        self.update_success = update_success
        self.vcs_presence = vcs_presence
        self.mockurl = url
        self.checkedout = vcs_presence
        self.updated = False
        
    def get_vcs_type_name(self):
        return "mocktype"

    def get_diff(self, basepath=None):
        return "mockdiff%s"%basepath

    def get_version(self, revision=None):
        return "mockversion%s"%revision
  
    def get_status(self, basepath=None, untracked=False):
        return "mockstatus%s,%s"%(basepath, untracked)

    def path_exists(self):
        return self.path_exists_flag

    def checkout(self, uri=None, version=None):
        self.checkedout = True
        return self.checkout_success

    def update(self, version):
        self.updated = True
        return self.update_success

    def detect_presence(self):
        return self.vcs_presence

    def get_url(self):
        return self.mockurl


class MockVcsConfigElement(rosinstall.config_elements.VCSConfigElement):

    def __init__(self, scmtype, path, local_name, uri, version = ''):
        self.scmtype = scmtype
        self.path = path
        self.local_name = local_name
        self.uri = uri
        self.version = version
        self.vcsc = MockVcsClient()
    


class ConfigMock_Test(unittest.TestCase):
    
    def test_mock_vcs_element(self):
        yaml = []
        install_path = 'install/path'
        config_filename = '.filename'
        config = Config(yaml, install_path, config_filename)
        try:
            config._create_vcs_config_element('mock', None, None, None)
            fail("expected Exception")
        except MultiProjectException: pass
        config = Config(yaml, install_path, config_filename, {"mock": MockVcsConfigElement})
        self.assertTrue(config._create_vcs_config_element('mock', None, None, None))



class ConfigSimple_Test(unittest.TestCase):

    def _get_mock_config(self, yaml, install_path = 'install/path'):
        config_filename = '.filename'
        return Config(yaml, install_path, config_filename, {"mock": MockVcsConfigElement})
    
    def test_init(self):
        try:
            Config(None, "path", None)
            self.fail("expected Exception")
        except MultiProjectException: pass
        try:
            Config([PathSpec('foo', 'bar')], "path", None)
            self.fail("expected Exception")
        except MultiProjectException: pass
        Config([PathSpec("foo"),
                PathSpec(os.path.join("test", "example_dirs", "ros_comm")),
                PathSpec(os.path.join("test", "example_dirs", "ros")),
                PathSpec(os.path.join("test", "example_dirs", "roscpp")),
                PathSpec("bar")],
               ".",
               None)
        yaml = []
        install_path = 'install/path'
        config_filename = '.filename'
        config = Config(yaml, install_path, config_filename)
        self.assertEqual(install_path, config.get_base_path())
        self.assertEqual([], config.get_config_elements())
        self.assertEqual([], config.get_version_locked_source())

    def test_config_simple1(self):
        mock1 = PathSpec('foo')
        config = self._get_mock_config([mock1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('foo', config.get_config_elements()[0].get_local_name())
        self.assertEqual('install/path/foo', config.get_config_elements()[0].get_path())

    def test_config_simple1_with_setupfile(self):
        mock1 = PathSpec('foo')
        mock1 = PathSpec('setup.sh', tags='setup-file')
        config = self._get_mock_config([mock1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('foo', config.get_config_elements()[0].get_local_name())
        self.assertEqual('install/path/foo', config.get_config_elements()[0].get_path())

        
    def test_config_simple2(self):
        git1 = PathSpec('foo', 'git', 'git/uri')
        svn1 = PathSpec('foos', 'svn', 'svn/uri')
        hg1 = PathSpec('fooh', 'hg', 'hg/uri')
        bzr1 = PathSpec('foob', 'bzr', 'bzr/uri')
        config = self._get_mock_config([git1, svn1, hg1, bzr1])
        self.assertEqual(4, len(config.get_config_elements()))
        self.assertEqual(4, len(config.get_version_locked_source()))
        self.assertEqual('foo', config.get_config_elements()[0].get_local_name())
        self.assertEqual('install/path/foo', config.get_config_elements()[0].get_path())
        self.assertEqual('git', config.get_source()[0].get_scmtype())
        self.assertEqual('git/uri', config.get_source()[0].get_uri())
        self.assertEqual('svn', config.get_source()[1].get_scmtype())
        self.assertEqual('svn/uri', config.get_source()[1].get_uri())
        self.assertEqual('hg', config.get_source()[2].get_scmtype())
        self.assertEqual('hg/uri', config.get_source()[2].get_uri())
        self.assertEqual('bzr', config.get_source()[3].get_scmtype())
        self.assertEqual('bzr/uri', config.get_source()[3].get_uri())


    def test_config_simple3(self):
        git1 = PathSpec('foo', 'git', 'git/uri', 'git.version')
        svn1 = PathSpec('foos', 'svn', 'svn/uri', '12345')
        bzr1 = PathSpec('foob', 'bzr', 'bzr/uri', 'bzr.version')
        hg1 = PathSpec('fooh', 'hg', 'hg/uri', 'hg.version')
        config = self._get_mock_config([git1, svn1, hg1, bzr1])
        self.assertEqual(4, len(config.get_config_elements()))
        self.assertEqual(4, len(config.get_version_locked_source()))

    def test_absolute_localname(self):
        mock1 = PathSpec('/foo/bim')
        config = self._get_mock_config([mock1], install_path = '/foo/bar/ba/ra/baz/bam')
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('/foo/bim', config.get_config_elements()[0].get_local_name())
        self.assertEqual('/foo/bim', config.get_config_elements()[0].get_path())
        
    def test_unnormalized_localname(self):
        "Should source normalize local-name"
        mock1 = PathSpec('foo/bar/..')
        config = self._get_mock_config([mock1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('foo/bar/..', config.get_config_elements()[0].get_local_name())
        self.assertEqual('install/path/foo', config.get_config_elements()[0].get_path())
       
    def test_long_localname(self):
        "Should source choose shorter local-name"
        mock1 = PathSpec("/foo/bar/boo/far/bim")
        config = self._get_mock_config([mock1], '/foo/bar/boo/far')
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual('/foo/bar/boo/far/bim', config.get_config_elements()[0].get_local_name())
        self.assertEqual('/foo/bar/boo/far/bim', config.get_config_elements()[0].get_path())
      
    def test_double_entry(self):
        "Should source be rewritten without duplicates"
        mock1 = PathSpec('foo')
        mock2 = PathSpec('foo')
        config = self._get_mock_config([mock1, mock2])
        self.assertEqual(1, len(config.get_config_elements()))

    def test_equivalent_entry(self):
        "Should source be rewritten without duplicates"
        mock1 = PathSpec('foo')
        mock2 = PathSpec('./foo')
        config = self._get_mock_config([mock1, mock2])
        self.assertEqual(1, len(config.get_config_elements()))

    def test_double_localname(self):
        "Entries have same local name"
        mock1 = PathSpec('foo', 'git', 'git/uri')
        mock2 = PathSpec('foo', 'hg', 'hg/uri')
        config = self._get_mock_config([mock1, mock2])
        self.assertEqual(1, len(config.get_config_elements()))

    def test_equivalent_localname(self):
        "Entries have equivalent local name"
        mock1 = PathSpec('foo', 'git', 'git/uri')
        mock2 = PathSpec('./foo/bar/..', 'hg', 'hg/uri')
        config = self._get_mock_config([mock1, mock2])
        self.assertEqual(1, len(config.get_config_elements()))
