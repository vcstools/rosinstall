import os
import unittest
import copy
import yaml
import tempfile
import shutil

import rosinstall.config_yaml
import rosinstall.config
from rosinstall.common import MultiProjectException
from rosinstall.config_yaml import rewrite_included_source, get_path_spec_from_yaml, get_yaml_from_uri, get_path_specs_from_uri, PathSpec


class YamlIO_Test(unittest.TestCase):

    def test_get_yaml_from_uri_from_file(self):
        file = os.path.join("test", "example.yaml")
        y = get_yaml_from_uri(file)
        
        self.assertTrue("text" in y)
        self.assertTrue(y["text"] == "foobar")

        self.assertTrue("number" in y)
        self.assertTrue(y["number"] == 2)
        # invalid
        try:
            yaml = get_yaml_from_uri(os.path.join("test", "example-broken.yaml"))
        except MultiProjectException:
            pass
        try:
            get_path_specs_from_uri(file)
            self.fail("Expected exception")
        except MultiProjectException:
            pass

        
    def test_get_yaml_from_uri_from_missing_file(self):
        file = "/asdfasdfasdfasfasdf_does_not_exist"
        try:
            get_yaml_from_uri(file)
            self.fail("Expected exception")
        except MultiProjectException:
            pass
        try:
            get_path_specs_from_uri(file)
            self.fail("Expected exception")
        except MultiProjectException:
            pass

#TODO Fix this
#    def test_get_yaml_from_uri_from_non_yaml_file(self):
#        file = os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "Makefile")
#        y = rosinstall.config.get_yaml_from_uri(file)
#        self.assertEqual(y, None)



class ConfigElementYamlFunctions_Test(unittest.TestCase):

    

    def test_rewrite_included_source(self):
        base_path = '/foo/bar'
        version = 'common_rosdeps-1.0.2'
        uri = 'https://kforge.ros.org/common/rosdepcore'
        # same simple
        struct = [PathSpec('local', 'hg', uri, version)]
        rewrite_included_source(struct, "/foo/bar")
        self.assertEqual(PathSpec(os.path.join(base_path, "local")), struct[0])
        # absolute path
        struct = [PathSpec("/opt/poo", 'hg', uri, version)]
        rewrite_included_source(struct, "/foo/bar")
        self.assertEqual([PathSpec("/opt/poo")], struct)
        # absolute path, relative basepath
        struct = [PathSpec("/opt/poo", 'hg', uri, version)]
        rewrite_included_source(struct, "foo/bar")
        self.assertEqual([PathSpec("/opt/poo")], struct)
        # relative base path
        struct = [PathSpec("../opt/poo", 'hg', uri, version)]
        rewrite_included_source(struct, "foo/bar")
        self.assertEqual([PathSpec("foo/opt/poo")], struct)

    def test_rewrite_included_source_setupfile(self):
        base_path = '/foo/bar'
        version = 'common_rosdeps-1.0.2'
        uri = 'https://kforge.ros.org/common/rosdepcore'
        # same simple
        struct = [PathSpec('local', tags='setup-file')]
        rewrite_included_source(struct, "/foo/bar")
        self.assertEqual(PathSpec(os.path.join(base_path, "local"), tags='setup-file'), struct[0])
        # absolute path
        struct = [PathSpec("/opt/poo", tags='setup-file')]
        rewrite_included_source(struct, "/foo/bar")
        self.assertEqual([PathSpec("/opt/poo", tags='setup-file')], struct)
        # absolute path, relative basepath
        struct = [PathSpec("/opt/poo", tags='setup-file')]
        rewrite_included_source(struct, "foo/bar")
        self.assertEqual([PathSpec("/opt/poo", tags='setup-file')], struct)
        # relative base path
        struct = [PathSpec("../opt/poo", tags='setup-file')]
        rewrite_included_source(struct, "foo/bar")
        self.assertEqual([PathSpec("foo/opt/poo", tags='setup-file')], struct)


class UriAggregationTest(unittest.TestCase):

    def test_aggregate_from_uris(self):
        pass
        

class ConfigFile_Test(unittest.TestCase):

    def test_generate(self):
        self.directory = tempfile.mkdtemp()
        config = rosinstall.config.Config([], self.directory)
        rosinstall.config_yaml.generate_config_yaml(config, 'foo', "# Hello\n")
        filepath = os.path.join(self.directory, 'foo')
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            read_data = f.read()
        lines = read_data.splitlines()
        self.assertEqual("# Hello", lines[0])

    def test_generate_with_stack(self):
        self.directory = tempfile.mkdtemp()
        config = rosinstall.config.Config([PathSpec('ros', 'svn', 'some/uri')], self.directory)
        rosinstall.config_yaml.generate_config_yaml(config, 'foo', "# Hello\n")
        filepath = os.path.join(self.directory, 'foo')
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            read_data = f.read()
        lines = read_data.splitlines()
        self.assertEqual("# Hello", lines[0])
        self.assertEqual("- svn: {local-name: ros, uri: %s/some/uri}"%self.directory, lines[1])

    def tearDown(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
        
        
class ConfigElementYamlWrapper_Test(unittest.TestCase):

    def test_original_syntax_scm(self):
        # - hg: {local-name: common_rosdeps, version: common_rosdeps-1.0.2, uri: https://kforge.ros.org/common/rosdepcore}
        local_name = 'common_rosdeps'
        version = 'common_rosdeps-1.0.2'
        uri = 'https://kforge.ros.org/common/rosdepcore'
        scmtype = 'hg'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(scmtype, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual(struct, wrap.get_legacy_yaml())
    
        # empty version
        local_name = 'common_rosdeps'
        version = None
        uri = 'https://kforge.ros.org/common/rosdepcore'
        scmtype = 'hg'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(scmtype, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual({scmtype: {'local-name': local_name, 'uri': uri}}, wrap.get_legacy_yaml())

        # no version
        local_name = 'common_rosdeps'
        version = None
        uri = 'https://kforge.ros.org/common/rosdepcore'
        scmtype = 'hg'
        struct = {scmtype: {'local-name': local_name, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(scmtype, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual({'hg': {'local-name': 'common_rosdeps', 'uri': 'https://kforge.ros.org/common/rosdepcore'}}, wrap.get_legacy_yaml())
        
        # other
        local_name = 'common_rosdeps'
        version = None
        uri = None
        scmtype = 'other'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(None, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual({scmtype: {'local-name': local_name}}, wrap.get_legacy_yaml())

        # properties (undocumented feature required for builds)
        local_name = 'common_rosdeps'
        version = None
        uri = None
        scmtype = 'other'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri,
                            'meta': {'repo-name': 'skynetish-ros-pkg'}}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(None, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual([{'meta': {'repo-name': 'skynetish-ros-pkg'}}], wrap.get_tags())
        self.assertEqual({scmtype: {'local-name': local_name, 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, wrap.get_legacy_yaml())

        # properties (undocumented feature required for builds)
        local_name = 'common_rosdeps'
        version = None
        uri = 'some/uri'
        scmtype = 'git'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri,
                            'meta': {'repo-name': 'skynetish-ros-pkg'}}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual('git', wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        self.assertEqual([{'meta': {'repo-name': 'skynetish-ros-pkg'}}], wrap.get_tags())
        self.assertEqual({scmtype: {'local-name': local_name, 'uri': 'some/uri', 'meta': {'repo-name': 'skynetish-ros-pkg'}}}, wrap.get_legacy_yaml())
        
    def test_original_syntax_invalids(self):
        local_name = 'common_rosdeps'
        version = '1234'
        uri = 'https://kforge.ros.org/common/rosdepcore'
        scmtype = 'hg'

        try:
            struct = {}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"hello world": None}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"git": None}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"git": {}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"git": {"uri": uri}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"git": {"local-name": local_name}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"foo": {"foo": None}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"other": {"foo": None}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"other": {"uri": uri}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"other": {"version": version}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass

    def test_original_syntax_setupfile(self):
        local_name = '/opt/ros/fuerte/setup.sh'
        version = None
        uri = None
        scmtype = 'setup-file'
        struct = {scmtype: {'local-name': local_name, 'version': version, 'uri': uri}}
        wrap = get_path_spec_from_yaml(struct)
        self.assertEqual(None, wrap.get_scmtype())
        self.assertEqual(scmtype, wrap.get_legacy_type())
        self.assertEqual(version, wrap.get_version())
        self.assertEqual(uri, wrap.get_uri())
        version = "1234"
        uri = 'https://kforge.ros.org/common/rosdepcore'
        try:
            struct = {"setup-file": {"uri": uri}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        try:
            struct = {"setup-file": {"version": version}}
            get_path_spec_from_yaml(struct)
            self.fail("expected exception")
        except MultiProjectException: pass
        
