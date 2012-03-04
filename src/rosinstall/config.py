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

from __future__ import print_function
import os

import config_elements
from config_elements import AVCSConfigElement, OtherConfigElement, SetupConfigElement
from common import MultiProjectException, normabspath
from config_yaml import get_path_specs_from_uri

  
class Config:
  """
  A config is a set of config elements, each of which defines a folder or file
  and possibly a VCS from which to update the folder.
  """
  
  def __init__(self, path_specs, install_path, config_filename = None, extended_types=None, merge_strategy = 'KillAppend'):
    """
    :param config_source_dict: A list (e.g. from yaml) describing the config, list of dict, each dict describing one element.
    :param config_filename: When given a folder, Config
    :param merge_strategy: how to deal with entries with equivalent path. See _append_element
    will look in folder for file of that name for more config source, str.
    """
    assert install_path is not None
    if path_specs is None:
      raise MultiProjectException("Passed empty source to create config")
    self.trees = []
    self.base_path = os.path.abspath(install_path)

    self.config_filename = None
    if config_filename is not None:
      self.config_filename = os.path.basename(config_filename)
    # using a registry primarily for unit test design
    self.registry = {'svn': AVCSConfigElement,
                     'git': AVCSConfigElement,
                     'hg': AVCSConfigElement,
                     'bzr': AVCSConfigElement,
                     'tar': AVCSConfigElement}
    if extended_types is not None:
      self.registry = dict(list(self.registry.items()) + list(extended_types.items()))
    self._load_config_dicts(path_specs, merge_strategy)

  def __str__(self):
    return str([str(x) for x in self.trees])

  def _load_config_dicts(self, path_specs, merge_strategy = 'KillAppend'):
    """
    goes through config_dicts and builds up self.trees. Validates inputs individually.
    May recursively pull elements from remote sources.
    """
    for path_spec in path_specs:
      #compute the local_path for the config element
      local_path = normabspath(path_spec.get_path(), self.get_base_path())
      if path_spec.get_scmtype() == None:
        if path_spec.get_tags() is not None and 'setup-file' in path_spec.get_tags():
          elem = SetupConfigElement(local_path, path_spec.get_path())
          self._append_element(elem)
        else:
          config_file_uri = '' # os.path.exists == False, later
          if os.path.isfile(local_path):
            config_file_uri = local_path
          elif os.path.isdir(local_path):
            # unless filename feature is disabled
            if self.config_filename is not None:
              config_file_uri = os.path.join(local_path, self.config_filename)
          if os.path.exists(config_file_uri):
            child_config = Config(get_path_specs_from_uri(config_file_uri), local_path, self.config_filename)
            for child_path_spec in child_config.get_source():
              full_child_path = os.path.join(local_path, child_path_spec.get_path())
              child_local_name = full_child_path
              if child_path_spec.get_tags() is not None and 'setup-file' in child_path_spec.get_tags():
                elem = SetupConfigElement(full_child_path, child_local_name)
                self._append_element(elem)
              else:
                elem = OtherConfigElement(full_child_path, child_local_name)
                self._append_element(elem)
          else:
            local_name = path_spec.get_path()
            elem = OtherConfigElement(local_path, local_name)
            self._append_element(elem)
      else:
        # Get the version and source_uri elements
        source_uri = path_spec.get_uri()
        version = path_spec.get_version()
        try:
          local_name = path_spec.get_path()
          elem = self._create_vcs_config_element(path_spec.get_scmtype(),
                                                 local_path,
                                                 local_name,
                                                 source_uri,
                                                 version)
          self._append_element(elem)
        except LookupError as ex:
          raise MultiProjectException("Abstracted VCS Config failed. Exception: %s" % ex)


  def _append_element(self, new_config_elt, merge_strategy = 'KillAppend'):
    """Add element to self.trees, checking for duplicate local-name fist.
    In that case, follow given strategy:
    KillAppend (default): remove old element, append new at the end
    Replace: remove first such old element, insert new at that position."""
    removals = []
    for index, loop_elt in enumerate (self.trees):
      if loop_elt.get_path() == new_config_elt.get_path():
        if merge_strategy == 'KillAppend':
          removals.append(loop_elt)
        elif merge_strategy == 'Replace':
          self.trees[index] = new_config_elt
          return True
        else:
          raise LookupError("No such merge strategy: %s"%str(merge_strategy))
    for loop_elt in removals:
      self.trees.remove(loop_elt)
    self.trees.append(new_config_elt)
    return True

  def _create_vcs_config_element(self, scmtype, path, local_name, uri, version = ''):
    try:
      eclass = self.registry[scmtype]
    except LookupError:
      raise MultiProjectException("No VCS client registered for vcs type %s"%scmtype)
    return eclass(scmtype = scmtype, path = path, local_name = local_name, uri = uri, version = version)

  def get_base_path(self):
    return self.base_path

  
  def get_version_locked_source(self):
    source_aggregate = []
    for t in self.trees:
      source_aggregate.append(t.get_versioned_path_spec())
    return source_aggregate


  def get_source(self):
    source_aggregate = []
    for t in self.trees:
      source_aggregate.append(t.get_path_spec())
    return source_aggregate  

  def execute_install(self, backup_path = None, mode = 'abort', robust = False):
    success = True
    if not os.path.exists(self.get_base_path()):
      os.mkdir(self.get_base_path())
    for t in self.trees:
      abs_backup_path = None
      if backup_path is not None:
        abs_backup_path = os.path.join(self.get_base_path(), backup_path)
      try:
        t.install(abs_backup_path, mode)
      except MultiProjectException as ex:
        fail_str = "Failed to install tree '%s'\n %s"%(t.get_path(), ex)
        if robust:
          success = False
          print("Continuing despite %s"%fail_str)
        else:
          raise MultiProjectException(fail_str)
      else:
          pass
    return success
    # TODO go back and make sure that everything in options.path is described
    # in the yaml, and offer to delete otherwise? not sure, but it could go here

  
  def get_config_elements(self):
    source_aggregate = []
    for t in self.trees:
      source_aggregate.append(t)
    return source_aggregate

