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
import shutil
import datetime

import vcstools
from vcstools import VcsClient

from common import MultiProjectException
from config_yaml import PathSpec
import ui

## Each Config element provides actions on a local folder


class ConfigElement:
  """ Base class for Config provides methods with not implemented
  exceptions.  Also a few shared methods."""
  def __init__(self, path, local_name):
    self.path = path
    self.local_name = local_name
  def get_path(self):
    """A normalized absolute path"""
    return self.path
  def get_local_name(self):
    """What the user specified in his config"""
    return self.local_name
  def install(self, backup_path = None, arg_mode = 'abort', robust = False):
    raise NotImplementedError, "ConfigElement install unimplemented"
  def get_path_spec(self):
    """PathSpec object with values as specified in file"""
    raise NotImplementedError, "ConfigElement get_path_spec unimplemented"
  def get_versioned_path_spec(self):
    """PathSpec where VCS elements have the version looked up"""
    raise NotImplementedError, "ConfigElement get_versioned_path_spec unimplemented"
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
  def __str__(self):
    return str(self.get_path_spec().get_legacy_yaml());



class OtherConfigElement(ConfigElement):
  def install(self, backup_path = None, arg_mode = None, robust = False):
    return True

  def get_versioned_path_spec(self):
    raise MultiProjectException("Cannot generate versioned outputs with non source types")

  def get_path_spec(self):
    return PathSpec(local_name = self.get_local_name(), path = self.get_path())


class SetupConfigElement(ConfigElement):
  """A setup config element specifies a single file containing configuration data for a config."""

  def install(self, backup_path = None, mode = None, robust = False):
    return True

  def get_versioned_path_spec(self):
    raise MultiProjectException("Cannot generate versioned outputs with non source types")
  
  def get_path_spec(self):
    return PathSpec(local_name = self.get_local_name(), path = self.get_path(), tags=['setup-file'])


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
    :param arg_mode: one of prompt, backup, delete, skip. Determines how to handle error cases
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
      else:
        cur_url = self.vcsc.get_url().rstrip('/')
        if not cur_url or cur_url != self.uri:  #strip trailing slashes for #3269
          # local repositories get absolute pathnames
          if not (os.path.isdir(self.uri) and os.path.isdir(cur_url) and os.path.samefile(cur_url, self.uri)):
            error_message = "url %s does not match %s requested."%(cur_url, self.uri)
        
      # If robust ala continue-on-error, just error now and it will be continued at a higher level
      if robust and error_message:
          raise MultiProjectException(error_message)

      if error_message is None:
        if not self.vcsc.update(self.version):
          raise MultiProjectException("Update Failed of %s"%self.path)
      else:
        # prompt the user based on the error code
        if arg_mode == 'prompt':
          mode = ui.Ui.get_ui().prompt_del_abort_retry(error_message, allow_skip = True)
          if mode == 'backup': # you can only backup if in prompt mode
            backup_path = ui.Ui.get_ui().get_backup_path()
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
  
  def get_path_spec(self):
    "yaml as from source"
    version = self.version
    if version == '': version = None
    return PathSpec(local_name = self.get_local_name(),
                    path = self.get_path(),
                    scmtype = self.vcsc.get_vcs_type_name(),
                    uri = self.uri,
                    version = version)

  def get_versioned_path_spec(self):
    "yaml looking up current version"
    version = self.version
    if version == '': version = None
    revision = None
    if version is not None:
      # revision is the UID of the version spec, can be them same
      revision = self.vcsc.get_version(self.version)
    currevision = self.vcsc.get_version()
    return PathSpec(local_name = self.get_local_name(),
                    path = self.get_path(),
                    scmtype = self.vcsc.get_vcs_type_name(),
                    uri = self.uri,
                    version = version,
                    revision = revision,
                    currevision = currevision)
     

  def get_diff(self, basepath=None):
    return self.vcsc.get_diff(basepath)
  
  def get_status(self, basepath=None, untracked=False):
    return self.vcsc.get_status(basepath, untracked)
  

  
class AVCSConfigElement(VCSConfigElement):
  """
  Implementation using vcstools vcsclient, works for types svn, git, hg, bzr, tar
  :raises: Lookup Exception for unknown types
  """
  def __init__(self, scmtype, path, local_name, uri, version = ''):
    VCSConfigElement.__init__(self, path, VcsClient(scmtype, path), local_name, uri, version)
