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

"""%(prog)s is a command to manipulate ROS workspaces. %(prog)s replaces its predecessor rosinstall.

Official usage:
  %(prog)s CMD [ARGS] [OPTIONS]

rosws will try to infer install path from context

Type '%(prog)s help' for usage.
"""

from __future__ import print_function
import os
import sys
from optparse import OptionParser

import cli_common
import rosinstall_cmd
import multiproject_cmd

from common import MultiProjectException
from helpers import ROSInstallException, ROSINSTALL_FILENAME, get_ros_package_path, get_ros_stack_path
from multiproject_cli import MultiprojectCLI, __MULTIPRO_CMD_DICT__, __MULTIPRO_VERSION__, IndentedHelpFormatterWithNL

## This file adds or extends commands from multiproject_cli where ROS
## specific output has to be generated. 

# extend the commands of multiproject
__ROSWS_CMD_DICT__ = { 'reload': 'sources the setup.sh of the current environment' }
__ROSWS_CMD_DICT__.update(__MULTIPRO_CMD_DICT__)


def _get_mode_from_options(parser, options):
    mode = 'prompt'
    if options.delete_changed:
        mode = 'delete'
    if options.abort_changed:
        if mode == 'delete':
            parser.error("delete-changed-uris is mutually exclusive with abort-changed-uris")
        mode = 'abort'
    if options.backup_changed != '':
        if mode == 'delete':
            parser.error("delete-changed-uris is mutually exclusive with backup-changed-uris")
        if mode == 'abort':
            parser.error("abort-changed-uris is mutually exclusive with backup-changed-uris")
        mode = 'backup'
    return mode
        

class RoswsCLI(MultiprojectCLI):

    def __init__(self, config_filename = ROSINSTALL_FILENAME):
        MultiprojectCLI.__init__(self, config_filename)

    def cmd_init(self, argv):
        if self.config_filename == None:
            print('Error: Bug: config filename required for init')
            return 1
        parser = OptionParser(usage="""usage: rosws init [PATH [PATH_TO_ROS [URIs]]]\n
rosws init does the following:
  1. Reads folder/file/web-uri PATH_TO_ROS looking for ROS
  2. Adds entries from any further URI provided
  2. Creates new %s file at PATH configured for the given ros distro
  3. Checks out and builds ros if necessary
  4. Generates setup files

PATH_TO_ROS can e.g. be a folder like /opt/ros/electric
If PATH_TO_ROS is not given, uses the current ROS_ROOT and ROS_WORKSPACE
If PATH is not given, uses current dir.
"""%self.config_filename,
                              description=__MULTIPRO_CMD_DICT__["init"],
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("-n", "--nobuild", dest="nobuild", default=False,
                          help="skip the build step for the ROS stack",
                          action="store_true")
        parser.add_option("--rosdep-yes", dest="rosdep_yes", default=False,
                          help="Pass through --rosdep-yes to rosmake",
                          action="store_true")
        parser.add_option("-c", "--catkin", dest="catkin", default=False,
                        help="Declare this is a catkin build.",
                        action="store_true")
        parser.add_option("--cmake-prefix-path", dest="catkinpp", default=None,
                        help="Where to set the CMAKE_PREFIX_PATH, implies --catkin",
                        action="store")
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
        if len(args) < 1:
            target_path = '.'
        else:
            target_path = args[0]
            
        if not os.path.isdir(target_path):
            if not os.path.exists(target_path):
              os.mkdir(target_path)
            else:
              print('Error: Cannot create in target path %s '%target_path)
                                
        if os.path.exists(os.path.join(target_path, self.config_filename)):
            print('Error: There already is a workspace config file %s at "%s". Use rosws install to modify.'%(self.config_filename, target_path))
            return 1
        if len(args) < 2:
            if 'ROS_ROOT' not in os.environ:
                raise ROSInstallException('ROS_ROOT not set, and no arguments given to init')
            print('No path to ros given; initializing from current environment')
            config_uris = [os.environ['ROS_ROOT']]
            print('Using ROS_ROOT: %s'%os.environ['ROS_ROOT'])
            if 'ROS_WORKSPACE' in os.environ:
                print('Using ROS_WORKSPACE: %s'%os.environ['ROS_ROOT'])
                for p in os.environ['ROS_WORKSPACE'].split(':'):
                    config_uris.append(os.environ['ROS_WORKSPACE'])
            # TODO
            # if 'ROS_PACKAGE_PATH' in os.environ:
            #   for p in os.environ['ROS_PACKAGE_PATH'].split(':'):
            #     self.init_args.append(p)
        else:
            config_uris = args[1:]

        config = multiproject_cmd.get_config(basepath = target_path,
                                                        additional_uris = config_uris,
                                                        config_filename = self.config_filename)
       
        # includes ROS specific files
        print("Writing %s/%s"%(config.get_base_path(), self.config_filename))
        rosinstall_cmd.cmd_persist_config(config)
        mode = _get_mode_from_options(parser, options)
        ## install or update each element
        install_success = multiproject_cmd.cmd_install_or_update(config, backup_path = options.backup_changed, mode = 'abort', robust = False)
      
        rosinstall_cmd.cmd_generate_ros_files(config,
                                              target_path,
                                              options.nobuild,
                                              options.rosdep_yes,
                                              options.catkin,
                                              options.catkinpp)
    
        if not install_success:
            print("Warning: installation encountered errors, but --continue-on-error was requested.  Look above for warnings.")
        print("\nrosws init complete.\n\nAdd 'source %s/setup.bash' to the bottom of your ~/.bashrc to set it up every time.\n\nIf you are not using bash please see http://www.ros.org/wiki/rosinstall/NonBashShells " % target_path)
        return 0

    def cmd_install(self, target_path, argv, config = None):
          parser = OptionParser(usage="""usage: rosws install [URI]* [OPTIONS]

rosws install does the following:
  1. Updates %s file with all additional URIs
  2. Checks out or updates all version controlled URIs
  3. Regenerates setup files

When an element in an additional URI has the same local-name as an existing element, the exiting element will be REMOVED, and the new entry APPENDED at the end. This can change the order of entries.
"""%self.config_filename,
                              description=__MULTIPRO_CMD_DICT__["init"],
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
          parser.add_option("-n", "--nobuild", dest="nobuild", default=False,
                            help="skip the build step for the ROS stack",
                            action="store_true")
          parser.add_option("--rosdep-yes", dest="rosdep_yes", default=False,
                            help="Pass through --rosdep-yes to rosmake",
                            action="store_true")
          parser.add_option("-c", "--catkin", dest="catkin", default=False,
                            help="Declare this is a catkin build.",
                            action="store_true")
          parser.add_option("--cmake-prefix-path", dest="catkinpp", default=None,
                          help="Where to set the CMAKE_PREFIX_PATH, implies --catkin",
                            action="store")
          # same options as for multiproject
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
          parser.add_option("--merge-kill-append", dest="merge_kill_append", default='',
                            help="(default) merge by deleting given entry and appending new one",
                            action="store_true")
          parser.add_option("-k", "--merge-keep", dest="merge_keep", default='',
                            help="merge by keeping existing entry and discarding new one",
                            action="store_true")
          parser.add_option("-m", "--merge-replace", dest="merge_replace", default='',
                            help="merge by replacing given entry with new one maintaining ordering",
                            action="store_true")
          parser.add_option("-y", "--confirm-all", dest="confirm_all", default='',
                            help="Do not ask for confirmation unless strictly necessary",
                            action="store_true")
          parser.add_option("--noupdates", dest="noupdates", default=False,
                            help="do not perform any SCM action (e.g. when no network connectivity)",
                            action="store_true")
          # required here but used one layer above
          parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
                            help="which workspace to use",
                            action="store")
          (options, args) = parser.parse_args(argv)
          
          mode = _get_mode_from_options(parser, options)
        
          config_uris = args

          if config == None:
              config = multiproject_cmd.get_config(target_path, additional_uris = [], config_filename = self.config_filename)
          elif config.get_base_path() != target_path:
              raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))

          merge_strategy = None
          count_mergeoptions = 0
          if options.merge_kill_append:
              merge_strategy = 'KillAppend'
              count_mergeoptions +=1
          if options.merge_keep:
              merge_strategy = 'MergeKeep'
              count_mergeoptions +=1
          if options.merge_replace:
              merge_strategy = 'MergeReplace'
              count_mergeoptions +=1
          if count_mergeoptions > 1:
              parser.error("You can only provide one merge-strategy")
          if count_mergeoptions == 0:
              merge_strategy = 'KillAppend'

          local_names_old = [x.get_local_name() for x in config.get_config_elements()]
          
          config_actions = multiproject_cmd.add_uris(config,
                                                     additional_uris = config_uris,
                                                     merge_strategy = merge_strategy)
          local_names_new = [x.get_local_name() for x in config.get_config_elements()]
          
          path_changed = False
          ask_user = False
          output = ""
          new_elements = []
          changed_elements = []
          discard_elements = []
          for localname, (action, path_spec) in config_actions.items():
              index = -1
              if localname in local_names_old:
                  index = local_names_old.index(localname)
              if action == 'KillAppend':
                  ask_user = True
                  if (index > -1 and local_names_old[:index+1] == local_names_new[:index+1]):
                      action = 'MergeReplace'
                  else:
                      changed_elements.append(localname)
                      path_changed = True

              if action == 'Append':
                  path_changed = True
                  new_elements.append(localname)
              elif action == 'MergeReplace':
                  changed_elements.append(localname)
                  ask_user = True
              elif action == 'MergeKeep':
                  discard_elements.append(localname)
                  ask_user = True
          if len(changed_elements) > 0:
              output += "\n     Change version of element (Use --merge-keep or --merge-replace to change):\n %s\n"%", ".join(changed_elements)
          if len(new_elements) > 0:
              output += "\n     Add new elements:\n %s\n"%", ".join(new_elements)
              

          if local_names_old != local_names_new[:len(local_names_old)]:
              old_order = ' '.join(reversed(local_names_old))
              new_order = ' '.join(reversed(local_names_new))
              output += "\n     ROS_PACKAGE_PATH order changed (Use --merge-keep or --merge-replace to prevent) from\n %s\n     to\n %s\n\n"%(old_order, new_order)
              ask_user = True

          if not options.noupdates:
              vcs_es = []
              for element in [x for x in config.get_config_elements() if x.is_vcs_element()]:
                  vcs_es.append(element.get_local_name())
              if len(vcs_es) > 0:
                  output += "\n     SCM update elements:\n %s\n"%", ".join(vcs_es)
                  
          if not options.nobuild:
              output += "\n     Call rosmake on ros and ros_comm (use -n to avoid that)\n"
                  
          if output != "":
              if options.confirm_all or not ask_user:
                  print("     Performing actions: ")
                  print(output)
              else:
                  print(output)
                  abort = None
                  prompt = "Continue(y/n): "
                  while abort == None:
                      mode_input = raw_input(prompt)
                      if mode_input == 'y':
                          abort = False
                      elif mode_input == 'n':
                          abort = True
                  if abort:
                      print("No changes made.")
                      return 0
          
          # includes ROS specific files
          print("Overwriting %s/%s"%(config.get_base_path(), self.config_filename))
          rosinstall_cmd.cmd_persist_config(config)

          # install or update each element

          if not options.noupdates:
              install_success = multiproject_cmd.cmd_install_or_update(config,
                                                                       backup_path = options.backup_changed,
                                                                       mode = 'abort',
                                                                       robust = False)
              if not install_success:
                  print("Warning: installation encountered errors, but --continue-on-error was requested.  Look above for warnings.")
                  
          rosinstall_cmd.cmd_generate_ros_files(config,
                                                target_path,
                                                options.nobuild,
                                                options.rosdep_yes,
                                                options.catkin,
                                                options.catkinpp)

          print("\nrosws update complete.")
          if path_changed:
              print("\nDo not forget to do ...\n$ source %s/setup.sh\n... in every open terminal." % target_path)
          return 0


    def cmd_remove(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws remove [PATH] localname",
                        description=__MULTIPRO_CMD_DICT__["remove"],
                        epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
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
        if config == None:
            config = multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        elif config.get_base_path() != target_path:
            raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))
        if config.remove_element(uri):
            print("Overwriting %s/%s"%(config.get_base_path(), self.config_filename))
            multiproject_cmd.cmd_persist_config(config, self.config_filename)
            print("Removed entry %s"%uri)
        return 0

    def cmd_reload(self, argv, config = None):
        parser = OptionParser(usage="usage: rosws reload",
                        description=__ROSWS_CMD_DICT__["reload"],
                        epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        (options, args) = parser.parse_args(argv)
        if len(args) > 0:
            parser.error("The reload command takes no options or further arguments. It is only available after sourcing the rosws.shell extentions.")
        parser.error("The reload command is only available after sourcing the rosws.shell extentions.")
    
        return 0

   
    def cmd_info(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws info PATH [OPTIONS]",
                              formatter = IndentedHelpFormatterWithNL(),
                              description=__MULTIPRO_CMD_DICT__["info"] + """

The Status (S) column shows
 x  for missing
 L  for uncommited (local) changes
 V  for difference in version and/or remote URI

Where status is V, the specified data (Spec) is shown next to the current data in the respective column.
For SVN entries, the url is split up according to standard layout (trunk/tags/branches).
The ROS_PACKAGE_PATH follows the order of the table, earlier entries overlay later entries.
The info command may fetch changesets from remote repositories without affecting your local files.""",
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("--data-only", dest="data_only", default=False,
                          help="Does not provide explanations",
                          action="store_true")
        parser.add_option("--no-pkg-path", dest="no_pkg_path", default=False,
                          help="Suppress ROS_PACKAGE_PATH.",
                          action="store_true")
        parser.add_option("--pkg-path-only", dest="pkg_path_only", default=False,
                          help="Shows only ROS_PACKAGE_PATH separated by ':'. Supercedes all other options.",
                          action="store_true")
        parser.add_option("--localnames-only", dest="local_names_only", default=False,
                          help="Shows only local names separated by ' '. Supercedes all except --pkg-path-only ",
                          action="store_true")
        parser.add_option("--version-only", dest="version_only", default=False,
                          help="Shows only version of single entry. Intended for scripting.",
                          action="store_true")
        parser.add_option("--uri-only", dest="uri_only", default=False,
                          help="Shows only uri of single entry.  Intended for scripting.",
                          action="store_true")
        # -t option required here for help but used one layer above, see cli_common
        parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
                          help="which workspace to use",
                          action="store")
        (options, args) = parser.parse_args(argv)

        if config == None:
            config = multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        elif config.get_base_path() != target_path:
            raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))

        # relevant for code completion, so these should yield quick response:
        if options.local_names_only:
            print(" ".join(map(lambda x : x.get_local_name(), config.get_config_elements())))
            return False
        if options.pkg_path_only:
            print(":".join(get_ros_package_path(config)))
            return False

        localname = None
        if len(args) > 0:
            localname = args[0]
            if len(args) > 1:
                print("Warning, ignoring extra arguments %s."%args[1:])
            outputs = multiproject_cmd.cmd_info(config, localname)
            if len(outputs) == 0 or outputs[0] == None:
                print("Unknown Localname: %s."%localname)
                return 1
            if options.uri_only:
                if outputs[0]['uri'] is not None:
                    print(outputs[0]['uri'])
            elif options.version_only:
                if outputs[0]['version'] is not None:
                    print(outputs[0]['version'])
            else:
                print(cli_common.get_info_list(config.get_base_path(), outputs[0], options.data_only))
            return 0
        
        print("workspace: %s"%target_path)
        print("ROS_ROOT: %s\n"%get_ros_stack_path(config))
    
        if not options.no_pkg_path:
            outputs = multiproject_cmd.cmd_info(config)
            print(cli_common.get_info_table(config.get_base_path(), outputs, options.data_only, reverse = True))
      
        return 0


def usage():
  """
  Prints usage from file header and from dictionary, sorting entries
  """
  dvars = {'prog': 'rosws'}
  dvars.update(vars())
  print(__doc__%dvars)
  keys=[]
  for k in __ROSWS_CMD_DICT__.iterkeys():
    keys.append(k)
  keys.sort()
  for k in keys:
    print("  " + k.ljust(10)+'   \t'+__ROSWS_CMD_DICT__[k])

def rosws_main(argv=None):
  """
  Calls the function corresponding to the first argument.
  """
  if argv == None:
    argv = sys.argv
  if (sys.argv[0] == '-c'):
      sys.argv = ['rosws'] + sys.argv[1:]
  if '--version' in argv:
    print("rosws: \t%s\n%s"%(__MULTIPRO_VERSION__, multiproject_cmd.cmd_version()))
    sys.exit(0)
  workspace = None
  if len(argv) < 2:
    if '--help' in argv:
      usage()
      return 0
    try:
      workspace = cli_common.get_workspace(argv, os.getcwd(), config_filename = ROSINSTALL_FILENAME, varname = "ROS_WORKSPACE")
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
        args.insert(0,"--help")
        # help help
        if command == 'help':
            usage()
            return 0
    cli = RoswsCLI()

    # commands for which we do not infer target workspace
    if command == 'init':
        return cli.cmd_init(args)
    if command == 'reload':
        return cli.cmd_reload(args)
    
    commands = {
      'snapshot'     : cli.cmd_snapshot,
      'info'         : cli.cmd_info,
      'install'      : cli.cmd_install,
      'remove'       : cli.cmd_remove,
      'modify'       : cli.cmd_modify,
      'diff'         : cli.cmd_diff,
      'status'       : cli.cmd_status,
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
    if workspace is None and not '--help' in args and not '-h' in args:
        
      workspace = cli_common.get_workspace(args, os.getcwd(), config_filename = ROSINSTALL_FILENAME, varname = "ROS_WORKSPACE")
    return commands[command](workspace, args)

  except KeyboardInterrupt:
    pass
  except ROSInstallException as e:
    sys.stderr.write("ERROR in rosinstall: %s\n"%str(e))
    return 1
  except MultiProjectException as e:
    sys.stderr.write("ERROR in config: %s\n"%str(e))
    return 1
