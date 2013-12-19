# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
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
import distutils
import shutil
from subprocess import Popen, PIPE
from optparse import OptionParser

import yaml

from rosinstall.helpers import ROSInstallException, ROSINSTALL_FILENAME
from wstool.common import MultiProjectException
from wstool.cli_common import get_workspace
import rosinstall.rosws_cli
from rosinstall.rosinstall_cmd import cmd_persist_config
from wstool.multiproject_cmd import get_config, cmd_install_or_update
import wstool.config_yaml


def get_stack_element_in_config(config, stack):
    """
    The path_spec of a config element if it is named like stack and has a
    root level file named stack.xml
    """
    for entry in config.get_config_elements():
        if entry.get_local_name() == stack:
            if os.path.isfile(os.path.join(entry.get_path(), 'stack.xml')):
                return entry
            else:
                return None
    return None


def roslocate_info(stack, distro, dev):
    """
    Looks up stack yaml on the web

    :raises: ROSInstallException on errors
    """
    # TODO: use roslocate from code
    cmd = ['roslocate', 'info', '--distro=%s' % (distro), stack]
    if dev is True:
        cmd.append('--dev')
    try:
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    except OSError as exc:
        raise ROSInstallException(
            '%s\nfailed to execute roslocate; is your ROS environment configured?' % (exc))

    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        sys.stderr.write('[rosws] Warning: failed to locate stack "%s" in distro "%s".    Falling back on non-distro-specific search; compatibility problems may ensue.\n' % (stack, distro))
        # Could be that the stack hasn't been released; try roslocate
        # again, without specifying the distro.
        cmd = ['roslocate', 'info', stack]
        if dev is True:
            cmd.append('--dev')
        try:
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        except OSError as exc:
            raise ROSInstallException(
                '%s\nfailed to execute roslocate; is your ROS environment configured?' % (exc))

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise ROSInstallException('roslocate failed: %s' % (stderr))
    return yaml.load(stdout)


def get_ros_stack_version():
    """
    Reads/Infers the ros stack version. Avoid using this function if you can.
    """
        # TODO: switch to `rosversion -d` after it's been released (r14279,
    # r14280)
    cmd = ['rosversion', 'ros']
    try:
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    except OSError as exc:
        raise ROSInstallException(
            '%s\nfailed to execute rosversion; is your ROS environment configured?' % (exc))

    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise ROSInstallException('rosversion failed: %s' % (stderr))
    ver = distutils.version.StrictVersion(stdout).version
    if len(ver) < 2:
        raise ROSInstallException('invalid ros version: %s' % (stdout))
    return ver


def rosversion_to_distro_name(ver):
    """
    Reads/Infers the distro name from ROS / or the ros stack
    version. Avoid using this function if you can.
    """
    if len(ver) < 2:
        raise ROSInstallException('invalid ros version: %s' % (ver))
    major, minor = ver[0:2]
    if major == 1 and minor == 10:
        return 'groovy'
    if major == 1 and minor == 8:
        return 'fuerte'
    if major == 1 and minor == 6:
        return 'electric'
    elif major == 1 and minor == 5:
        return 'unstable'
    elif major == 1 and minor == 4:
        return 'diamondback'
    else:
        raise ROSInstallException('unknown ros version: %s' % (ver))


def get_dependent_stacks(stack):
    """
    Calls rosstack depends-on to get a list of dependance stacks. Avoid
    using this function if you can.
    """
    # roslib.stacks doesn't expose the dependency parts of rosstack, so
    # we'll call it manually
    cmd = ['rosstack', 'depends-on', stack]
    try:
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    except OSError as exc:
        raise ROSInstallException(
            '%s\nfailed to execute rosstack; is your ROS environment configured?' % (exc))
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise ROSInstallException('rosstack failed: %s' % (stderr))
    # Make sure to exclude empty lines
    deps = []
    for line in stdout.splitlines():
        if len(line) > 0:
            deps.append(line)
    return deps


def cmd_add_stack(config, stackname, released=False, recurse=False):
    """
    Attempts to get ROS stack from source if it is not already in config.
    Attempts the same for all stacks it depents, if recurse is given.
    Fails if any stack failed.

    :param released: use the released or the dev version
    :param recurse: also get dependant version
    :returns: True if stack has been added
    """
    def _add_stack(config, stackname, distro, released=False):
        stack_element = get_stack_element_in_config(config, stackname)
        if stack_element is not None:
            print("stack %stackname already in config at %s" %
                  (stackname, stack_element.get_path()))
            return False
        yaml_dict = roslocate_info(stackname, distro, not released)
        if yaml_dict is not None and len(yaml_dict) > 0:
            path_spec = wstool.config_yaml.get_path_spec_from_yaml(yaml_dict[0])

            if config.add_path_spec(path_spec, merge_strategy="MergeKeep") is False:
                print("Config did not add element %s" % path_spec)
                return False
            return True
        print("roslocate did not return anything")
        return False

    ver = get_ros_stack_version()
    distro = rosversion_to_distro_name(ver)
    if _add_stack(config, stackname, distro, released) is False:
        return False

    if recurse:
        deps = get_dependent_stacks(stackname)
        # Also switch anything that depends on this stack
        for stack in deps:
            _add_stack(config, stack, distro=distro, released=released)
    return True


def cmd_delete_stack(config, stackname, delete=False, recurse=False):
    """
    Attempts to get ROS stack from source if it is not already in config.
    Attempts the same for all stacks it depents, if recurse is given.
    Fails if any stack failed.

    :param released: use the released or the dev version
    :param recurse: also get dependant version
    :returns: True if stack has been added
    """
    def _del_stack(config, stackname, delete=False):
        stack_element = get_stack_element_in_config(config, stackname)
        if stack_element is None:
            print("stack not in config: %s " % stackname)
            return False
        config.remove_element(stack_element.get_local_name())
        if delete:
            # TODO confirm each delete
            shutil.rmtree(os.path.join(config.base_path, stackname),
                          ignore_errors=True)
        return True

    if _del_stack(config, stackname, delete) is False:
        return False

    if recurse:
        deps = get_dependent_stacks(stackname)
        # Also switch anything that depends on this stack
        for stack in deps:
            _del_stack(config, stack, delete)
    return True


class RosWsStacksCLI():

    def __init__(self):
        self.config_filename = ROSINSTALL_FILENAME

    def cmd_add_stack(self, target_path, argv):
        parser = OptionParser(usage="usage: rosws add-stack [PATH] localname",
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("-N", "--non-recursive", dest="norecurse",
                          default=False,
                          help="don't change configuration for dependent stacks",
                          action="store_true")
        parser.add_option("--released", dest="released",
                          default=False,
                          help="Pull stack from release tag instead of development branch",
                          action="store_true")
        parser.add_option("--continue-on-error", dest="robust",
                          default=False,
                          help="Continue despite checkout errors",
                          action="store_true")
        parser.add_option("--delete-changed-uris", dest="delete_changed",
                          default=False,
                          help="Delete the local copy of a directory before changing uri.",
                          action="store_true")
        parser.add_option("--abort-changed-uris", dest="abort_changed",
                          default=False,
                          help="Abort if changed uri detected",
                          action="store_true")
        parser.add_option("--backup-changed-uris", dest="backup_changed",
                          default='',
                          help="backup the local copy of a directory before changing uri to this directory.",
                          action="store")
        (options, args) = parser.parse_args(argv)
        mode = 'prompt'
        if options.delete_changed:
            mode = 'delete'
        if options.abort_changed:
            if mode == 'delete':
                parser.error(
                    "delete-changed-uris is mutually exclusive with abort-changed-uris")
            mode = 'abort'
        if options.backup_changed != '':
            if mode == 'delete':
                parser.error(
                    "delete-changed-uris is mutually exclusive with backup-changed-uris")
            if mode == 'abort':
                parser.error(
                    "abort-changed-uris is mutually exclusive with backup-changed-uris")
            mode = 'backup'
        if len(args) < 1:
            print("Error: Too few arguments.")
            print(parser.usage)
            return -1
        if len(args) > 1:
            print("Error: Too many arguments.")
            print(parser.usage)
            return -1
        stack = args[0]
        config = get_config(
            target_path, [], config_filename=self.config_filename)
        if cmd_add_stack(config,
                         stack,
                         released=options.released,
                         recurse=(not options.norecurse)) is True:
            cmd_persist_config(config, self.config_filename)
            # install or update each element
            install_success = cmd_install_or_update(
                config,
                backup_path=options.backup_changed,
                mode=mode,
                robust=options.robust)
            if install_success:
                return 0
        return 1

    def cmd_delete_stack(self, target_path, argv):
        parser = OptionParser(
            usage="usage: rosws delete-stack [PATH] localname",
            epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("-N", "--non-recursive", dest="norecurse",
                          default=False,
                          help="don't change configuration for dependent stacks",
                          action="store_true")
        parser.add_option("-d", "--delete-working-copies", dest="delete",
                          default=False,
                          help="when deleting a stack from the configuration, also delete the working copy (DANGEROUS!)",
                          action="store_true")
        (options, args) = parser.parse_args(argv)

        if len(args) < 1:
            print("Error: Too few arguments.")
            print(parser.usage)
            return -1
        if len(args) > 1:
            print("Error: Too many arguments.")
            print(parser.usage)
            return -1
        uri = args[0]
        config = get_config(
            target_path, [], config_filename=self.config_filename)
        if cmd_delete_stack(config,
                            uri,
                            delete=options.delete,
                            recurse=(not options.norecurse)):
            cmd_persist_config(config, self.config_filename)
            return 0
        return 1


def usage():
    print("""%(prog)s is an experimental command to add and remove stack from ROS workspaces.

Usage:
    %(prog)s add [INSTALL_PATH] [STACK] [OPTIONS]
    %(prog)s delete [INSTALL_PATH] [STACK] [OPTIONS]

Type '%(prog)s --help' for usage.
""" % {'prog': 'rosws-stacks'})


def rosws_stacks_main(argv=None):
    """
    Calls the function corresponding to the first argument.
    """
    if argv is None:
        argv = sys.argv
    if ('--help' in argv):
        usage()
        return 0
    if len(argv) < 2:
        try:
            workspace = get_workspace(argv,
                                      os.getcwd(),
                                      config_filename=ROSINSTALL_FILENAME,
                                      varname="ROS_WORKSPACE")
            argv.append('info')
        except MultiProjectException as exc:
            print(str(exc))
            usage()
            return 0

    try:
        command = argv[1]
        args = argv[2:]

        if command == 'help':
            if len(argv) < 3:
                usage()
                return 0

            else:
                command = argv[2]
                args = argv[3:]
                args.insert(0, "-h")

        cli = RosWsStacksCLI()
        commands = {'add': cli.cmd_add_stack,
                    'delete': cli.cmd_delete_stack}
        if command not in commands:
            if os.path.exists(command):
                args = ['-t', command] + args
                command = 'info'
            else:
                if command.startswith('-'):
                    print("First argument must be name of a command: %s" % command)
                else:
                    print("Error: unknown command: %s" % command)
                usage()
                return 1
        workspace = get_workspace(args,
                                  os.getcwd(),
                                  config_filename=ROSINSTALL_FILENAME)
        result = commands[command](workspace, args) or 0
        return result

    except KeyboardInterrupt:
        pass
