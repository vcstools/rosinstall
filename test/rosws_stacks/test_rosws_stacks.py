import os
import io
import unittest
import tempfile
import shutil

import rosinstall.helpers
import rosinstall.rosws_stacks_cli
from rosinstall.helpers import ROSInstallException
from wstool.config import Config
from wstool.config_yaml import PathSpec


class RosWsStacksTest(unittest.TestCase):
    def test_get_distro(self):
        self.assertEqual('diamondback', rosinstall.rosws_stacks_cli.rosversion_to_distro_name([1, 4, 0]))
        self.assertEqual('electric', rosinstall.rosws_stacks_cli.rosversion_to_distro_name([1, 6, 0]))
        self.assertEqual('fuerte', rosinstall.rosws_stacks_cli.rosversion_to_distro_name([1, 8, 0]))
        self.assertEqual('groovy', rosinstall.rosws_stacks_cli.rosversion_to_distro_name([1, 10, 0]))
        try:
            self.assertEqual('groovy', rosinstall.rosws_stacks_cli.rosversion_to_distro_name([1]))
            self.fail('expected exception')
        except ROSInstallException:
            pass
        try:
            self.assertEqual('groovy', rosinstall.rosws_stacks_cli.rosversion_to_distro_name(['a', 'b']))
            self.fail('expected exception')
        except ROSInstallException:
            pass

    def test_get_stack_element_in_config(self):
        self.test_root_path = tempfile.mkdtemp()
        self.install_path = os.path.join(self.test_root_path, "install")
        os.makedirs(self.install_path)
        f = io.open(os.path.join(self.install_path, 'stack.xml'), 'a')
        f.write(unicode("hello stack"))
        f.close()
        config = Config([PathSpec("foo"),
                         PathSpec("install"),
                         PathSpec("bar")],
                        self.test_root_path,
                        None)
        self.assertEqual(None, rosinstall.rosws_stacks_cli.get_stack_element_in_config(config, 'foo'))
        self.assertEqual(None, rosinstall.rosws_stacks_cli.get_stack_element_in_config(config, None))
        el = rosinstall.rosws_stacks_cli.get_stack_element_in_config(config, 'install')
        self.assertEqual(self.install_path, el.get_path())
        shutil.rmtree(self.test_root_path)

    def test_roslocate_info(self):
        yaml = rosinstall.rosws_stacks_cli.roslocate_info("ros_comm", "electric", False)
        self.assertEqual([{'svn': {'local-name': 'ros_comm', 'uri': 'https://code.ros.org/svn/ros/stacks/ros_comm/tags/ros_comm-1.6.6'}}], yaml)

    def xtest_get_ros_stack_version(self):
        ver = rosinstall.rosws_stacks_cli.get_ros_stack_version()
        assertTrue(ver[0] > 1)
        assertTrue(ver[1] >= 0)

    def test_get_dependent_stacks(self):
        dep_ons = rosinstall.rosws_stacks_cli.get_dependent_stacks('ros')
        self.assertTrue(len(dep_ons) > 1)
