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
from common import select_element, select_elements, MultiProjectException
from config_yaml import PathSpec

import multiproject_cmd

# implementation of single CLI commands (extracted for use in several overlapping scripts)

__MULTIPRO_VERSION__ = '0.6.01'

__MULTIPRO_CMD_DICT__={
  "help"     : "provide help for commands",
  "init"     : "set up a directory as workspace",
  "info"     : "Overview of some entries",
  "merge"    : "merges your workspace with another config set",
  "set"      : "add or changes one entry from your workspace config",
  "update"   : "update or check out some of your config elements",
  "remove"   : "remove an entry from your workspace config, without deleting files",
  "snapshot" : "write a file specifying repositories to have the version they currently have",
  "diff"     : "print a diff over some SCM controlled entries",
  "status"   : "print the change status of files in some SCM controlled entries",
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

  

class MultiprojectCLI:

    def __init__(self, config_filename = None):
        self.config_filename = config_filename

    def cmd_init(self, argv):
        raise Exception("Not implemented yet")
        # TODO enable when making multiproject an independent CLI

    
    def cmd_merge(self, target_path, argv, config = None):
        raise Exception("Not implemented yet")
        # TODO enable when making multiproject an independent CLI


    def cmd_diff(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws diff [localname]* ",
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
            difflist = multiproject_cmd.cmd_diff(config, localnames = args)
        else:
            difflist = multiproject_cmd.cmd_diff(config)
        alldiff = ""
        for entrydiff in difflist:
            if entrydiff['diff'] != None:
                alldiff += entrydiff['diff']
        print(alldiff)
            
        return False
    
    
    def cmd_status(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws status [localname]* ",
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
            statuslist = multiproject_cmd.cmd_status(config,
                                                     localnames = args,
                                                     untracked = options.untracked)
        else:
            statuslist = multiproject_cmd.cmd_status(config, untracked = options.untracked)
        allstatus=""
        for entrystatus in statuslist:
            if entrystatus['status'] != None:
                allstatus += entrystatus['status']
        print(allstatus)
        return 0

    
    def cmd_set(self, target_path, argv, config = None):
        """
        command for modifying/adding a single entry
        :param target_path: where to look for config
        :param config: config to use instead of parsing file anew
        """
        parser = OptionParser(usage="usage: rosws set [localname] [SCM-URI]?  [--(detached|svn|hg|git|bzr)] [--version=VERSION]]",
                              formatter = IndentedHelpFormatterWithNL(),
                              description=__MULTIPRO_CMD_DICT__["set"] + """
The command will infer whether you want to add or modify an entry. If you modify, it will only change the details you provide, keeping those you did not provide. if you only provide a uri, will use the basename of it as localname unless such an element already exists.
""",
                              epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("--detached", dest="detach", default=False,
                          help="make an entry unmanaged (default for new element)",
                          action="store_true")
        parser.add_option("-v","--version-new", dest="version", default=False,
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

        if len(args) > 2:
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
        if options.detach:
          count_scms +=1
        if count_scms > 1:
            parser.error("You cannot provide more than one scm provider option")
          
        is_insert = False
        # find out whether to is_insert or modify
        if len(args) == 0:
          parser.error("Must provide a localname")
        
        element = select_element(config.get_config_elements(), args[0])

        uri = None
        if len(args) == 2:
          uri = args[1]
        if element is None:
            if uri != None and scmtype is not None:
                # maybe is insert
                localname = os.path.basename(uri)
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
                                uri = uri,
                                version = version,
                                scmtype = scmtype)
            else:
                spec = PathSpec(local_name = localname)
            print("     Add element: \n %s"%spec)
        else:
            # modify
            old_spec = element.get_path_spec()
            if options.detach:
                spec = PathSpec(local_name = element.get_local_name())
            else:
                spec = PathSpec(local_name = element.get_local_name(),
                                uri = uri or old_spec.get_uri(),
                                version = options.version or old_spec.get_version(),
                                scmtype = scmtype or old_spec.get_scmtype(),
                                path = old_spec.get_path())
            if spec == old_spec:
                if not options.detach:
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
        # for element in config.get_config_elements():
        #   if element.get_local_name() == spec.get_local_name():
        #     if element.is_vcs_element():
        #       element.install(checkout = not os.path.exists(os.path.join(config.get_base_path(), spec.get_local_name())))
        #       break
        return 0


    def cmd_update(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws update [localname]*",
                        description=__MULTIPRO_CMD_DICT__["update"],
                        epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        parser.add_option("--delete-changed-uris", dest="delete_changed", default=False,
                          help="Delete the local copy of a directory before changing uri.",
                          action="store_true")
        parser.add_option("--abort-changed-uris", dest="abort_changed", default=False,
                          help="Abort if changed uri detected",
                          action="store_true")
        parser.add_option("--continue-on-error", dest="robust", default=False,
                          help="Continue despite checkout errors",
                          action="store_true")
        parser.add_option("--backup-changed-uris", dest="backup_changed", default='',
                          help="backup the local copy of a directory before changing uri to this directory.",
                          action="store")
        (options, args) = parser.parse_args(argv)

        if config == None:
            config = multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        elif config.get_base_path() != target_path:
            raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))
        elements = []
        success = True
        mode = _get_mode_from_options(parser, options)
        if success:
            install_success = multiproject_cmd.cmd_install_or_update(
              config,
              localnames = args,
              backup_path = options.backup_changed,
              mode = 'abort', 
              robust = False)
            return 0
        return 1


    def cmd_remove(self, target_path, argv, config = None):
        parser = OptionParser(usage="usage: rosws remove [localname]*",
                        description=__MULTIPRO_CMD_DICT__["remove"],
                        epilog="See: http://www.ros.org/wiki/rosinstall for details\n")
        (options, args) = parser.parse_args(argv)
        if len(args) < 1:
            print("Error: Too few arguments.")
            print(parser.usage)
            return -1

        if config == None:
            config = multiproject_cmd.get_config(target_path, [], config_filename = self.config_filename)
        elif config.get_base_path() != target_path:
            raise MultiProjectException("Config path does not match %s %s "%(config.get_base_path(), target_path))
        success = True
        elements = select_elements(config, args)
        for element in elements:
            if not config.remove_element(element.get_local_name()):
                success = False
                print("Bug: No such element %s in config, aborting without changes"%(localname))
                break
        if success:
            print("Overwriting %s/%s"%(config.get_base_path(), self.config_filename))
            multiproject_cmd.cmd_persist_config(config, self.config_filename)
            print("Removed entries %s"%args)
            
        return 0

            
    def cmd_info(self, target_path, argv, reverse = False, config = None):
        """
        :param target_path: where to look for config
        :param config: config to use instead of parsing file anew
        """
        raise Exception("Not implemented yet")
        # TODO enable when making multiproject an independent CLI



