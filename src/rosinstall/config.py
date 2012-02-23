from __future__ import print_function
import os
import yaml
import copy
import urllib2

import config_elements
from common import MultiProjectException, normabspath
from config_elements import AVCSConfigElement, OtherConfigElement, SetupConfigElement


def get_yaml_from_uri(uri):
  """reads and parses yaml from a local file or remote uri"""
  stream = 0
  if os.path.isfile(uri):
    try:
      stream = open(uri, 'r')
    except IOError as e:
      raise MultiProjectException("error opening file [%s]: %s\n" % (uri, e))
  else:
    try:
      stream = urllib2.urlopen(uri)
    except IOError as e:
      raise MultiProjectException("Is not a local file, nor able to download as a URL [%s]: %s\n" % (uri, e))
    except ValueError as e:
      raise MultiProjectException("Is not a local file, nor a valid URL [%s] : %s\n" % (uri,e))
  if not stream:
    raise MultiProjectException("couldn't load config uri %s\n" % uri)
  try:
    y = yaml.load(stream);
  except yaml.YAMLError as e:
    raise MultiProjectException("Invalid multiproject yaml format in [%s]: %s\n" % (uri, e))
  return y

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
  
  def __init__(self, config_source_dicts, install_path, config_filename, extended_types=None):
    """
    :param config_source_dict: A list (e.g. from yaml) describing the config, list of dict, each dict describing one element.
    :param config_filename: When given a folder, Config
    will look in folder for file of that name for more config source, str.
    """
    if config_source_dicts is None:
      raise MultiProjectException("Passed empty source to create config")
    self.source = config_source_dicts
    self.trees = [ ]
    self.base_path = install_path
    self.config_filename = config_filename
    # using a registry primarily for unit test design
    self.registry = {'svn': AVCSConfigElement,
                     'git': AVCSConfigElement,
                     'hg': AVCSConfigElement,
                     'bzr': AVCSConfigElement,
                     'tar': AVCSConfigElement}
    if extended_types is not None:
      self.registry = dict(list(self.registry.items()) + list(extended_types.items()))
    self._load_config_dicts(self.source)

  def __str__(self):
    return str([str(x) for x in self.trees])

  def _load_config_dicts(self, config_dicts):
    """
    goes through config_dicts and builds up self.trees. Validates inputs individually.
    May recursively pull elements from remote sources.
    """
    for tree_elt in config_dicts:
      for key, values in tree_elt.iteritems():

        # Check that local_name exists and record it
        if not 'local-name' in values or values['local-name'] is None or values['local-name'].strip() == '':
          raise MultiProjectException("local-name is required on all config elements")
        else:
          local_name = values['local-name']

        # Get the version and source_uri elements
        source_uri = values.get('uri', None)
        version = values.get('version', '')
        
        #compute the local_path for the config element
        local_path = normabspath(local_name, self.base_path)

        if key == 'other':
          config_file_uri = '' # does not exist
          if os.path.isfile(local_path):
            config_file_uri = local_path
          elif os.path.isdir(local_path):
            config_file_uri = os.path.join(local_path, self.config_filename)
            
          if os.path.exists(config_file_uri):
            child_config = Config(get_yaml_from_uri(config_file_uri), config_file_uri)
            for child_t in child_config.get_config_elements():
              full_child_path = os.path.join(local_path, child_t.get_path())
              child_local_name = full_child_path
              elem = OtherConfigElement(full_child_path, child_local_name)              
              if child_t.setup_file: # Inherit setup_file key from children
                elem.setup_file = child_t.setup_file
              self._append_element(elem)
          else:
            elem = OtherConfigElement(local_path, local_name)
            if 'setup-file' in values:
              elem.setup_file = values['setup-file']
            self._append_element(elem)
        elif key == 'setup-file':
          elem = SetupConfigElement(local_path)
          self._append_element(elem)
        else:
          try:
            elem = self._create_vcs_config_element(key, local_path, local_name, source_uri, version)
            if 'setup-file' in values:
              elem.setup_file = values['setup-file']
            self._append_element(elem)
          except LookupError as ex:
            raise MultiProjectException("Abstracted VCS Config failed. Exception: %s" % ex)


  def _append_element(self, new_config_elt):
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
      source_aggregate.extend(t.get_versioned_yaml())
    return source_aggregate


  def get_source(self):
    return self.source
  

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
    """ Return all config elements """
    return copy.copy(self.trees)

