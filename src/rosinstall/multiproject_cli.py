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

from __future__ import print_function
import sys
import os
import cli_common
import textwrap
import yaml
from optparse import OptionParser, IndentedHelpFormatter
from common import select_element, MultiProjectException
from config_yaml import PathSpec

import multiproject_cmd

# implementation of single CLI commands (extracted for use in several overlapping scripts)

__MULTIPRO_VERSION__ = '0.6.01'

__MULTIPRO_CMD_DICT__={
  "help"     : "provides help for commands",
  "init"     : "sets up a directory as workspace",
  "info"     : "Overview of all or specific entries",
  "install"  : "to update or also extend your workspace",
  "modify"   : "adds or changes one entry from your workspace config",
  "remove"   : "removes an entry from your workspace config, without deleting files",
  "snapshot" : "writes a file specifying repositories to have the version they currently have",
  "diff"     : "prints a diff over all (or one) SCM controlled entries",
  "status"   : "prints the change status of files in all (or one) SCM controlled entries",
}

class IndentedHelpFormatterWithNL(IndentedHelpFormatter):
  def format_description(self, description):
    if not description: return ""
    desc_width = self.width - self.current_indent
    indent = " "*self.current_indent
# the above is still the same
    bits = description.split('\n')
    formatted_bits = [
      textwrap.fill(bit,
        desc_width,
        initial_indent=indent,
        subsequent_indent=indent)
      for bit in bits]
    result = "\n".join(formatted_bits) + "\n"
    return result 


class MultiprojectCLI:

    def __init__(self, config_filename = None):
        self.config_filename = config_filename

    def cmd_init(self, argv):
        pass
        # TODO enable when making multiproject an independent CLI
#         if self.config_filename == None:
#             print('Error: Bug: config filename required for init')
#             return 1
#         parser = OptionParser(usage="usage: multiproject init [PATH]\n\n\
# rosws init creates new workspace config file at PATH\n")
#         # required here but used one layer above
#         parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
#                           help="which workspace to use",
#                           action="store")
#         (options, args) = parser.parse_args(argv)
#         if len(args) < 1:
#             target_path = '.'
#         else:
#             target_path = args[0]
            
#         if not os.path.isdir(os.path.join(target_path)):
#             if os.path.exists(os.path.dirname(target_path)):
#               os.mkdir(target_path)
#             else:
#               print('Error: Cannot create in target path %s '%target_path)
                                
#         if os.path.exists(os.path.join(target_path, self.config_filename)):
#             print('Error: There already is a workspace config file %s at %s'%(self.config_filename, target_path))
#             return 1
#         # TODO: fix this when used one day
#         config_uris = args[1:]
    
#         config = multiproject_cmd.get_config(basepath = target_path, config_uris = config_uris, config_filename = self.config_filename)
#         multiproject_cmd.cmd_persist_config(config, self.config_filename)
      
#         return 0

    
    def cmd_install(self, target_path, argv, config = None):
        pass
        # TODO enable when making multiproject an independent CLI
        # parser = OptionParser(usage="usage: rosws install PATH [URI]+\n\n\
# rosws install does the following:\n\
#   1. Merges new URIs to existing .rosinstall file at PATH\n\
#   2. Checks out or updates all version controlled URIs\n\
#   3. Generates/overwrites updated setup files\n",
#                               description=__ROSWS_CMD_DICT__[command],
#                               epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
#         parser.add_option("--continue-on-error", dest="robust", default=False,
#                           help="Continue despite checkout errors",
#                           action="store_true")
#         parser.add_option("--delete-changed-uris", dest="delete_changed", default=False,
#                           help="Delete the local copy of a directory before changing uri.",
#                           action="store_true")
#         parser.add_option("--abort-changed-uris", dest="abort_changed", default=False,
#                           help="Abort if changed uri detected",
#                           action="store_true")
#         parser.add_option("--backup-changed-uris", dest="backup_changed", default='',
#                           help="backup the local copy of a directory before changing uri to this directory.",
#                           action="store")
#         # required here but used one layer above
#         parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
#                           help="which workspace to use",
#                           action="store")
#         (options, args) = parser.parse_args(argv)

#         mode = 'prompt'
#         if options.delete_changed:
#             mode = 'delete'
#         if options.abort_changed:
#             if mode == 'delete':
#                 parser.error("delete-changed-uris is mutually exclusive with abort-changed-uris")
#             mode = 'abort'
#         if options.backup_changed != '':
#             if mode == 'delete':
#                 parser.error("delete-changed-uris is mutually exclusive with backup-changed-uris")
#             if mode == 'abort':
#                 parser.error("abort-changed-uris is mutually exclusive with backup-changed-uris")
#             mode = 'backup'
#         config_uris = args
        
#         if config == None:
#             config = multiproject_cmd.get_config(target_path, config_uris, config_filename = self.config_filename)
#         elif config.get_base_path() != target_path:
#             raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))
#         rosinstall.rosinstall_cmd.cmd_persist_config(config, self.config_filename)

#         install_success = multiproject_cmd.cmd_install_or_update(config, options.backup_changed, mode, options.robust)
        
#         return install_success


    def cmd_diff(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws diff [localname] ",
                              description=__MULTIPRO_CMD_DICT__["diff"],
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        # required here but used one layer above
        parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
                          help="which workspace to use",
                          action="store")
        (options, args) = parser.parse_args(argv)
        
        if config == None:
            config = multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        elif config.get_base_path() != target_path:
            raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))

        
        if len(args) > 0:
            localname = args[0]
            if len(args) > 1:
                print("Warning, ignoring extra arguments %s."%args[1:])
            difflist = multiproject_cmd.cmd_diff(config, localname = localname)
        else:
            difflist = multiproject_cmd.cmd_diff(config)
        alldiff = ""
        for entrydiff in difflist:
            if entrydiff['diff'] != None:
                alldiff += entrydiff['diff']
        print(alldiff)
            
        return False
    
    
    def cmd_status(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws status [localname] ",
                              description=__MULTIPRO_CMD_DICT__["status"] + ". The status columns meanings are as the respective SCM defines them.",
                              epilog="""See: http://www.ros.org/wiki/rosinstall for details""")
        parser.add_option("--untracked", dest="untracked", default=False,
                          help="Also shows untracked files",
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

        if len(args) > 0:
            localname = args[0]
            if len(args) > 1:
                print("Warning, ignoring extra arguments %s."%args[1:])
            statuslist = multiproject_cmd.cmd_status(config,
                                                     localname = localname,
                                                     untracked = options.untracked)
        else:
            statuslist = multiproject_cmd.cmd_status(config, untracked = options.untracked)
        allstatus=""
        for entrystatus in statuslist:
            if entrystatus['status'] != None:
                allstatus += entrystatus['status']
        print(allstatus)
        return 0

    
    def cmd_modify(self, target_path, argv, config = None):
        """
        command for modifying/adding a single entry
        :param target_path: where to look for config
        :param config: config to use instead of parsing file anew
        """
        parser = OptionParser(usage="usage: rosws modify [localname]  [--dettach | [--uri=URI] [--(svn|hg|git|bzr)] [--version=VERSION]]",
                              formatter = IndentedHelpFormatterWithNL(),
                              description=__MULTIPRO_CMD_DICT__["modify"] + """
The command will infer whether you want to add or modify an entry. If you modify, it will only change the details you provide, keeping those you did not provide. if you only provide a uri, will use the basename of it as localname unless such an element alreay exists.
""",
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("--dettach", dest="dettach", default=False,
                          help="remove SCM information from an entry",
                          action="store_true")
        parser.add_option("--uri", dest="uri", default=False,
                          help="point SCM to this remote uri",
                          action="store")
        parser.add_option("--version-new", dest="version", default=False,
                          help="point SCM to this version",
                          action="store")
        parser.add_option("--git", dest="git", default=False,
                          help="make an entry a git entry",
                          action="store_true")
        parser.add_option("--svn", dest="svn", default=False,
                          help="make an entry a subversion entry",
                          action="store_true")
        parser.add_option("--hg", dest="hg", default=False,
                          help="make an entry a mercurial entry",
                          action="store_true")
        parser.add_option("--bzr", dest="bzr", default=False,
                          help="make an entry a bazaar entry",
                          action="store_true")
        parser.add_option("-y", "--confirm", dest="confirm", default='',
                          help="Do not ask for confirmation",
                          action="store_true")
        # -t option required here for help but used one layer above, see cli_common
        parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
                          help="which workspace to use",
                          action="store")
        (options, args) = parser.parse_args(argv)

        if len(args) > 1:
            print("Error: Too many arguments.")
            print(parser.usage)
            return -1
        
        if config == None:
            config = multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        elif config.get_base_path() != target_path:
            raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))

        scmtype = None
        count_scms = 0
        if options.git:
            scmtype = 'git'
            count_scms +=1
        if options.svn:
            scmtype = 'svn'
            count_scms +=1
        if options.hg:
            scmtype = 'hg'
            count_scms +=1
        if options.bzr:
            scmtype = 'bzr'
            count_scms +=1
        if count_scms > 1:
            parser.error("You cannot provide more than one scm provider")
          
        is_insert = False
        # find out whether to is_insert or modify
        if len(args) > 0:
            try:
                element = select_element(config.get_config_elements(), args[0])
            except MultiProjectException:
                element = None

        if len(args) == 0 or element is None:
            if options.uri != False and scmtype is not None:
                # maybe is insert
                localname = os.path.basename(options.uri)
                try:
                  element = select_element(config.get_config_elements(), localname)
                except MultiProjectException:
                    element = None
                if element is not None:
                    parser.error("Cannot guess what localname to create")
                is_insert = True
            else:
                parser.error("No scm or localname provided")
            
        if is_insert:
            if scmtype is not None:
                version = None
                if options.version != False:
                  version = options.version
                spec = PathSpec(local_name = localname,
                                uri = options.uri,
                                version = version,
                                scmtype = scmtype)
            else:
                spec = PathSpec(local_name = localname)
            print("     Add element: \n %s"%spec)
        else:
            # modify
            old_spec = element.get_path_spec()
            if options.dettach:
                spec = PathSpec(local_name = element.get_local_name())
            else:
                spec = PathSpec(local_name = element.get_local_name(),
                                uri = options.uri or old_spec.get_uri(),
                                version = options.version or old_spec.get_version(),
                                scmtype = scmtype or old_spec.get_scmtype(),
                                path = old_spec.get_path())
            if spec == old_spec:
                if not options.dettach:
                    parser.error("No change provided, did you mean --detach ?")
                parser.error("No change provided.")
            print("     Change element from: \n %s\n     to\n %s"%(old_spec, spec))

        action = config.add_path_spec(spec, merge_strategy = 'MergeReplace')
        if not options.confirm:
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
        print("Overwriting %s/%s"%(config.get_base_path(), self.config_filename))
        multiproject_cmd.cmd_persist_config(config, self.config_filename)
        for element in config.get_config_elements():
            if element.get_local_name() == spec.get_local_name():
              if element.is_vcs_element():
                element.install(checkout = not os.path.exists(os.path.join(config.get_base_path(), spec.get_local_name())))
              break
        return 0
      
    def cmd_remove(self, target_path, argv, config = None):
        """
        :param target_path: where to look for config
        :param config: config to use instead of parsing file anew
        """
        parser = OptionParser(usage="usage: rosws remove localname",
                        description=__MULTIPRO_CMD_DICT__["remove"],
                        epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        (options, args) = parser.parse_args(argv)
        if len(args) < 1:
            print("Error: Too few arguments.")
            print(parser.usage)
            return -1
        if len(args) > 2:
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

            
    def cmd_info(self, target_path, argv, reverse = False, config = None):
        """
        :param target_path: where to look for config
        :param config: config to use instead of parsing file anew
        """
        # TODO enable when making multiproject an independent CLI
        # parser = OptionParser(usage="usage: rosws info [localname] ",
        #                       description=__MULTIPRO_CMD_DICT__["info"] + ". The Status (S) column can be x for missing and M for modified.",
        #                       epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        # parser.add_option("--data-only", dest="data_only", default=False,
        #                   help="Does not provide explanations",
        #                   action="store_true")
        # parser.add_option("--localnames-only", dest="local_names_only", default=False,
        #                   help="Shows only local names separated by ' '.",
        #                   action="store_true")
        # # -t option required here for help but used one layer above, see cli_common
        # parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
        #                   help="which workspace to use",
        #                   action="store")
        # (options, args) = parser.parse_args(argv)

        # if config == None:
        #     config = multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        # elif config.get_base_path() != target_path:
        #     raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))
      
        # if len(args) > 0:
        #     localname = args[0]
        #     if len(args) > 1:
        #         print("Warning, ignoring extra arguments %s."%args[1:])
        #     outputs = multiproject_cmd.cmd_info(config, localname)
        #     if len(outputs) == 0 or outputs[0] == None:
        #             print("Unknown Localname: %s."%localname)
        #             return 1
        #     cli_common.print_info_list(config.get_base_path(), outputs[0], options.data_only)
        # else:
        #     if options.local_names_only:
        #         print(" ".join(map(lambda x : x.get_local_name(), config.get_config_elements())))
        #         return False
        #     outputs = multiproject_cmd.cmd_info(config)
        #     cli_common.print_info_table(config.get_base_path(), outputs, options.data_only, reverse)
      
        return 0

    def cmd_snapshot(self, target_path, argv):
        parser = OptionParser(usage="usage: rosinstall snapshot filename",
                              description=__MULTIPRO_CMD_DICT__["snapshot"],
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        # -t option required here for help but used one layer above, see cli_common
        parser.add_option("-t", "--target-workspace", dest="workspace", default=None,
                          help="which workspace to use",
                          action="store")
        (options, args) = parser.parse_args(argv)
    
        if len(args) > 1:
            print("Warning, ignoring extra arguments %s."%args[1:])
        if len(args) == 0:
            print("Error: You need to specify a filename to write.")
            print(parser.usage)
            return -1
        filename = args[0]
    
        if target_path == None:
            print("Error: Cannot tell where your ros environment is"%(target_path, self.config_filename))
            return 1
        
        config = multiproject_cmd.get_config(target_path, config_filename = self.config_filename)
    
        tree_elts = config.get_version_locked_source()
        with open(filename, 'w') as fh:
            fh.write(yaml.safe_dump(tree_elts))
        print("Saved versioned rosinstall of current directory %s to %s"%(target_path, filename))
        return 0


