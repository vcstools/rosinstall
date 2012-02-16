from __future__ import print_function
import os
import yaml
import copy
import datetime
import shutil

import vcstools
from vcstools import VcsClient

class MultiProjectException(Exception): pass

def get_backup_path():
    backup_path = raw_input("Please enter backup pathname: ")
    print("backing up to %s"%backup_path)
    return backup_path

def prompt_del_abort_retry(prompt, allow_skip = False):
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
  def __init__(self, path):
    self.path = path
    self.setup_file = None
  def get_path(self):
    return self.path
  def install(self, backup_path, mode, robust):
    raise NotImplementedError, "ConfigElement install unimplemented"
  def get_yaml(self):
    """yaml with values as specified in file"""
    raise NotImplementedError, "ConfigElement get_versioned_yaml unimplemented"
  def get_versioned_yaml(self):
    raise NotImplementedError, "ConfigElement get_versioned_yaml unimplemented"
  def is_vcs_element(self):
    # subclasses to override when appropriate
    return False
  def get_diff(self, basepath=None):
    raise NotImplementedError, "ConfigElement get_diff unimplemented"
  def get_status(self, basepath=None, untracked=False):
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
  def __init__(self, path, uri, version=''):
    ConfigElement.__init__(self, path)
    if uri == None:
      raise MultiProjectException("Invalid scm entry having no uri attribute for path %s"%path)
    self.uri = uri.rstrip('/') # strip trailing slashes if defined to not be too strict #3061
    self.version = version

  def is_vcs_element(self):
    return True
    
  def install(self,  backup_path = None,arg_mode = 'abort', robust=False):
    mode = arg_mode
    print("Installing %s %s to %s"%(self.uri, self.version, self.path))

    # Directory exists see what we need to do
    if self.vcsc.path_exists():
      error_message = None
      if not self.vcsc.detect_presence():
        error_message = "Failed to detect %s presence at %s."%(self.vcsc.get_vcs_type_name(), self.path)
      elif not self.vcsc.get_url() or self.vcsc.get_url().rstrip('/') != self.uri:  #strip trailing slashes for #3269
        error_message = "url %s does not match %s requested."%(self.vcsc.get_url(), self.uri)
        
      # If robust ala continue-on-error, just error now and it will be continued at a higher level
      if robust and error_message:
          raise MultiProjectException(error_message)

      # prompt the user based on the error code
      if error_message:
        if arg_mode == 'prompt':
            mode = prompt_del_abort_retry(error_message, allow_skip = True)
            if mode == 'backup': # you can only backup if in prompt mode
              backup_path = get_backup_path()
        if mode == 'abort':
          raise MultiProjectException(error_message)
        elif mode == 'backup':
          self.backup(backup_path)
        elif mode == 'delete':
          shutil.rmtree(self.path)
        elif mode == 'skip':
          return
      
    # If the directory does not exist checkout
    if not self.vcsc.path_exists():
      if not self.vcsc.checkout(self.uri, self.version):
        raise MultiProjectException("Checkout of %s version %s into %s failed."%(self.uri, self.version, self.path))
      else:
        return
    else: # otherwise update
      if not self.vcsc.update(self.version):
          raise MultiProjectException("Update Failed of %s"%self.path)
      else:
          return 
    return
  
  def get_yaml(self):
    "yaml as from source"
    result = {self.vcsc.get_vcs_type_name(): {"local-name": self.path, "uri": self.uri} }
    if self.version != None and self.version != '':
      result[self.vcsc.get_vcs_type_name()]["version"]=self.version
    return [result]

  def get_versioned_yaml(self):
    return [{self.vcsc.get_vcs_type_name(): {"local-name": self.path, "uri": self.uri, "version":self.vcsc.get_version()} }]

  def get_diff(self, basepath=None):
    return self.vcsc.get_diff(basepath)
  
  def get_status(self, basepath=None, untracked=False):
    return self.vcsc.get_status(basepath, untracked)
  

class AVCSConfigElement(VCSConfigElement):
  def __init__(self, type, path, uri, version = ''):
    VCSConfigElement.__init__(self, path, uri, version)
    self.type = type
    self.vcsc = VcsClient(self.type, self.path)


class Config:
  def __init__(self, yaml_source, install_path):
    if yaml_source is None:
      raise MultiProjectException("Passes empty source to create config")
    self.source_uri = install_path #TODO Hack so I don't have to fix the usages of this remove!!!
    self.source = yaml_source
    self.trees = [ ]
    self.base_path = install_path
    self.load_yaml(self.source)
    

  def load_yaml(self, yaml):
    for tree_elt in yaml:
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
          if os.path.exists(local_path) and os.path.isfile(local_path):
            config_file_uri = local_path
          elif os.path.isdir(local_path):
            config_file_uri = os.path.join(local_path, ".rosinstall")
          if os.path.exists(config_file_uri):
            child_config = Config(rosinstall.helpers.get_yaml_from_uri(config_file_uri), config_file_uri)
            for child_t in child_config.trees:
              full_child_path = os.path.join(local_path, child_t.get_path())
              elem = OtherConfigElement(full_child_path)
              if child_t.setup_file: # Inherit setup_file key from children
                elem.setup_file = child_t.setup_file
              self.trees.append(elem)
          else:
            elem = OtherConfigElement(local_path)
            if 'setup-file' in values:
              elem.setup_file = values['setup-file']
            self.trees.append(elem)
        else:
          try:
            elem = AVCSConfigElement(key, local_path, source_uri, version)
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
      except MultiProjectException, ex:
        success = False
        fail_str = "Failed to install tree '%s'\n %s"%(t.get_path(), ex)
        if robust:
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



    
  
