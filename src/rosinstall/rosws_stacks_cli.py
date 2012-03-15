from __future__ import print_function
import os
import sys
import distutils
from subprocess import Popen, PIPE
from optparse import OptionParser

import yaml

from rosinstall.helpers import ROSInstallException, ROSINSTALL_FILENAME
import rosinstall.helpers
import rosinstall.cli_common
import rosinstall.rosws_cli
import rosinstall.rosinstall_cmd
import rosinstall.multiproject_cmd
import rosinstall.config_yaml



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
  cmd = ['roslocate', 'info', '--distro=%s'%(distro), stack]
  if dev == True:
    cmd.append('--dev')
  try:
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
  except OSError as e:
    raise ROSInstallException('%s\nfailed to execute roslocate; is your ROS environment configured?'%(e))

  stdout, stderr = p.communicate()
  if p.returncode != 0:
    sys.stderr.write('[rosws] Warning: failed to locate stack "%s" in distro "%s".  Falling back on non-distro-specific search; compatibility problems may ensue.\n'%(stack,distro))
    # Could be that the stack hasn't been released; try roslocate
    # again, without specifying the distro.
    cmd = ['roslocate', 'info', stack]
    if dev == True:
      cmd.append('--dev')
    try:
      p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    except OSError as e:
      raise ROSInstallException('%s\nfailed to execute roslocate; is your ROS environment configured?'%(e))

    stdout, stderr = p.communicate()
    if p.returncode != 0:
      raise ROSInstallException('roslocate failed: %s'%(stderr))
  return yaml.load(stdout)


def get_ros_stack_version():
  """
  Reads/Infers the ros stack version. Avoid using this function if you can.
  """
    # TODO: switch to `rosversion -d` after it's been released (r14279,
  # r14280)
  cmd = ['rosversion', 'ros']
  try:
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
  except OSError as e:
    raise ROSInstallException('%s\nfailed to execute rosversion; is your ROS environment configured?'%(e))

  stdout, stderr = p.communicate()
  if p.returncode != 0:
    raise ROSInstallException('rosversion failed: %s'%(stderr))
  ver = distutils.version.StrictVersion(stdout).version
  if len(ver) < 2:
    raise ROSInstallException('invalid ros version: %s'%(stdout))
  return ver

def rosversion_to_distro_name(ver):
  """
  Reads/Infers the distro name from ROS / or the ros stack
  version. Avoid using this function if you can.
  """
  if len(ver) < 2:
    raise ROSInstallException('invalid ros version: %s'%(ver))
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
    raise ROSInstallException('unknown ros version: %s'%(ver))

def get_dependent_stacks(stack):
  """
  Calls rosstack depends-on to get a list of dependance stacks. Avoid
  using this function if you can.
  """
  # roslib.stacks doesn't expose the dependency parts of rosstack, so
  # we'll call it manually
  cmd = ['rosstack', 'depends-on', stack]
  try:
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
  except OSError as e:
    raise ROSInstallException('%s\nfailed to execute rosstack; is your ROS environment configured?'%(e))
  stdout, stderr = p.communicate()
  if p.returncode != 0:
    raise ROSInstallException('rosstack failed: %s'%(stderr))
  # Make sure to exclude empty lines
  deps = []
  for l in stdout.split('\n'):
    if len(l) > 0:
      deps.append(l)
  return deps



def cmd_add_stack(config, stackname, released = False, recurse = False):
  """
  Attempts to get ROS stack from source if it is not already in config.
  Attempts the same for all stacks it depents, if recurse is given.
  Fails if any stack failed.
  
  :param released: use the released or the dev version
  :param recurse: also get dependant version
  :returns: True if stack has been added
  """
  def _add_stack(config, stackname, distro, released = False, recurse = False):
    stack_element = get_stack_element_in_config(config, stackname)
    if stack_element is not None:
      print("stack %stackname already in config at %s"%(stackname, stack_element.get_path()))
      return False
    yaml_dict = roslocate_info(stackname, distro, not released)
    if yaml_dict is not None and len(yaml_dict) > 0:
      path_spec = rosinstall.config_yaml.get_path_spec_from_yaml(yaml_dict[0])
      if config.add_path_specs([path_spec]) == False:
        print("Config did not add element %s"%path_spec)
        return False
      return True
    print("roslocate did not return anything")
    return False

  ver = get_ros_stack_version()
  distro = rosversion_to_distro_name(ver)
  if _add_stack(config, stackname, distro, released, recurse) == False:
    return False
  
  if recurse:
    deps = get_dependent_stacks(stack)
    # Also switch anything that depends on this stack
    for s in deps:
      if add_stack_rec(config, s, distro, not released) == False:
        return False
  return True

def cmd_delete_stack(config, stackname, delete = False, recurse = False):
  """
  Attempts to get ROS stack from source if it is not already in config.
  Attempts the same for all stacks it depents, if recurse is given.
  Fails if any stack failed.
  
  :param released: use the released or the dev version
  :param recurse: also get dependant version
  :returns: True if stack has been added
  """
  def _del_stack(config, stackname, delete = False, recurse = False):
    stack_element = get_stack_element_in_config(config, stackname)
    if stack_element is None:
      print("stack not in config: %s "%stackname)
      return False
    config.remove_element(stack_element.get_local_name())
    if delete:
      # TODO confirm each delete
      shutil.rmtree(os.path.join(self.path, stack), ignore_errors=True)
    return True

  if _del_stack(config, stackname, delete, recurse) == False:
    return False
  
  if recurse:
    deps = get_dependent_stacks(stack)
    # Also switch anything that depends on this stack
    for s in deps:
      _del_stack(config, s, delete, recurse)
  return True



class RosWsStacksCLI():

    def __init__(self):
        self.config_filename = ROSINSTALL_FILENAME
  
    def cmd_add_stack(self, target_path, argv):
        parser = OptionParser(usage="usage: rosws add-stack [PATH] localname",
                        epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("-N", "--non-recursive", dest="norecurse", default=False,
                          help="don't change configuration for dependent stacks",
                          action="store_true")
        parser.add_option("--released", dest="released", default=False,
                          help="Pull stack from release tag instead of development branch",
                          action="store_true")
        parser.add_option("--continue-on-error", dest="robust", default=False,
                          help="Continue despite checkout errors",
                          action="store_true")
        parser.add_option("--delete-changed-uris", dest="delete_changed", default=False,
                          help="Delete the local copy of a directory before changing uri.",
                          action="store_true")
        parser.add_option("--abort-changed-uris", dest="abort_changed", default=False,
                          help="Abort if changed uri detected",
                          action="store_true")
        parser.add_option("--backup-changed-uris", dest="backup_changed", default='',
                          help="backup the local copy of a directory before changing uri to this directory.",
                          action="store")
        (options, args) = parser.parse_args(argv)
        mode = rosinstall.rosws_cli._get_mode_from_options(parser, options)
        if len(args) < 1:
            print("Error: Too few arguments.")
            print(parser.usage)
            return -1
        if len(args) > 1:
            print("Error: Too many arguments.")
            print(parser.usage)
            return -1
        stack = args[0]
        config = rosinstall.multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        if cmd_add_stack(config, stack) == True:
            rosinstall.multiproject_cmd.cmd_persist_config(config, self.config_filename)
            # install or update each element
            install_success = rosinstall.multiproject_cmd.cmd_install_or_update(config,
                                                                     backup_changed = options.backup_changed,
                                                                     mode = mode,
                                                                     robust = options.robust)
            if install_success:
              return 0
        return 1


    def cmd_delete_stack(self, target_path, argv):
        parser = OptionParser(usage="usage: rosws delete-stack [PATH] localname",
                        epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("-N", "--non-recursive", dest="norecurse", default=False,
                          help="don't change configuration for dependent stacks",
                          action="store_true")
        parser.add_option("-d", "--delete-working-copies", dest="delete", default=False,
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
        config = rosinstall.multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        if cmd_delete_stack(config, uri):
            rosinstall.multiproject_cmd.cmd_persist_config(config, self.config_filename)
            return 0
        return 1
    

  

def usage():
  print("""%(prog)s is an experimental command to add and remove stack from ROS workspaces.

Usage:
  %(prog)s add [INSTALL_PATH] [STACK] [OPTIONS]
  %(prog)s delete [INSTALL_PATH] [STACK] [OPTIONS]

Type '%(prog)s --help' for usage.
"""%{'prog': 'rosws-stacks'})
    
def rosws_stacks_main(argv=None):
  """
  Calls the function corresponding to the first argument.
  """
  if argv == None:
      argv = sys.argv
  if ('--help' in argv):
      usage()
      return 0
  if len(argv) < 2:
      try:
          workspace = rosinstall.cli_common.get_workspace(argv, os.getcwd(), config_filename = ROSINSTALL_FILENAME, varname = "ROS_WORKSPACE")
          argv.append('info')
      except MultiProjectException as e:
        print(str(e))
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
        command=argv[2]
        args = argv[3:]
        args.insert(0,"-h")

    cli = RosWsStacksCLI()
    commands = {
      'add'         : cli.cmd_add_stack,
      'delete'      : cli.cmd_delete_stack,
      }
    if command not in commands:
      if os.path.exists(command):
        args = ['-t', command] + args
        command = 'info'
      else:
        if command.startswith('-'):
          print("First argument must be name of a command: %s"%command)
        else:
          print("Error: unknown command: %s"%command)
        usage()
        return 1
    workspace = rosinstall.cli_common.get_workspace(args, os.getcwd(), config_filename = ROSINSTALL_FILENAME)
    result = commands[command](workspace, args) or 0
    return result

  except KeyboardInterrupt:
    pass
