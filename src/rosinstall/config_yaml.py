import os
import yaml
import urllib2

from common import MultiProjectException, conditional_abspath

__REPOTYPES__ = ['svn', 'bzr', 'hg', 'git']
__ALLTYPES__ = __REPOTYPES__ + ['other', 'setup-file']

## The Path spec is a leightweigt object to transport the
## specification of a config element between functions,
## independently of yaml structure.
## Specifications are persisted in yaml, this file deals
## with manipulations of any such structures representing configs as
## yaml.
## get_path_spec_from_yaml turns yaml into path_spec, and pathspec
## get_legacy_yaml returns yaml.


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
    stream.close()
  except yaml.YAMLError as e:
    raise MultiProjectException("Invalid multiproject yaml format in [%s]: %s\n" % (uri, e))
  return y

def get_path_specs_from_uri(uri):
  yaml = get_yaml_from_uri(uri)
  if yaml is not None:
    return [get_path_spec_from_yaml(x) for x in yaml]
  return []


def rewrite_included_source(source_path_specs, source_dir, as_is = False):
  """source yaml is the contents of another directory in source dir,
  we rewrite it to target_dir, by changing the path relative to source
  dir and changing vcs types to 'other' type"""
  for index, pathspec in enumerate(source_path_specs):
    if as_is:
      local_path = pathspec.get_path()
    else:
      local_path = os.path.normpath(os.path.join(source_dir, pathspec.get_path()))
    pathspec.detach_vcs_info()
    pathspec.set_path(local_path)
    source_path_specs[index] = pathspec
  return source_path_specs


def aggregate_from_uris(config_uris, base_path, filename):
  """
  Iterates through uris, each locations a set of config elements as yaml.
  builds a new list of uris following these rules:
  1. when a new location is a folder, test folder for filename
  2. if filename exists, parse yaml from there
  3. else treat folder as a config element itself
  4. parse all config element yamls from location
  5. for each element to be added:
  6. if an element exists in new list with same local-name, delete it
  7. append new element to the new list
  """
  aggregate_source_yaml = []
  # build up a merged list of config elements from all given config_uris
  for loop_uri in config_uris:
    config_uri = conditional_abspath(loop_uri)
    if os.path.isdir(config_uri):
      config_file_uri = os.path.join(config_uri, filename)
      if os.path.exists(config_file_uri):
        source_path_specs = get_path_specs_from_uri(config_file_uri)
        if not source_path_specs:
          raise MultiProjectException("Bad remote folder: %s  This can be caused by empty %s file. "%(loop_uri, filename))
        # adapt paths and change any 'vcs' element into an 'other' element
        source_path_specs = rewrite_included_source(source_path_specs, config_uri)
      else:
        # fall back to just a directory
        source_path_specs = [PathSpec(config_uri)]
    else:
      source_path_specs = get_path_specs_from_uri(config_uri)
      if not source_path_specs:
          raise MultiProjectException("Bad remote source: %s  This can be caused by empty %s file. "%(loop_uri, filename))
    # deal with duplicates in Config class
    if source_path_specs is not None:
      assert type(source_path_specs) == list
      aggregate_source_yaml.extend(source_path_specs)
  return aggregate_source_yaml


class PathSpec:
  def __init__(self,
               local_name,
               scmtype = None,
               uri = None,
               version = None,
               tags = None,
               revision = None):
    """Fils in local properties based on dict, unifies different syntaxes"""
    self._local_name = local_name
    self._uri = uri
    self._version = version
    self._scmtype = scmtype
    self._tags = tags
    self._revision = revision

  def __str__(self):
    return self.get_legacy_yaml()

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      print(self.__dict__)
      print(other.__dict__)
      return self.__dict__ == other.__dict__
    else:
      return False

  def __ne__(self, other):
    return not self.__eq__(other)
  
  def detach_vcs_info(self):
    """if wrapper has VCS information, remove it to make it a plain folder"""
    if self._scmtype is not None:
      self._scmtype = None
      self._uri = None
      self._version = None
    
  def get_legacy_type(self):
    """return one of __ALLTYPES__"""
    if self._scmtype is not None:
      return self._scmtype
    elif self._tags is not None and 'setup-file' in self._tags:
      return 'setup-file'
    return 'other'

  def get_legacy_yaml(self):
    """return something like {hg: {local-name: common, version: common-1.0.2, uri: https://kforge.org/common/}}"""
    properties = {'local-name' : self._local_name}
    if self._scmtype is not None:
      # cautiously discarding uri and version even if they had been set in the meantime
      if self._uri is not None:
        properties['uri'] = self._uri
      if self._version is not None:
        properties['version'] = self._version
      if self._revision is not None:
        properties['revision'] = self._revision
    yaml = {self.get_legacy_type(): properties}
    return yaml

  def get_path(self):
    return self._local_name

  def set_path(self, local_name):
    self._local_name = local_name

  def get_tags(self):
    return self._tags

  def get_scmtype(self):
    return self._scmtype

  def get_version(self):
    return self._version

  def get_uri(self):
    return self._uri


def get_path_spec_from_yaml(yaml_dict):
  """Fills in local properties based on dict, unifies different syntaxes"""
  local_name = None
  uri = None
  version = None
  scmtype = None
  tags = None
  assert type(yaml_dict) == dict
  # old syntax:
# - hg: {local-name: common_rosdeps, version: common_rosdeps-1.0.2, uri: https://kforge.ros.org/common/rosdepcore}
# - setup-file: {local-name: /opt/ros/fuerte/setup.sh}
# - other: {local-name: /opt/ros/fuerte/share/ros}
# - other: {local-name: /opt/ros/fuerte/share}
# - other: {local-name: /opt/ros/fuerte/stacks}
  if len(yaml_dict) == 1 and yaml_dict.keys()[0] in __ALLTYPES__:
    firstkey = yaml_dict.keys()[0]
    if firstkey in __REPOTYPES__:
      scmtype = yaml_dict.keys()[0]
    if firstkey == 'setup-file':
      tags = ['setup-file']
    values = yaml_dict[firstkey]
    if values is not None:
      for key, value in values.items():
        if key == "local-name":
          local_name = value
        elif key == "uri":
          uri = value
        elif key == "version":
          version = value
        else:
          raise MultiProjectException("Unknown key %s in %s"%(key, yaml_dict))
  else:
    raise MultiProjectException("scm type structure not recognized %s"%(yaml_dict))
  # global validation
  if local_name == None:
    raise MultiProjectException("Config element without a local-name: %s"%(yaml_dict))
  if scmtype == None:
    if uri != None:
      raise MultiProjectException("Uri provided in non-scm entry %s"%(yaml_dict))
    if version != None:
      raise MultiProjectException("Version provided in non-scm entry %s"%(yaml_dict))
  else:
    if uri == None:
      raise MultiProjectException("scm type without declared uri in %s"%(value))
  return PathSpec( local_name = local_name,
                   scmtype = scmtype,
                   uri = uri,
                   version = version,
                   tags = tags)

def generate_config_yaml(config, filename, header):
  if not os.path.exists(config.get_base_path()):
    os.makedirs(config.get_base_path())
  with open(os.path.join(config.get_base_path(), filename), 'w+b') as f:
    if header is not None:
      f.write(header)
    f.write(yaml.safe_dump([x.get_legacy_yaml() for x in config.get_source()]))
