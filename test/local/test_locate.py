import unittest
from mock import Mock
import rosinstall.locate as locate


class LocateTest(unittest.TestCase):

    def test_getters_invalid(self):
        data = {
            'vcs': None,
            'vcs_uri': None}
        self.assertRaises(locate.InvalidData,
                          locate.get_rosinstall, 'myname', data, None)
        data = {
            'vcs': None,
            'vcs_uri': 'https://code.ros.org/svn/ros-pkg'}
        self.assertRaises(locate.InvalidData,
                          locate.get_rosinstall, 'myname', data, None)
        data = {
            'vcs': 'svn',
            'vcs_uri': None}
        self.assertRaises(locate.InvalidData,
                          locate.get_rosinstall, 'myname', data, None)
        data = {}
        self.assertRaises(locate.InvalidData,
                          locate.get_rosinstall, 'myname', data, None)
        data = {'vcs_uri': 'https://code.ros.org/svn/ros-pkg'}
        self.assertRaises(locate.InvalidData,
                          locate.get_rosinstall, 'myname', data, None)
        data = {'vcs': 'svn'}
        self.assertRaises(locate.InvalidData,
                          locate.get_rosinstall, 'myname', data, None)
        data = {'rosinstalls': None}
        self.assertRaises(locate.InvalidData,
                          locate.get_rosinstall,
                          'myname', data, 'mytype', 'devel')
        data = {'rosinstall': None}
        self.assertRaises(locate.InvalidData,
                          locate.get_rosinstall,
                          'myname', data, 'mytype', None)

    def test_getters_empty(self):
        data = {'vcs': 'svn',
                'vcs_uri': 'https://code.ros.org/svn/ros-pkg'}
        self.assertEqual('', locate.get_www(None, data, None))
        self.assertEqual('', locate.get_repo(None, data, None))
        self.assertEqual('https://code.ros.org/svn/ros-pkg', locate.get_vcs_uri_for_branch(data))
        self.assertEqual('https://code.ros.org/svn/ros-pkg', locate.get_vcs_uri_for_branch(data, 'release'))
        self.assertEqual('https://code.ros.org/svn/ros-pkg', locate.get_vcs_uri_for_branch(data, 'devel'))
        self.assertEqual('svn', locate.get_vcs(None, data, None))
        self.assertEqual('- svn:\n    local-name: myname\n    uri: https://code.ros.org/svn/ros-pkg\n',
                         locate.get_rosinstall('myname',
                                               data, 'mytype'))
        self.assertEqual('- svn:\n    local-name: myname\n    uri: https://code.ros.org/svn/ros-pkg\n',
                         locate.get_rosinstall('myname',
                                               data, 'mytype', 'devel'))
        self.assertEqual('- svn:\n    local-name: myname\n    uri: https://code.ros.org/svn/ros-pkg\n',
                         locate.get_rosinstall('myname',
                                               data, 'mytype', 'release'))
        self.assertEqual('- svn:\n    local-name: foo/myname\n    uri: https://code.ros.org/svn/ros-pkg\n',
                         locate.get_rosinstall('myname',
                                               data, 'mytype', None, 'foo'))
        self.assertEqual('https://code.ros.org/svn/ros-pkg',
                         locate.get_vcs_uri(data))
        self.assertEqual('', locate.get_vcs_version(data))
        self.assertEqual('package', locate.get_type(data))

    def test_get_with_branches(self):
        data = {
            'rosinstalls':
                {'devel':
                     {'hg':
                          {'local-name': 'navigation',
                           'uri': 'https://kforge.ros.org/test/devel',
                           'version': 'navigation-1.6'}},
                 'distro':
                     {'hg':
                          {'local-name': 'navigation',
                           'uri': 'https://kforge.ros.org/test/distro',
                           'version': 'electric'}},
                 'release':
                     {'hg':
                      {'local-name': 'navigation',
                       'uri': 'https://kforge.ros.org/test/rel',
                       'version': 'navigation-1.6.5'}}},
            'vcs': 'svn',
            'vcs_uri': 'https://code.ros.org/svn/ros-pkg'}
        self.assertEqual('https://code.ros.org/svn/ros-pkg',
                         locate.get_vcs_uri_for_branch(data))
        self.assertEqual('https://kforge.ros.org/test/rel',
                         locate.get_vcs_uri_for_branch(data, 'release'))
        self.assertEqual('https://kforge.ros.org/test/devel',
                         locate.get_vcs_uri_for_branch(data, 'devel'))
        self.assertEqual('https://kforge.ros.org/test/distro',
                         locate.get_vcs_uri_for_branch(data, 'distro'))
        self.assertEqual('svn', locate.get_vcs(None, data, None))
        self.assertEqual('https://code.ros.org/svn/ros-pkg', locate.get_vcs_uri(data))
        self.assertEqual('', locate.get_vcs_version(data))
        self.assertEqual('package', locate.get_type(data))
        self.assertEqual(
            '- svn:\n    local-name: myname\n    uri: https://code.ros.org/svn/ros-pkg\n',
            locate.get_rosinstall('myname',
                                  data, 'mytype'))
        self.assertEqual(
            '- hg:\n    local-name: navigation\n    uri: https://kforge.ros.org/test/devel\n    version: navigation-1.6\n',
            locate.get_rosinstall('myname',
                                  data, 'mytype', 'devel'))
        self.assertEqual(
            '- hg:\n    local-name: navigation\n    uri: https://kforge.ros.org/test/rel\n    version: navigation-1.6.5\n',
            locate.get_rosinstall('myname',
                                  data, 'mytype', 'release'))
        self.assertEqual(
            '- svn:\n    local-name: foo/myname\n    uri: https://code.ros.org/svn/ros-pkg\n',
            locate.get_rosinstall('myname',
                                  data, 'mytype', None, 'foo'))

    def test_get_with_rosinstall(self):
        data = {
            'rosinstall':
                {'hg':
                      {'local-name': 'navigation',
                       'uri': 'https://kforge.ros.org/test/rel',
                       'version': 'navigation-1.6.5'}},
            'vcs': 'svn',
            'vcs_uri': 'https://code.ros.org/svn/ros-pkg'}
        self.assertEqual(
            '- hg:\n    local-name: navigation\n    uri: https://kforge.ros.org/test/rel\n    version: navigation-1.6.5\n',
            locate.get_rosinstall('myname',
                                  data, 'mytype'))
        self.assertEqual(
            '- hg:\n    local-name: foo/navigation\n    uri: https://kforge.ros.org/test/rel\n    version: navigation-1.6.5\n',
            locate.get_rosinstall('myname',
                                  data, 'mytype', None, 'foo'))

    def test_getters(self):
        data = {'package_type': 'package',
                'repo_name': 'visualization',
                'repo_url': '',
                'srvs': [],
                'timestamp': 1362233859.0088351,
                'url': 'http://ros.org/wiki/rviz',
                'vcs': 'svn',
                'vcs_uri': 'https://code.ros.org/svn/ros-pkg',
                'vcs_version': '0.1',
                'repository': 'navigation'}
        self.assertEqual('http://ros.org/wiki/rviz', locate.get_www(None, data, None))
        self.assertEqual('visualization', locate.get_repo(None, data, None))
        self.assertEqual(
            '- svn:\n    local-name: foo/myname\n    uri: https://code.ros.org/svn/ros-pkg\n    version: \'0.1\'\n',
            locate.get_rosinstall('myname',
                                  data, 'mytype', None, 'foo'))
        self.assertEqual('https://code.ros.org/svn/ros-pkg', locate.get_vcs_uri(data))
        self.assertEqual('0.1', locate.get_vcs_version(data))
        self.assertEqual('package', locate.get_type(data))

    def test_get_manifest_diamondback(self):
        distro = 'diamondback'
        # rviz
        result = locate.get_manifest('rviz', distro)
        self.assertEqual('package', result[1], result)
        # rospack
        (data, type_, url) = locate.get_manifest('rospack', distro)
        self.assertEqual('package', type_, result)
        data = locate._get_rosinstall_dict('rospack', data, type_)
        self.assertEqual('https://code.ros.org/svn/ros/stacks/ros/tags/ros-1.4.10', data.get('svn', {}).get('uri', ''))
        # ros_comm
        (data, type_, url) = locate.get_manifest('ros_comm', distro)
        self.assertEqual('stack', type_)
        data = locate._get_rosinstall_dict('ros_comm', data, type_)
        self.assertTrue('code.ros.org' in data.get('svn', {}).get('uri', ''), data)

    def test_get_manifest_electric(self):
        distro = 'electric'
        # rviz
        result = locate.get_manifest('rviz', distro)
        self.assertEqual('package', result[1], result)
        # rospack
        (data, type_, url) = locate.get_manifest('rospack', distro)
        self.assertEqual('package', type_)
        data = locate._get_rosinstall_dict('rospack', data, type_)
        self.assertEqual('https://code.ros.org/svn/ros/stacks/ros/tags/ros-1.6.9', data.get('svn', {}).get('uri', ''))
        # ros_comm
        (data, type_, url) = locate.get_manifest('ros_comm', distro)
        self.assertEqual('stack', type_)
        data = locate._get_rosinstall_dict('ros_comm', data, type_)
        self.assertTrue('code.ros.org' in data.get('svn', {}).get('uri', ''), data)

    def test_get_manifest_fuerte(self):
        distro = 'fuerte'
        # rviz
        result = locate.get_manifest('rviz', distro)
        self.assertEqual('package', result[1], result)
        # rospack
        (data, type_, url) = locate.get_manifest('rospack', distro)
        self.assertEqual('package', type_)
        data = locate._get_rosinstall_dict('rospack', data, type_)
        self.assertEqual('https://github.com/ros/rospack.git', data.get('git', {}).get('uri', ''))
        self.assertTrue(distro in data.get('git', {}).get('version', ''), data)
        # ros_comm
        (data, type_, url) = locate.get_manifest('ros_comm', distro)
        self.assertEqual('stack', type_)
        data = locate._get_rosinstall_dict('ros_comm', data, type_)
        self.assertEqual('https://github.com/ros/ros_comm.git', data.get('git', {}).get('uri', ''))
        self.assertTrue(distro in data.get('git', {}).get('version', ''), data)

    def test_get_manifest_groovy(self):
        distro = 'groovy'
        # rviz
        result = locate.get_manifest('rviz', distro)
        self.assertEqual('package', result[1], result)
        # rospack
        (data, type_, url) = locate.get_manifest('rospack', distro)
        self.assertEqual('package', type_)
        data = locate._get_rosinstall_dict('rospack', data, type_)
        self.assertEqual('https://github.com/ros/rospack.git', data.get('git', {}).get('uri', ''))
        self.assertTrue(distro in data.get('git', {}).get('version', ''), data)
        # ros_comm
        (data, type_, url) = locate.get_manifest('ros_comm', distro)
        self.assertEqual('metapackage', type_)
        data = locate._get_rosinstall_dict('ros_comm', data, type_)
        self.assertEqual('https://github.com/ros/ros_comm.git', data.get('git', {}).get('uri', ''))
        self.assertTrue(distro in data.get('git', {}).get('version', ''), data)

    def test_get_manifest_current(self):
        # this test obviously returns different results over time
        distro = None
        # rviz
        result = locate.get_manifest('rviz', distro)
        self.assertEqual('package', result[1], result)
        # rospack
        (data, type_, url) = locate.get_manifest('rospack', distro)
        self.assertEqual('package', type_)
        data = locate._get_rosinstall_dict('rospack', data, type_)
        self.assertEqual('https://github.com/ros/rospack.git', data.get('git', {}).get('uri', ''))
        # ros_comm
        (data, type_, url) = locate.get_manifest('ros_comm', distro)
        self.assertEqual('metapackage', type_)
        data = locate._get_rosinstall_dict('ros_comm', data, type_)
        self.assertEqual('https://github.com/ros/ros_comm.git', data.get('git', {}).get('uri', ''))
