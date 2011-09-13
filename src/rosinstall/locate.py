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

# Author: kwc

import os
import sys
import yaml
import urllib2

BRANCH_RELEASE = 'release'
BRANCH_DEVEL = 'devel'

class InvalidData(Exception): pass

def get_rosinstall(name, data, type_, branch=None, prefix=None):
    """
    Compute a rosinstall fragment for checkout
    
    @param name: resource name
    @param data: manifest data for resource
    @param branch: source branch type ('devel' or 'release')
    @param prefix: checkout filepath prefix
    @raise InvalidData
    """
    
    if not 'rosinstall' in data:
        raise InvalidData("rosinstall control information for %s %s\n"%(type_, name))

    ri_entry = None
    if branch and 'rosinstalls' in data:
        ri_entry = data['rosinstalls'].get(branch, None)

    # if we were unable to compute the rosinstall info based on a
    # desired branch, use the default info instead
    if ri_entry is None:
        if data['vcs'] == 'svn':
            # fancy logic to enable package-specific checkout and also
            # fix a bug in the indexer.
            ri_entry = {'svn': {'local-name': name, 'uri': data['vcs_uri']}}
        else:
            ri_entry = data['rosinstall']
        
    if len(ri_entry) != 1:
        raise InvalidData("rosinstall malformed for %s %s\n"%(type_, name))

    prefix = prefix or ''
    for k, v in ri_entry.iteritems():
        if 'local-name' in v:
            local_name = v['local-name']                
            # 3513
            # compute path: we can't use os.path.join because rosinstall paths
            # are always Unix-style.
            paths = [x for x in (prefix, local_name) if x]
            path = '/'.join(paths)
            v['local-name'] = path

    return yaml.dump([ri_entry], default_flow_style=False)

def get_vcs_uri_for_branch(data, branch=None):
    """
    @param data: rosdoc manifest data
    @param branch: source branch type ('devel' or 'release')
    """
    ri_entry = None
    if branch and 'rosinstalls' in data:
        ri_entry = data['rosinstalls'].get(branch, None)
        vcs_type = ri_entry.keys()[0]
        return ri_entry[vcs_type]['uri']
    else:
        return data.get('vcs_uri', '')

def get_vcs(name, data, type_):
    """
    @param name: resource name
    @param data: rosdoc manifest data
    @param type_: resource type ('stack' or 'package')
    """
    return data.get('vcs', '')

def get_repo(name, data, type_):
    """
    @param name: resource name
    @param data: rosdoc manifest data
    @param type_: resource type ('stack' or 'package')
    """
    return data.get('repository', '')

def get_www(name, data, type_):
    """
    @param name: resource name
    @param data: rosdoc manifest data
    @param type_: resource type ('stack' or 'package')
    """
    return data.get('url', '')

def get_rosdoc_manifest(arg, distro_name=None):
    """
    Get the rosdoc manifest data and type of arg.

    @param arg: name of package/stack to get manifest information for.
    get_manifest() gives stacks symbols precedence over package
    symbols.
    @type  arg: str
    
    @return: (manifest data, 'package'|'stack'). 
    @rtype: ({str: str}, str)
    @raise IOError: if data cannot be loaded
    """
    try:
        if distro_name is not None:
            url = 'http://ros.org/doc/%s/api/%s/stack.yaml'%(distro_name, arg)
        else:
            url = 'http://ros.org/doc/api/%s/stack.yaml'%(arg)
        r = urllib2.urlopen(url)
        return yaml.load(r), 'stack'
    except:
        try:
            if distro_name is not None:
                url = 'http://ros.org/doc/%s/api/%s/manifest.yaml'%(distro_name, arg)
            else:
                url = 'http://ros.org/doc/api/%s/manifest.yaml'%(arg)
            r = urllib2.urlopen(url)
            return yaml.load(r), 'package'
        except:
            raise IOError(arg)
        
