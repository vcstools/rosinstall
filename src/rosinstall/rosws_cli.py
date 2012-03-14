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
import yaml
from optparse import OptionParser

import cli_common
import rosinstall_cmd
import multiproject_cmd

from common import MultiProjectException, select_element
from helpers import ROSInstallException, ROSINSTALL_FILENAME, get_ros_package_path, get_ros_stack_path
from multiproject_cli import MultiprojectCLI, __MULTIPRO_CMD_DICT__, IndentedHelpFormatterWithNL
from config_yaml import get_path_spec_from_yaml

## This file adds or extends commands from multiproject_cli where ROS
## specific output has to be generated. 

# extend the commands of multiproject
__ROSWS_CMD_DICT__ = {
      "regenerate"     : "create ROS workspace specific setup files"
      }
__ROSWS_CMD_DICT__.update(__MULTIPRO_CMD_DICT__)


class RoswsCLI(MultiprojectCLI):

    def __init__(self, config_filename = ROSINSTALL_FILENAME):
        MultiprojectCLI.__init__(self, config_filename)

    def cmd_init(self, argv):
        if self.config_filename == None:
            print('Error: Bug: config filename required for init')
            return 1
        parser = OptionParser(usage="""usage: rosws init [TARGET_PATH [SOURCE_PATH]]?\n
rosws init does the following:
  1. Reads folder/file/web-uri SOURCE_PATH looking for a rosinstall yaml to copy
  2. Creates new %s file at TARGET-PATH configured for the given ros distro
  3. Generates ROS setup files, provided a SOURCE_PATH pointing to a ROS was provided

SOURCE_PATH can e.g. be a folder like /opt/ros/electric
If PATH is not given, uses current dir.

Examples:
$ rosws init ~/fuerte /opt/ros/fuerte
"""%self.config_filename,
                              description=__MULTIPRO_CMD_DICT__["init"],
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("-c", "--catkin", dest="catkin", default=False,
                          help="Declare this is a catkin build.",
                          action="store_true")
        parser.add_option("--cmake-prefix-path", dest="catkinpp", default=None,
                          help="Where to set the CMAKE_PREFIX_PATH",
                          action="store")
        parser.add_option("--continue-on-error", dest="robust", default=False,
                          help="Continue despite checkout errors",
                          action="store_true")
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
            print('Error: There already is a workspace config file %s at "%s". Use rosws install/modify.'%(self.config_filename, target_path))
            return 1
        if len(args) > 2:
            parser.error('Too many arguments')
        config_uris = []
        if len(args) == 2:
            config_uris.append(args[1])
        if len(config_uris) > 0:
            print('Using ROS_ROOT: %s'%config_uris[0])

        config = multiproject_cmd.get_config(basepath = target_path,
                                                        additional_uris = config_uris,
                                                        config_filename = self.config_filename)
       
        # includes ROS specific files
        print("Writing %s/%s"%(config.get_base_path(), self.config_filename))
        rosinstall_cmd.cmd_persist_config(config)

        ## install or update each element
        install_success = multiproject_cmd.cmd_install_or_update(config, robust = False)
      
        rosinstall_cmd.cmd_generate_ros_files(config,
                                              target_path,
                                              nobuild = True,
                                              rosdep_yes = False,
                                              catkin = options.catkin,
                                              catkinpp = options.catkinpp,
                                              no_ros_allowed = True)
    
        if not install_success:
            print("Warning: installation encountered errors, but --continue-on-error was requested.  Look above for warnings.")
        print("\nrosws init complete.\n\nAdd 'source %s/setup.bash' to the bottom of your ~/.bashrc to set it up every time.\n\nIf you are not using bash please see http://www.ros.org/wiki/rosinstall/NonBashShells " % target_path)
        return 0

    def cmd_merge(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws merge [URI] [OPTIONS]",
                              formatter = IndentedHelpFormatterWithNL(),
                              description=__MULTIPRO_CMD_DICT__["init"] +""".

The command merges config with given other rosinstall element sets, from files or web uris.

The default workspace will be inferred from context, you can specify one using -t.

By default, when an element in an additional URI has the same
local-name as an existing element, the exiting element will be
REMOVED, and the new entry APPENDED at the end. This can change the
order of entries.

Examples:
$ rosws merge someother.rosinstall

You can use '-' to pipe in input, as an example:
roslocate info robot_mode | rosws merge -
""",
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        # same options as for multiproject
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
                          help="do not ask for confirmation unless strictly necessary",
                          action="store_true")
        # required here but used one layer above
        parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
                          help="which workspace to use",
                          action="store")
        (options, args) = parser.parse_args(argv)

        if len(args) > 1:
            print("Error: Too many arguments.")
            print(parser.usage)
            return -1
        if len(args) == 0:
            print("Error: Too few arguments.")
            print(parser.usage)
            return -1
        
        config_uris = args

        specs = []
        if config_uris[0] == '-':
            pipedata = "".join(sys.stdin.readlines())
            yamldicts = yaml.load(pipedata)
            options.confirm_all = True # cant have user interaction and piped input
            specs.extend([get_path_spec_from_yaml(x) for x in yamldicts])
            config_uris = []

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
        # default option
        if count_mergeoptions == 0:
            merge_strategy = 'MergeReplace'

        (newconfig, path_changed) = self.prompt_merge(target_path,
                                                      additional_uris = config_uris,
                                                      additional_specs = specs,
                                                      path_change_message = "ROS_PACKAGE_PATH order changed",
                                                      merge_strategy = merge_strategy,
                                                      confirmed = options.confirm_all)
        if newconfig is not None:
            print("Overwriting %s/%s"%(newconfig.get_base_path(), self.config_filename))
            rosinstall_cmd.cmd_persist_config(newconfig)
       
            print("\nrosws update complete.")
            if path_changed:
                print("\nDo not forget to do ...\n$ source %s/setup.sh\n... in every open terminal." % target_path)
        print("Config changed, remember to run rosws update to update the tree")
        return 0

    

    def cmd_regenerate(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws regenerate",
                              formatter = IndentedHelpFormatterWithNL(),
                              description=__MULTIPRO_CMD_DICT__["remove"] + """

this command without options generates files setup.sh, setup.bash and
setup.zsh. Note that doing this is unnecessary in general, as these
files do not change anymore, unless you change from one ROS distro to
another (which you should never do like this, create a separate new
workspace instead), or you deleted or modified any of those files
accidentally.
""",
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("-c", "--catkin", dest="catkin", default=False,
                          help="Declare this is a catkin build.",
                          action="store_true")
        parser.add_option("--cmake-prefix-path", dest="catkinpp", default=None,
                          help="Where to set the CMAKE_PREFIX_PATH",
                          action="store")
        (options, args) = parser.parse_args(argv)
        if len(args) > 0:
            print("Error: Too many arguments.")
            print(parser.usage)
            return -1

        if config == None:
            config = multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        elif config.get_base_path() != target_path:
            raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))
        rosinstall_cmd.cmd_generate_ros_files(config,
                                              target_path,
                                              nobuild = True,
                                              rosdep_yes = False,
                                              catkin = options.catkin,
                                              catkinpp = options.catkinpp,
                                              no_ros_allowed = True)
        return 0

   
    def cmd_info(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws info [localname]* [OPTIONS]",
                              formatter = IndentedHelpFormatterWithNL(),
                              description=__MULTIPRO_CMD_DICT__["info"] + """

The Status (S) column shows
 x  for missing
 L  for uncommited (local) changes
 V  for difference in version and/or remote URI

The 'Version-Spec' column shows what tag, branch or revision was given
in the .rosinstall file. The 'UID' column shows the unique ID of the
current (and specified) version. The 'URI' column shows the configured
URL of the repo.

If status is V, the difference between what was specified and what is
real is shown in the respective column. For SVN entries, the url is
split up according to standard layout (trunk/tags/branches).  The
ROS_PACKAGE_PATH follows the order of the table, earlier entries
overlay later entries.

When giving a localname, the diplay just shows the data of one element in list form.
This also has the generic properties element which is usually empty.

Examples:
$ rosws info -t ~/ros/fuerte
$ rosws info robot_model
""",
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
        parser.add_option("--yaml", dest="yaml", default=False,
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
        if args == []:
            args = None
        # relevant for code completion, so these should yield quick response:
        if options.local_names_only:
            print(" ".join(map(lambda x : x.get_local_name(), config.get_config_elements())))
            return 0
        if options.pkg_path_only:
            print(":".join(get_ros_package_path(config)))
            return 0
        if options.yaml:
            source_aggregate = multiproject_cmd.cmd_snapshot(config, localnames = args)
            print(yaml.safe_dump(source_aggregate))
            return 0

        outputs = multiproject_cmd.cmd_info(config, localnames = args)
        if args is not None and len(outputs) == 1:
            # consider not using table display
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
            print(cli_common.get_info_table(config.get_base_path(), outputs, options.data_only, reverse = True))
      
        return 0


def usage():
  """
  Prints usage from file header and from dictionary, sorting entries
  """
  dvars = {'prog': 'rosws'}
  dvars.update(vars())
  print(__doc__%dvars)
  # keys=[]
  # for k in __ROSWS_CMD_DICT__.iterkeys():
  #   if k in gkeys:
  #     keys.append(k)
  # keys.sort()
  keys=['help', 'init', None, 'set', 'merge', None, 'update', None, 'info', 'status', 'diff', None, 'regenerate']
  for k in keys:
    if k in __ROSWS_CMD_DICT__:
      print("  " + k.ljust(10)+'   \t'+__ROSWS_CMD_DICT__[k])
    else:
      print('')

def rosws_main(argv=None):
  """
  Calls the function corresponding to the first argument.
  """
  if argv == None:
    argv = sys.argv
  if (sys.argv[0] == '-c'):
      sys.argv = ['rosws'] + sys.argv[1:]
  if '--version' in argv:
    import __version__
    print("rosws: \t%s\n%s"%(__version__.version, multiproject_cmd.cmd_version()))
    sys.exit(0)
  workspace = None
  if len(argv) < 2:
    try:
      workspace = cli_common.get_workspace(argv, os.getcwd(), config_filename = ROSINSTALL_FILENAME, varname = "ROS_WORKSPACE")
      argv.append('info')
    except MultiProjectException as e:
      print(str(e))
      usage()
      return 0
    
  if '--help' == argv[1]:
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
    commands = {'init': cli.cmd_init}
    # commands which work on a workspace
    ws_commands = {
      'info'         : cli.cmd_info,
      'remove'       : cli.cmd_remove,
      'regenerate'   : cli.cmd_regenerate,
      'set'          : cli.cmd_set,
      'merge'        : cli.cmd_merge,
      'diff'         : cli.cmd_diff,
      'status'       : cli.cmd_status,
      'update'       : cli.cmd_update,
      }


    # TODO remove
    if command not in ['diff', 'status', 'info']:
        print("(rosws and py-rosws are experimental scripts, please provide feedback to tfoote@willowgarage.com)")
    
    if command not in commands and command not in ws_commands:
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
      
    if command in commands:
        return commands[command](args)
    else:
        if workspace is None and not '--help' in args and not '-h' in args:
            workspace = cli_common.get_workspace(args, os.getcwd(), config_filename = ROSINSTALL_FILENAME, varname = "ROS_WORKSPACE")
        return ws_commands[command](workspace, args)

  except KeyboardInterrupt:
    pass
  except ROSInstallException as e:
    sys.stderr.write("ERROR in rosinstall: %s\n"%str(e))
    return 1
  except MultiProjectException as e:
    sys.stderr.write("ERROR in config: %s\n"%str(e))
    return 1
