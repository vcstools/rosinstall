from __future__ import print_function
import os
import yaml
import copy
import datetime
import shutil
import urllib2

import vcstools
from vcstools import VcsClient

class MultiProjectException(Exception): pass

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

class ConfigElement:
  """ Base class for Config provides methods with not implemented
  exceptions.  Also a few shared methods."""
  def __init__(self, path, local_name):
    self.path = path
    self.setup_file = None
    self.local_name = local_name
  def get_path(self):
    """where the config element is w.r.t. current dir or absolute"""
    return self.path
  def get_local_name(self):
    """where the config element is w.r.t. the Config base path (or absolute)"""
    return self.local_name
  def install(self, backup_path, mode, robust):
    raise NotImplementedError, "ConfigElement install unimplemented"
  def get_yaml(self):
    """yaml with values as specified in file"""
    raise NotImplementedError, "ConfigElement get_versioned_yaml unimplemented"
  def get_versioned_yaml(self):
    """yaml where VCS elements have the version looked up"""
    raise NotImplementedError, "ConfigElement get_versioned_yaml unimplemented"
  def is_vcs_element(self):
    # subclasses to override when appropriate
    return False
  def get_diff(self, basepath = None):
    raise NotImplementedError, "ConfigElement get_diff unimplemented"
  def get_status(self, basepath = None, untracked = False):
    raise NotImplementedError, "ConfigElement get_status unimplemented"
  def backup(self, backup_path):
    if not backup_path:
      raise MultiProjectException("Cannot install %s.  backup disabled."%self.path)
    backup_path = os.path.join(backup_path, os.path.basename(self.path)+"_%s"%datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    print("Backing up %s to %s"%(self.path, backup_path))
    shutil.move(self.path, backup_path)

class OtherConfigElement(ConfigElement):
  def install(self, backup_path, mode, robust=False):
    return True

  def get_versioned_yaml(self):
    raise MultiProjectException("Cannot generate versioned outputs with non source types")

  def get_yaml(self):
    return [{"other": {"local-name": self.path} }]
  
class VCSConfigElement(ConfigElement):
  
  def __init__(self, path, vcs_client, local_name, uri, version=''):
    """
    Creates a config element for a VCS repository.
    :param path: absolute or relative path, str
    :param vcs_client: Object compatible with vcstools.VcsClientBase
    :param local_name: display name for the element, str
    :param uri: VCS uri to checkout/pull from, str
    :param version: optional revision spec (tagname, SHAID, ..., str)
    """
    ConfigElement.__init__(self, path, local_name)
    if path is None:
      raise MultiProjectException("Invalid empty path")
    if uri is None:
      raise MultiProjectException("Invalid scm entry having no uri attribute for path %s"%path)
    self.uri = uri.rstrip('/') # strip trailing slashes if defined to not be too strict #3061
    self.version = version
    if vcs_client is None:
      raise MultiProjectException("Vcs Config element can only be constructed by providing a VCS client instance")
    self.vcsc = vcs_client

  def is_vcs_element(self):
    return True
    
  def install(self, backup_path = None, arg_mode = 'abort', robust = False):
    """
    Attempt to make it so that self.path is the result of checking out / updating from remote repo
    :param arg_mode: one of prompt, backup, delete, skip. Determins how to handle error cases
    :param backup_path: if arg_mode==backup, determines where to backup to
    :param robust: if true, operation will be aborted without changes to the filesystem and without user interaction
    """
    print("Installing %s (%s) to %s"%(self.uri, self.version, self.path))

    if not self.vcsc.path_exists():
      if not self.vcsc.checkout(self.uri, self.version):
        raise MultiProjectException("Checkout of %s version %s into %s failed."%(self.uri, self.version, self.path))
    else:
      # Directory exists see what we need to do
      error_message = None
      if not self.vcsc.detect_presence():
        error_message = "Failed to detect %s presence at %s."%(self.vcsc.get_vcs_type_name(), self.path)
      elif not self.vcsc.get_url() or self.vcsc.get_url().rstrip('/') != self.uri:  #strip trailing slashes for #3269
        error_message = "url %s does not match %s requested."%(self.vcsc.get_url(), self.uri)
        
      # If robust ala continue-on-error, just error now and it will be continued at a higher level
      if robust and error_message:
          raise MultiProjectException(error_message)

      if error_message is None:
        if not self.vcsc.update(self.version):
          raise MultiProjectException("Update Failed of %s"%self.path)
      else:
        # prompt the user based on the error code
        if arg_mode == 'prompt':
          mode = prompt_del_abort_retry(error_message, allow_skip = True)
          if mode == 'backup': # you can only backup if in prompt mode
            backup_path = get_backup_path()
        else:
          mode = arg_mode
          
        if mode == 'abort':
          raise MultiProjectException(error_message)
        elif mode == 'backup':
          self.backup(backup_path)
        elif mode == 'delete':
          shutil.rmtree(self.path)
        elif mode == 'skip':
          return
      
        # If the directory now does not exist checkout
        if self.vcsc.path_exists():
          raise MultiProjectException("Bug: directory %s should not exist anymore"%(self.path))
        else:
          if not self.vcsc.checkout(self.uri, self.version):
            raise MultiProjectException("Checkout of %s version %s into %s failed."%(self.uri, self.version, self.path))
  
  def get_yaml(self):
    "yaml as from source"
    result = {self.vcsc.get_vcs_type_name(): {"local-name": self.path, "uri": self.uri} }
    if self.version != None and self.version != '':
      result[self.vcsc.get_vcs_type_name()]["version"] = self.version
    return [result]

  def get_versioned_yaml(self):
    "yaml looking up current version"
    result = {self.vcsc.get_vcs_type_name(): {"local-name": self.path, "uri": self.uri, "version": self.vcsc.get_version(), "revision":""} }
    if self.version != None and self.version.strip() != '':
      result[self.vcsc.get_vcs_type_name()]["revision"] = self.vcsc.get_version(self.version)
    return [result]

  def get_diff(self, basepath=None):
    return self.vcsc.get_diff(basepath)
  
  def get_status(self, basepath=None, untracked=False):
    return self.vcsc.get_status(basepath, untracked)
  

  
class AVCSConfigElement(VCSConfigElement):
  """
  Implementation using vcstools vcsclient, works for types svn, git, hg, bzr, tar
  :raises: Lookup Exception for unknown types
  """
  def __init__(self, vtype, path, local_name, uri, version = ''):
    VCSConfigElement.__init__(self, path, VcsClient(vtype, path), local_name, uri, version)

    
class SetupConfigElement(ConfigElement):
  """A setup config element specifies a single file containing configuration data for a config."""
  def install(self, backup_path, mode, robust=False):
    return True

  def get_versioned_yaml(self):
    raise MultiProjectException("Cannot generate versioned outputs with non source types")

  def get_yaml(self):
    return [{"setup-file": {"local-name": self.path} }]


  
class Config:
  """
  A config is a set of config elements, each of which defines a folder or file
  and possibly a VCS from which to update the folder.
  """
  
  def __init__(self, config_source_dicts, install_path, config_filename):
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
    self._load_config_dicts(self.source)


  def _load_config_dicts(self, config_dicts):
    """
    goes through config_dicts and builds up self.trees. validates inputs
    and deals with duplicates. May recursively pull elements from remote sources.
    """
    for tree_elt in config_dicts:
      for key, values in tree_elt.iteritems():

        # Check that local_name exists and record it
        if not 'local-name' in values:
          raise MultiProjectException("local-name is required on all config elements")
        else:
          local_name = values['local-name']

        # Get the version and source_uri elements
        source_uri = values.get('uri', None)
        version = values.get('version', '')
        
        #compute the local_path for the config element
        local_path = os.path.normpath(os.path.join(self.base_path, local_name))

        if key == 'other':
          config_file_uri = '' # does not exist
          if os.path.isfile(local_path):
            config_file_uri = local_path
          elif os.path.isdir(local_path):
            config_file_uri = os.path.join(local_path, self.config_filename)
            
          if os.path.exists(config_file_uri):
            child_config = Config(get_yaml_from_uri(config_file_uri), config_file_uri)
            for child_t in child_config.trees:
              full_child_path = os.path.join(local_path, child_t.get_path())
              child_local_name = full_child_path
              elem = OtherConfigElement(full_child_path, child_local_name)              
              if child_t.setup_file: # Inherit setup_file key from children
                elem.setup_file = child_t.setup_file
              self.trees.append(elem)
          else:
            elem = OtherConfigElement(local_path, local_name)
            if 'setup-file' in values:
              elem.setup_file = values['setup-file']
            self.trees.append(elem)
        elif key == 'setup-file':
          elem = SetupConfigElement(local_path)
          self.trees.append(elem)
        else:
          try:
            elem = AVCSConfigElement(key, local_path, local_name, source_uri, version)
            if 'setup-file' in values:
              elem.setup_file = values['setup-file']
            self.trees.append(elem)
          except LookupError as ex:
            raise MultiProjectException("Abstracted VCS Config failed. Exception: %s" % ex)

          
  def get_base_path(self):
    return self.base_path

  
  def write_version_locked_source(self, filename):
    source_aggregate = []
    for t in self.trees:
      source_aggregate.extend(t.get_versioned_yaml())
    with open(filename, 'w') as fh:
      fh.write(yaml.safe_dump(source_aggregate))

      
  def write_source(self, filename, header = None):
    """
    Write file into the root of the config
    """
    if not os.path.exists(self.base_path):
      os.makedirs(self.base_path)
    f = open(os.path.join(self.base_path, filename), "w+b")
    if header is not None:
      f.write(header)
    f.write(yaml.safe_dump(self.source))
    f.close()


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

