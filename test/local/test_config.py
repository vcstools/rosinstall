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
from rosinstall.config import MultiProjectException

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
    
    def test_mock_vcs_lement(self):
        yaml = []
        install_path = 'install/path'
        config_filename = '.filename'
        config = rosinstall.config.Config(yaml, install_path, config_filename)
        try:
            config._create_vcs_config_element('mock', None, None, None)
            fail("expected Exception")
        except MultiProjectException: pass
        config = rosinstall.config.Config(yaml, install_path, config_filename, {"mock": MockVcsConfigElement})
        self.assertTrue(config._create_vcs_config_element('mock', None, None, None))



class ConfigSimple_Test(unittest.TestCase):

    def _get_mock_config(self, yaml, install_path = 'install/path'):
        config_filename = '.filename'
        return rosinstall.config.Config(yaml, install_path, config_filename, {"mock": MockVcsConfigElement})
    
    def test_init(self):
        try:
            config = rosinstall.config.Config(None, None, None)
            self.fail("expected Exception")
        except MultiProjectException: pass
        try:
            config = rosinstall.config.Config([{'foo': 'bar'}], None, None)
            self.fail("expected Exception")
        except MultiProjectException: pass
        try:
            config = self._get_mock_config([{'mock': {}}])
            self.fail("expected Exception")
        except MultiProjectException: pass
        try:
            config = self._get_mock_config([{'mock': {"local-name": None}}])
            self.fail("expected Exception")
        except MultiProjectException: pass
        yaml = []
        install_path = 'install/path'
        config_filename = '.filename'
        config = rosinstall.config.Config(yaml, install_path, config_filename)
        self.assertEqual(install_path, config.get_base_path())
        self.assertEqual([], config.get_config_elements())
        self.assertEqual([], config.get_source())
        self.assertEqual([], config.get_version_locked_source())

    def test_config_simple1(self):
        mock1 = {'mock': {"local-name": "foo"}}
        config = self._get_mock_config([mock1])
        self.assertEqual(1, len(config.get_config_elements()))
        self.assertEqual(1, len(config.get_source()))
        self.assertEqual(1, len(config.get_version_locked_source()))
        self.assertEqual([{'mock': {'local-name': 'foo'}}], config.get_source())

        
    def test_config_simple2(self):
        mock1 = {'mock': {"local-name": "foom"}}
        git1 = {'git': {"local-name": "foog", "uri": "git/uri"}}
        svn1 = {'svn': {"local-name": "foos", "uri": "svn/uri"}}
        bzr1 = {'bzr': {"local-name": "foob", "uri": "bzr/uri"}}
        hg1 = {'hg': {"local-name": "fooh", "uri": "hg/uri"}}
        config = self._get_mock_config([mock1, git1, svn1, hg1, bzr1])
        self.assertEqual(5, len(config.get_config_elements()))
        self.assertEqual(5, len(config.get_source()))
        self.assertEqual(5, len(config.get_version_locked_source()))
        self.assertEqual([{'mock': {'local-name': 'foom'}}, {'git': {'local-name': 'foog', 'uri': 'git/uri'}}, {'svn': {'local-name': 'foos', 'uri': 'svn/uri'}}, {'hg': {'local-name': 'fooh', 'uri': 'hg/uri'}}, {'bzr': {'local-name': 'foob', 'uri': 'bzr/uri'}}], config.get_source())
        self.assertEqual([{'mocktype': {'local-name': 'install/path/foom', 'version': 'mockversionNone', 'uri': None, 'revision': ''}}, {'git': {'local-name': 'install/path/foog', 'version': None, 'uri': 'git/uri', 'revision': ''}}, {'svn': {'local-name': 'install/path/foos', 'version': None, 'uri': 'svn/uri', 'revision': ''}}, {'hg': {'local-name': 'install/path/fooh', 'version': None, 'uri': 'hg/uri', 'revision': ''}}, {'bzr': {'local-name': 'install/path/foob', 'version': None, 'uri': 'bzr/uri', 'revision': ''}}], config.get_version_locked_source())


    def test_config_simple3(self):
        mock1 = {'mock': {"local-name": "foom"}}
        git1 = {'git': {"local-name": "foog", "uri": "git/uri", "version": "git.version"}}
        svn1 = {'svn': {"local-name": "foos", "uri": "svn/uri", "version": "12345"}}
        bzr1 = {'bzr': {"local-name": "foob", "uri": "bzr/uri", "version": "bzr.version"}}
        hg1 = {'hg': {"local-name": "fooh", "uri": "hg/uri", "version": "hg.version"}}
        config = self._get_mock_config([mock1, git1, svn1, hg1, bzr1])
        self.assertEqual(5, len(config.get_config_elements()))
        self.assertEqual(5, len(config.get_source()))
        self.assertEqual(5, len(config.get_version_locked_source()))
        self.assertEqual([{'mock': {'local-name': 'foom'}}, {'git': {'local-name': 'foog', 'version': 'git.version', 'uri': 'git/uri'}}, {'svn': {'local-name': 'foos', 'version': '12345', 'uri': 'svn/uri'}}, {'hg': {'local-name': 'fooh', 'version': 'hg.version', 'uri': 'hg/uri'}}, {'bzr': {'local-name': 'foob', 'version': 'bzr.version', 'uri': 'bzr/uri'}}], config.get_source())
        self.assertEqual([{'mocktype': {'local-name': 'install/path/foom', 'version': 'mockversionNone', 'uri': None, 'revision': ''}}, {'git': {'local-name': 'install/path/foog', 'version': None, 'uri': 'git/uri', 'revision': None}}, {'svn': {'local-name': 'install/path/foos', 'version': None, 'uri': 'svn/uri', 'revision': None}}, {'hg': {'local-name': 'install/path/fooh', 'version': None, 'uri': 'hg/uri', 'revision': None}}, {'bzr': {'local-name': 'install/path/foob', 'version': None, 'uri': 'bzr/uri', 'revision': None}}], config.get_version_locked_source())

