from __future__ import print_function
import os

import config_elements
from config_elements import AVCSConfigElement, OtherConfigElement, SetupConfigElement
from common import MultiProjectException, normabspath
from config_yaml import get_path_specs_from_uri

def get_backup_path():
  """Interactive function asking the user to choose a path for backup"""
  backup_path = raw_input("Please enter backup pathname: ")
  print("backing up to %s"%backup_path)
  return backup_path

def prompt_del_abort_retry(prompt, allow_skip = False):
  """Interactive function asking the user to choose a conflict resolution"""
  if allow_skip:
    valid_modes = ['(d)elete', '(a)bort', '(b)ackup', '(s)kip']
  else:
    valid_modes = ['(d)elete', '(a)bort', '(b)ackup']

  mode = ""

  full_prompt = "%s %s: "%(prompt, ", ".join(valid_modes))

  while mode == "":

    mode_input = raw_input(full_prompt)
    if mode_input == 'b' or mode_input == 'backup':
      mode = 'backup'
    elif mode_input == 'd' or mode_input =='delete':
      mode = 'delete'
    elif mode_input == 'a' or mode_input =='abort':
      mode = 'abort'
    elif allow_skip and mode_input == 's' or mode_input =='skip':
      mode = 'skip'
  return mode

    
  
class Config:
  """
  A config is a set of config elements, each of which defines a folder or file
  and possibly a VCS from which to update the folder.
  """
  
  def __init__(self, path_specs, install_path, config_filename, extended_types=None, merge_strategy = 'KillAppend'):
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
    
    self.config_filename = config_filename
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
      local_path = normabspath(path_spec.get_path(), self.base_path)
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

  def execute_install(self, backup_path, mode, robust = False):
    success = True
    if not os.path.exists(self.base_path):
      os.mkdir(self.base_path)
    for t in self.trees:
      try:
        t.install(os.path.join(self.base_path, backup_path), mode)
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

